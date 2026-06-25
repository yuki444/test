# coding: utf-8
"""
Agent③ v4 — 動画化（タイトルスクリーン + 歌詞テキスト + スムーズ Ken Burns）

使い方:
  python scripts/make_videos.py --date 2026-06-25
  python scripts/make_videos.py --date 2026-06-25 --force
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

VIDEO_W, VIDEO_H = 1280, 720
FPS = 25
CROSSFADE_SEC = 1.5
TITLE_DURATION = 5.0      # タイトルスクリーン秒数
LYRICS_LINES_MAX = 4
ZOOM_AMOUNT = 0.15

REPO_ROOT = Path(__file__).parent.parent
LYRICS_DIR = REPO_ROOT / "lyrics"

_ffmpeg_env = os.environ.get("FFMPEG_CMD", "ffmpeg")
_ffmpeg_path = shutil.which(_ffmpeg_env)
FFMPEG_CMD = _ffmpeg_path if _ffmpeg_path else _ffmpeg_env

FONT_CANDIDATES = [
    "C:\\Windows\\Fonts\\meiryo.ttc",
    "C:\\Windows\\Fonts\\YuGothM.ttc",
    "C:\\Windows\\Fonts\\YuGothB.ttc",
    "C:\\Windows\\Fonts\\msgothic.ttc",
    "C:\\Windows\\Fonts\\yugothic.ttf",
    "C:\\Windows\\Fonts\\meiryob.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# ── 診断 ─────────────────────────────────────────────────────────────────────

def check_dependencies():
    ok = True
    print(f"  Pillow : {'OK' if PILLOW_OK else 'NOT INSTALLED  -> pip install Pillow'}")
    if not PILLOW_OK:
        ok = False
    else:
        font = find_font(40)
        if font:
            print(f"  Font   : OK ({font.path if hasattr(font, 'path') else 'found'})")
        else:
            paths = [p for p in FONT_CANDIDATES if Path(p).exists()]
            print(f"  Font   : NOT FOUND  (checked {len(FONT_CANDIDATES)} paths)")
            print(f"           Fonts present: {paths}")
    print(f"  ffmpeg : {FFMPEG_CMD if _ffmpeg_path else 'NOT FOUND'}")
    if not _ffmpeg_path:
        ok = False
    return ok


# ── 歌詞パース ────────────────────────────────────────────────────────────────

def parse_lyrics_file(date_str):
    path = LYRICS_DIR / date_str / "song.txt"
    if not path.exists():
        return {"title": "", "sections": [], "raw": ""}

    content = path.read_text(encoding="utf-8").strip()
    lines = content.split("\n")

    title = ""
    body_start = 0
    if lines and ":" in lines[0] and not lines[0].startswith("["):
        for i, line in enumerate(lines):
            if line.strip() == "---":
                body_start = i + 1
                break
            if ":" in line:
                k, _, v = line.partition(":")
                if k.strip().lower() == "title":
                    title = v.strip()

    body = "\n".join(lines[body_start:])
    sections = []
    current_name = None
    current_lines = []

    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_name is not None:
                sections.append({
                    "name": current_name,
                    "lyrics": "\n".join(l for l in current_lines if l.strip()),
                })
            current_name = stripped[1:-1]
            current_lines = []
        elif current_name is not None:
            current_lines.append(stripped)

    if current_name is not None:
        sections.append({
            "name": current_name,
            "lyrics": "\n".join(l for l in current_lines if l.strip()),
        })

    return {"title": title, "sections": sections, "raw": body}


# ── セクション時間計算 ────────────────────────────────────────────────────────

def calc_section_durations(sections, total_dur, audio_path=None):
    """
    各セクションの表示時間を計算する。

    1. Whisper が使える場合: 音声認識で歌詞の開始位置を検出してタイミング同期
    2. 使えない場合: 歌詞の文字数に比例した時間配分（均等より自然）
    """
    n = len(sections)
    if n == 0:
        return []

    # --- Whisper で音声認識タイミング取得 ---
    if audio_path is not None:
        try:
            import whisper
            print("  [Whisper] 音声認識でタイミング検出中...")
            model = whisper.load_model("base")
            result = model.transcribe(
                str(audio_path),
                language="ja",
                word_timestamps=False,
                verbose=False,
            )
            segments = result.get("segments", [])
            if segments:
                return _whisper_to_section_durations(sections, segments, total_dur)
        except ImportError:
            pass  # Whisper 未インストール → 文字数比例にフォールバック
        except Exception as e:
            print(f"  [Whisper] エラー: {e} → 文字数比例にフォールバック")

    # --- 文字数比例 ---
    return _char_proportional_durations(sections, total_dur)


def _char_proportional_durations(sections, total_dur):
    """歌詞の文字数に比例して各セクションに時間を割り当てる。"""
    # セクション種別ごとの重みを加味（サビは長め、イントロは短め）
    SECTION_WEIGHTS = {
        "intro":      0.7,
        "outro":      0.6,
        "pre-chorus": 0.8,
        "bridge":     0.9,
        "verse":      1.0,
        "chorus":     1.1,
    }

    weights = []
    for sec in sections:
        name_lower = sec["name"].lower()
        char_count = max(len(re.sub(r'\s', '', sec.get("lyrics", ""))), 1)
        weight_key = next((k for k in SECTION_WEIGHTS if name_lower.startswith(k)), None)
        w = SECTION_WEIGHTS.get(weight_key, 1.0) if weight_key else 1.0
        weights.append(char_count * w)

    total_w = sum(weights)
    return [total_dur * w / total_w for w in weights]


def _whisper_to_section_durations(sections, segments, total_dur):
    """Whisperセグメントから各セクションの推定継続時間を算出する。"""
    n = len(sections)
    if not segments or n == 0:
        return [total_dur / n] * n

    # セグメントを均等にセクション数で分割
    segs_per_sec = len(segments) / n
    durations = []
    for i in range(n):
        start_idx = int(i * segs_per_sec)
        end_idx   = int((i + 1) * segs_per_sec)
        seg_slice = segments[start_idx:end_idx] if end_idx > start_idx else [segments[min(start_idx, len(segments)-1)]]
        sec_start = seg_slice[0]["start"]
        sec_end   = seg_slice[-1]["end"]
        durations.append(max(sec_end - sec_start, 1.0))

    # 合計を total_dur に正規化
    total_w = sum(durations)
    return [total_dur * d / total_w for d in durations]


# ── Pollinations 画像生成 ──────────────────────────────────────────────────

SECTION_MOOD = {
    "Intro":      "opening, ambient, dawn light, cinematic establishing shot",
    "Verse":      "calm, storytelling, atmospheric, soft natural light",
    "Verse 1":    "calm, morning light, cinematic, peaceful landscape",
    "Verse 2":    "emotional, memories, soft golden hour, warm tones",
    "Pre-Chorus": "building energy, dramatic sky, twilight, tension",
    "Chorus":     "energetic, uplifting, vibrant colors, emotional peak, light rays",
    "Bridge":     "introspective, mysterious night sky, turning point",
    "Outro":      "peaceful resolution, fading sunset, soft glow, cinematic ending",
}

def section_mood(name):
    for key, mood in SECTION_MOOD.items():
        if name.lower().startswith(key.lower()):
            return mood
    return "cinematic, artistic, atmospheric, beautiful landscape"


def download_image(prompt, out_path, seed=42, timeout=90):
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={VIDEO_W}&height={VIDEO_H}&nologo=true&seed={seed}&enhance=true"
    )
    print(f"    img [{seed}]: {prompt[:60]}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if len(data) < 1000:
            raise ValueError("too small")
        out_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"    img failed: {e}")
        return False


# ── Pillow フォント ──────────────────────────────────────────────────────────

def find_font(size):
    if not PILLOW_OK:
        return None
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return None


# ── タイトルスクリーン画像生成 ────────────────────────────────────────────

def make_title_image(song_title, style_label, base_img_path, out_path):
    """
    曲タイトルを大きく表示したオープニング画像を生成する。
    Break the Night スタイル: 左寄り白太字タイトル + 下部スタイル表示
    """
    if not PILLOW_OK:
        shutil.copy(str(base_img_path), str(out_path))
        return

    base = Image.open(str(base_img_path)).convert("RGB").resize(
        (VIDEO_W, VIDEO_H), Image.LANCZOS
    )

    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 全体に薄い暗幕（読みやすさ向上）
    draw.rectangle([(0, 0), (VIDEO_W, VIDEO_H)], fill=(0, 0, 0, 60))

    # タイトル周辺にグラデーション（左から中央）
    for x in range(VIDEO_W // 2):
        alpha = int(130 * (1 - x / (VIDEO_W // 2)))
        draw.rectangle([(x, 0), (x, VIDEO_H)], fill=(0, 0, 0, alpha))

    # フォント
    font_title  = find_font(88)
    font_style  = find_font(32)

    title_x = 80
    title_y = VIDEO_H // 2 - 70

    if font_title:
        # タイトル影
        for dx, dy in [(3, 3), (4, 4)]:
            draw.text((title_x + dx, title_y + dy), song_title,
                      font=font_title, fill=(0, 0, 0, 180))
        # タイトル本文（白）
        draw.text((title_x, title_y), song_title,
                  font=font_title, fill=(255, 255, 255, 255))

    if font_style and style_label:
        style_y = title_y + (105 if font_title else 60)
        # 細いアクセントライン
        draw.rectangle([(title_x, style_y - 4), (title_x + 50, style_y - 1)],
                        fill=(255, 220, 80, 200))
        # スタイルラベル
        draw.text((title_x + 2, style_y + 2), style_label,
                  font=font_style, fill=(0, 0, 0, 140))
        draw.text((title_x, style_y), style_label,
                  font=font_style, fill=(240, 220, 120, 230))

    result = Image.alpha_composite(base.convert("RGBA"), overlay)
    result.convert("RGB").save(str(out_path), "JPEG", quality=95)


# ── 歌詞オーバーレイ画像生成 ─────────────────────────────────────────────

def add_lyrics_overlay(base_img_path, section_name, lyrics, out_path):
    if not PILLOW_OK:
        shutil.copy(str(base_img_path), str(out_path))
        return

    base = Image.open(str(base_img_path)).convert("RGB").resize(
        (VIDEO_W, VIDEO_H), Image.LANCZOS
    )

    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 下部グラデーション
    grad_y = VIDEO_H * 50 // 100
    for y in range(grad_y, VIDEO_H):
        alpha = int(200 * (y - grad_y) / (VIDEO_H - grad_y))
        draw.rectangle([(0, y), (VIDEO_W, y)], fill=(0, 0, 0, alpha))

    font_lyrics = find_font(44)

    # 歌詞テキスト（下部）
    lines = [l for l in lyrics.split("\n") if l.strip()][:LYRICS_LINES_MAX]
    if font_lyrics and lines:
        line_h = 58
        y = VIDEO_H - len(lines) * line_h - 40
        for line in lines:
            # 影（複数重ね）
            for dx, dy in [(2, 2), (3, 3)]:
                draw.text((20 + dx, y + dy), line, font=font_lyrics, fill=(0, 0, 0, 160))
            # 本文（白）
            draw.text((20, y), line, font=font_lyrics, fill=(255, 255, 255, 255))
            y += line_h

    result = Image.alpha_composite(base.convert("RGBA"), overlay)
    result.convert("RGB").save(str(out_path), "JPEG", quality=93)


# ── 黒背景フォールバック ──────────────────────────────────────────────────

def make_blank_image(out_path, label=""):
    if PILLOW_OK:
        img = Image.new("RGB", (VIDEO_W, VIDEO_H), (12, 12, 28))
        draw = ImageDraw.Draw(img)
        font = find_font(60)
        if font and label:
            try:
                draw.text((VIDEO_W // 2, VIDEO_H // 2), label, font=font,
                          fill=(180, 180, 210), anchor="mm")
            except Exception:
                draw.text((100, VIDEO_H // 2 - 30), label, font=font,
                          fill=(180, 180, 210))
        img.save(str(out_path), "JPEG", quality=90)
    else:
        subprocess.run(
            [FFMPEG_CMD, "-y", "-f", "lavfi",
             "-i", f"color=black:size={VIDEO_W}x{VIDEO_H}:rate=1",
             "-vframes", "1", str(out_path)],
            capture_output=True,
        )


# ── ffmpeg 動画生成 ──────────────────────────────────────────────────────

def build_video_from_sections(section_images, section_durations, audio_path,
                               out_path, total_duration, title_img=None):
    """
    - section_images[0] がタイトル用画像なら title_img=True で渡す
    - タイトルには fade-in を追加
    - 音声は TITLE_DURATION 秒オフセット（タイトルは無音）
    """
    # タイトル画像を先頭に追加
    all_images = list(section_images)
    all_durations = list(section_durations)
    if title_img is not None:
        all_images.insert(0, title_img)
        all_durations.insert(0, TITLE_DURATION)

    n = len(all_images)
    cf = min(CROSSFADE_SEC, min(all_durations) * 0.35)

    inputs = []
    for img in all_images:
        inputs += ["-loop", "1", "-i", str(img)]
    inputs += ["-i", str(audio_path)]

    filter_parts = []

    for i, (img, dur) in enumerate(zip(all_images, all_durations)):
        dur_frames = max(int(dur * FPS), 2)
        zoom_end = 1.0 + ZOOM_AMOUNT

        if i % 2 == 0:
            z_expr = f"min({zoom_end:.3f},1.0+{ZOOM_AMOUNT:.3f}*on/{dur_frames})"
        else:
            z_expr = f"max(1.0,{zoom_end:.3f}-{ZOOM_AMOUNT:.3f}*on/{dur_frames})"

        # タイトル（i==0 かつ title_img あり）には fade-in を追加
        fade_filter = ""
        if title_img is not None and i == 0:
            fade_filter = f",fade=t=in:st=0:d=1.0"

        zp = (
            f"[{i}:v]"
            f"scale={VIDEO_W * 2}:{VIDEO_H * 2}:flags=bicubic,"
            f"zoompan="
            f"z='{z_expr}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={dur_frames}:"
            f"fps={FPS}:"
            f"s={VIDEO_W}x{VIDEO_H},"
            f"setsar=1"
            f"{fade_filter}[v{i}]"
        )
        filter_parts.append(zp)

    # xfade チェーン
    if n == 1:
        last_video = "v0"
    else:
        offset = all_durations[0] - cf
        filter_parts.append(
            f"[v0][v1]xfade=transition=fade:duration={cf:.2f}:offset={offset:.2f}[xf1]"
        )
        for i in range(2, n):
            offset += all_durations[i - 1] - cf
            filter_parts.append(
                f"[xf{i-1}][v{i}]xfade=transition=fade:duration={cf:.2f}:offset={offset:.2f}[xf{i}]"
            )
        last_video = f"xf{n-1}"

    # 音声の長さに合わせてトリム
    # タイトル付きの場合は映像全体 = タイトル秒 + 音楽秒
    total_video_dur = total_duration + (TITLE_DURATION if title_img is not None else 0)
    filter_parts.append(
        f"[{last_video}]trim=0:{total_video_dur:.2f},setpts=PTS-STARTPTS[vout]"
    )

    # 音声を TITLE_DURATION 秒遅らせる（タイトルは無音）
    if title_img is not None:
        filter_parts.append(
            f"[{n}:a]adelay={int(TITLE_DURATION * 1000)}:all=1[aout]"
        )
        amap = "[aout]"
    else:
        amap = f"{n}:a"

    filter_complex = "; ".join(filter_parts)

    cmd = [
        FFMPEG_CMD, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", amap,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-t", str(total_video_dur),
        str(out_path),
    ]

    dur_min = int(total_duration // 60)
    dur_sec = int(total_duration % 60)
    print(f"  encoding ({n} clips incl. title, {dur_min}:{dur_sec:02d} + {TITLE_DURATION:.0f}s title)...")

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        for line in result.stderr.strip().split("\n")[-12:]:
            if any(kw in line.lower() for kw in ("error", "invalid", "failed", "no such")):
                print(f"  ffmpeg: {line}")
        # デバッグ用: 最後の10行を出力
        print("--- ffmpeg stderr (last 10 lines) ---")
        for line in result.stderr.strip().split("\n")[-10:]:
            print(f"  {line}")
        return False

    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  done: {out_path.name} ({size_mb:.1f} MB)")
    return True


# ── メイン処理 ────────────────────────────────────────────────────────────────

def load_results(date_str):
    p = Path("output") / date_str / "results.json"
    if not p.exists():
        raise FileNotFoundError(f"results.json not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_results(date_str, data):
    p = Path("output") / date_str / "results.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_video(song, out_dir, date_str, force=False):
    song_id    = song["id"]
    mp4_path   = out_dir / f"{song_id}.mp4"

    if mp4_path.exists() and not force:
        print(f"  exists: {mp4_path.name}  (--force to regenerate)")
        return mp4_path

    total_dur  = float(song.get("duration") or song.get("duration_sec") or 0)
    audio_url  = song.get("audio_url")
    song_title = song.get("title", "Suno AI Music")
    style_label = song.get("style_label", "")
    tags        = song.get("tags", "cinematic")

    if not audio_url:
        print(f"  no audio_url: {song_id}")
        return None

    lyrics_data  = parse_lyrics_file(date_str)
    sections     = lyrics_data.get("sections", [])
    lyrics_title = lyrics_data.get("title", "") or song_title

    # タイトルの "(Style)" 部分を除去して曲名だけ表示
    display_title = lyrics_title if lyrics_title else song_title
    # "曲名 (スタイル)" の形式を取り除く
    if "(" in display_title:
        display_title = display_title[:display_title.rfind("(")].strip()

    print(f"  title: {display_title}")
    print(f"  lyrics: {repr(lyrics_title)} / {len(sections)} sections")

    if not sections:
        sections = [{"name": "Song", "lyrics": display_title}]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 音声ダウンロード
        audio_path = tmp / f"{song_id}.mp3"
        print(f"  downloading audio...")
        try:
            req = urllib.request.Request(audio_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio_path.write_bytes(resp.read())
            print(f"  audio: {audio_path.stat().st_size // 1024} KB")
        except Exception as e:
            print(f"  audio download failed: {e}")
            return None

        # 実際の秒数を ffprobe で確認
        if total_dur <= 0:
            try:
                ffprobe_cmd = FFMPEG_CMD.replace("ffmpeg.EXE", "ffprobe.EXE").replace("ffmpeg", "ffprobe")
                probe = subprocess.run(
                    [ffprobe_cmd, "-v", "quiet",
                     "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )
                total_dur = float(probe.stdout.strip())
            except Exception:
                total_dur = 200.0

        section_durations_list = calc_section_durations(sections, total_dur, audio_path)
        sec_dur = total_dur / len(sections)  # fallback avg for display
        print(f"  {len(sections)} sections x {sec_dur:.1f}s = {total_dur:.0f}s")

        # タイトル背景画像
        title_raw = tmp / "title_raw.jpg"
        title_prompt = (
            f"{display_title}, cinematic music video opening, atmospheric background, "
            f"{tags[:50]}, dramatic lighting, no text, wide 16:9, high quality"
        )
        if not download_image(title_prompt, title_raw, seed=999):
            suno_url = song.get("image_url")
            if suno_url:
                try:
                    req2 = urllib.request.Request(suno_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req2, timeout=30) as r:
                        title_raw.write_bytes(r.read())
                except Exception:
                    make_blank_image(title_raw, display_title)
            else:
                make_blank_image(title_raw, display_title)

        title_img = tmp / "title.jpg"
        make_title_image(display_title, style_label, title_raw, title_img)

        # セクション画像生成
        section_images = []
        section_durations = []

        for i, sec in enumerate(sections):
            sec_name   = sec["name"]
            sec_lyrics = sec.get("lyrics", "")

            mood   = section_mood(sec_name)
            prompt = (
                f"{display_title}, {sec_name}, {mood}, "
                f"{tags[:50]}, wide 16:9, photorealistic, no text, no letters"
            )
            raw_img = tmp / f"raw_{i:02d}.jpg"

            if not download_image(prompt, raw_img, seed=i * 17 + 3):
                suno_url = song.get("image_url")
                if suno_url:
                    try:
                        req2 = urllib.request.Request(suno_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req2, timeout=30) as r:
                            raw_img.write_bytes(r.read())
                    except Exception:
                        make_blank_image(raw_img, sec_name)
                else:
                    make_blank_image(raw_img, sec_name)

            overlay_img = tmp / f"sec_{i:02d}.jpg"
            add_lyrics_overlay(raw_img, sec_name, sec_lyrics, overlay_img)
            section_images.append(overlay_img)
            section_durations.append(section_durations_list[i])

        success = build_video_from_sections(
            section_images, section_durations, audio_path, mp4_path, total_dur,
            title_img=title_img,
        )
        return mp4_path if success else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--force", action="store_true", help="overwrite existing MP4")
    args = parser.parse_args()

    print(f"\n=== Agent③ make_videos v4 : {args.date} ===")
    print("--- Dependencies ---")
    if not check_dependencies():
        print("ERROR: missing dependencies. Install Pillow and ffmpeg first.")
        sys.exit(1)
    print("--------------------\n")

    try:
        data = load_results(args.date)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    songs   = data.get("songs", [])
    out_dir = Path("output") / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    if not songs:
        print("ERROR: no songs in results.json")
        sys.exit(1)

    seen = set()
    ok = failed = 0

    for song in songs:
        status = song.get("status", "complete")
        if status not in ("complete", ""):
            print(f"skip (not complete): {song.get('id')}")
            continue
        sid = song.get("id")
        if sid in seen:
            print(f"skip (duplicate): {sid}")
            continue
        seen.add(sid)

        print(f"\n[{song.get('style_label','')}] {song.get('title','?')}")
        mp4 = make_video(song, out_dir, args.date, force=args.force)
        if mp4:
            song["video_path"] = str(mp4)
            ok += 1
        else:
            failed += 1

    save_results(args.date, data)
    print(f"\n=== done: {ok} ok / {failed} failed ===")
    print(f"output: output/{args.date}/")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
