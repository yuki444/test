# coding: utf-8
"""
Agent③ v2 — 動画化スクリプト（歌詞アニメーション対応）

機能:
  - lyrics/YYYY-MM-DD/song.txt から歌詞セクションを解析
  - Pollinations AI でセクションごとに背景画像を生成
  - Pillow で歌詞テキストを画像に重ねる（日本語対応）
  - ffmpeg zoompan で Ken Burns エフェクト（ゆっくりズーム）
  - ffmpeg xfade でセクション間クロスフェード
  - 音声トラックと合成して MP4 を出力

使い方:
  python scripts/make_videos.py --date 2026-06-25
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# Pillow は requirements.txt に含まれている
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False
    print("⚠️  Pillow が未インストール: pip install Pillow")

# ── 設定 ──────────────────────────────────────────────────────────────────────

VIDEO_W, VIDEO_H = 1280, 720
FPS = 25
CROSSFADE_SEC = 1.0          # セクション間クロスフェード秒数
LYRICS_LINES_MAX = 4         # 1画面に表示する最大行数

REPO_ROOT = Path(__file__).parent.parent
LYRICS_DIR = REPO_ROOT / "lyrics"

# ffmpeg フルパス解決
_ffmpeg_env = os.environ.get("FFMPEG_CMD", "ffmpeg")
_ffmpeg_path = shutil.which(_ffmpeg_env)
FFMPEG_CMD = _ffmpeg_path if _ffmpeg_path else _ffmpeg_env

# 日本語対応フォント候補（Windows / Linux）
FONT_CANDIDATES = [
    "C:\\Windows\\Fonts\\meiryo.ttc",
    "C:\\Windows\\Fonts\\YuGothM.ttc",
    "C:\\Windows\\Fonts\\msgothic.ttc",
    "C:\\Windows\\Fonts\\yugothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
]


# ── 歌詞パース ────────────────────────────────────────────────────────────────

def parse_lyrics_file(date_str: str) -> dict:
    """lyrics/YYYY-MM-DD/song.txt を解析してセクションリストを返す。"""
    path = LYRICS_DIR / date_str / "song.txt"
    if not path.exists():
        return {"title": "", "sections": [], "raw": ""}

    content = path.read_text(encoding="utf-8").strip()
    lines = content.split("\n")

    # メタデータヘッダーを読む
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

    # セクション分割
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

    # タイムスタンプは make_video 時に duration から計算
    return {"title": title, "sections": sections, "raw": body}


# ── Pollinations 画像生成 ──────────────────────────────────────────────────

SECTION_MOOD = {
    "Verse": "calm, storytelling, atmospheric",
    "Verse 1": "calm opening, morning light, cinematic",
    "Verse 2": "emotional, memories, soft light",
    "Pre-Chorus": "building tension, dramatic, twilight",
    "Chorus": "energetic, uplifting, vibrant colors, emotional climax",
    "Bridge": "introspective, turning point, mysterious",
    "Outro": "peaceful, resolution, fading light, cinematic ending",
    "Intro": "opening, ambient, establishing shot",
}

def section_mood(name: str) -> str:
    for key, mood in SECTION_MOOD.items():
        if name.lower().startswith(key.lower()):
            return mood
    return "cinematic, artistic, atmospheric"


def download_pollinations_image(prompt: str, out_path: Path, seed: int = 42) -> bool:
    """Pollinations AI から画像を生成してダウンロードする。"""
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={VIDEO_W}&height={VIDEO_H}&nologo=true&seed={seed}"
    )
    try:
        print(f"    🎨 画像生成中: {prompt[:60]}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            out_path.write_bytes(resp.read())
        print(f"    ✅ 保存: {out_path.name}")
        return True
    except Exception as e:
        print(f"    ⚠️  画像生成失敗: {e}")
        return False


# ── Pillow テキスト合成 ────────────────────────────────────────────────────

def find_font(size: int = 36):
    """日本語対応フォントを探す。"""
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def add_lyrics_overlay(base_img_path: Path, section_name: str, lyrics: str, out_path: Path):
    """
    背景画像に歌詞テキストを合成する。
    - 下部 1/3 に半透明グラデーション
    - セクション名（小）+ 歌詞テキスト（大）
    """
    if not PILLOW_OK:
        shutil.copy(base_img_path, out_path)
        return

    img = Image.open(base_img_path).convert("RGBA").resize((VIDEO_W, VIDEO_H), Image.LANCZOS)

    # 下部グラデーションオーバーレイ
    grad = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw_g = ImageDraw.Draw(grad)
    grad_top = VIDEO_H * 55 // 100
    for y in range(grad_top, VIDEO_H):
        alpha = int(200 * (y - grad_top) / (VIDEO_H - grad_top))
        draw_g.line([(0, y), (VIDEO_W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, grad)

    draw = ImageDraw.Draw(img)

    # フォント
    font_section = find_font(22)
    font_lyrics  = find_font(36)

    # セクション名（右上コーナー）
    section_text = f"♪ {section_name}"
    draw.text((VIDEO_W - 20, 20), section_text, font=font_section,
              fill=(255, 255, 255, 180), anchor="rt" if hasattr(draw, 'textbbox') else None)

    # 歌詞テキスト（下部）
    lines = [l for l in lyrics.split("\n") if l.strip()][:LYRICS_LINES_MAX]
    y_start = VIDEO_H - 40 - len(lines) * 48
    for line in lines:
        # 影
        draw.text((22, y_start + 2), line, font=font_lyrics, fill=(0, 0, 0, 160))
        # 本文
        draw.text((20, y_start), line, font=font_lyrics, fill=(255, 255, 255, 240))
        y_start += 48

    img.convert("RGB").save(str(out_path), "JPEG", quality=92)


# ── ffmpeg 動画生成 ────────────────────────────────────────────────────────

def build_video_from_sections(
    section_images: list[Path],
    section_durations: list[float],
    audio_path: Path,
    out_path: Path,
    total_duration: float,
) -> bool:
    """
    複数の画像からセクション動画を生成する。
    - zoompan で Ken Burns エフェクト（偶数: ズームイン / 奇数: ズームアウト）
    - xfade でセクション間クロスフェード
    - 音声トラックを合成
    """
    n = len(section_images)
    if n == 0:
        return False

    cf = CROSSFADE_SEC  # クロスフェード秒数

    # --- ffmpeg 入力 ---
    inputs = []
    for img in section_images:
        inputs += ["-loop", "1", "-i", str(img)]
    inputs += ["-i", str(audio_path)]

    # --- フィルターグラフ ---
    filter_parts = []

    for i, (img, dur) in enumerate(zip(section_images, section_durations)):
        dur_frames = int(dur * FPS)
        # Ken Burns: 偶数→ズームイン、奇数→ズームアウト
        if i % 2 == 0:
            zoom_expr = f"'min(1+({i}*0.0001)+on*0.0005,1.5)'"
            x_expr    = "'iw/2-(iw/zoom/2)'"
            y_expr    = "'ih/2-(ih/zoom/2)'"
        else:
            zoom_expr = f"'max(1.5-on*0.0005,1.0)'"
            x_expr    = "'iw/2-(iw/zoom/2)+sin(on/30)*20'"
            y_expr    = "'ih/2-(ih/zoom/2)'"

        zp = (
            f"[{i}:v]zoompan="
            f"z={zoom_expr}:d={dur_frames}:"
            f"x={x_expr}:y={y_expr}:s={VIDEO_W}x{VIDEO_H},"
            f"fps={FPS},setsar=1[v{i}]"
        )
        filter_parts.append(zp)

    # xfade チェーン
    if n == 1:
        last_video = "v0"
    else:
        offset = section_durations[0] - cf
        filter_parts.append(
            f"[v0][v1]xfade=transition=fade:duration={cf}:offset={offset:.2f}[xf1]"
        )
        for i in range(2, n):
            offset += section_durations[i - 1] - cf
            prev = f"xf{i-1}"
            curr = f"v{i}"
            nxt  = f"xf{i}"
            filter_parts.append(
                f"[{prev}][{curr}]xfade=transition=fade:duration={cf}:offset={offset:.2f}[{nxt}]"
            )
        last_video = f"xf{n-1}"

    # 最終ビデオを固定長にトリム（音声の長さに合わせる）
    filter_parts.append(f"[{last_video}]trim=0:{total_duration:.2f},setpts=PTS-STARTPTS[vout]")

    filter_complex = "; ".join(filter_parts)

    cmd = [
        FFMPEG_CMD, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{n}:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-metadata", f"title=Suno AI Music",
        str(out_path),
    ]

    print(f"  🎬 動画エンコード中（{n} セクション, {total_duration:.0f}秒）...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"  ❌ ffmpeg エラー:\n{result.stderr[-800:]}")
        return False

    size_mb = out_path.stat().st_size / 1_048_576
    dur_min = int(total_duration // 60)
    dur_sec = int(total_duration % 60)
    print(f"  ✅ 完了: {out_path.name} ({size_mb:.1f} MB, {dur_min}:{dur_sec:02d})")
    return True


# ── メイン処理 ────────────────────────────────────────────────────────────────

def load_results(date_str: str) -> dict:
    p = Path("output") / date_str / "results.json"
    if not p.exists():
        raise FileNotFoundError(f"results.json が見つかりません: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_results(date_str: str, data: dict):
    p = Path("output") / date_str / "results.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_video(song: dict, out_dir: Path, date_str: str) -> Path | None:
    song_id  = song["id"]
    mp4_path = out_dir / f"{song_id}.mp4"

    if mp4_path.exists():
        print(f"  ✅ 既存: {mp4_path.name}")
        return mp4_path

    total_dur = song.get("duration") or song.get("duration_sec", 0)
    audio_url = song.get("audio_url")
    song_title = song.get("title", "Suno AI Music")
    tags       = song.get("tags", "cinematic")

    if not audio_url:
        print(f"  ⚠️  audio_url なし: {song_id}")
        return None

    # 歌詞を解析
    lyrics_data = parse_lyrics_file(date_str)
    sections    = lyrics_data.get("sections", [])

    if not sections:
        print(f"  ℹ️  歌詞ファイルなし — シンプル版（静止画）で生成します")
        sections = [{"name": "Song", "lyrics": ""}]

    print(f"\n  📖 歌詞セクション数: {len(sections)}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. 音声ダウンロード
        audio_path = tmp / f"{song_id}.mp3"
        print(f"  ⬇  音声ダウンロード中...")
        req = urllib.request.Request(audio_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            audio_path.write_bytes(resp.read())
        print(f"  ✅ 音声保存: {audio_path.name}")

        # 2. セクションごとに画像生成 + 歌詞テキスト合成
        section_images    = []
        section_durations = []
        raw_dur = total_dur if total_dur > 0 else 200
        sec_dur = raw_dur / len(sections)

        for i, sec in enumerate(sections):
            sec_name   = sec["name"]
            sec_lyrics = sec.get("lyrics", "")

            # Pollinations 画像生成
            mood    = section_mood(sec_name)
            prompt  = f"{song_title}, {sec_name}, {mood}, {tags}, 16:9 wide, no text, high quality"
            raw_img = tmp / f"section_{i:02d}_raw.jpg"

            if not download_pollinations_image(prompt, raw_img, seed=i * 7 + 1):
                # フォールバック: Suno のアートワーク
                suno_img_url = song.get("image_url")
                if suno_img_url:
                    try:
                        req2 = urllib.request.Request(suno_img_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req2, timeout=30) as r:
                            raw_img.write_bytes(r.read())
                    except Exception:
                        _make_blank_image(raw_img, sec_name)
                else:
                    _make_blank_image(raw_img, sec_name)

            # 歌詞テキスト合成
            overlay_img = tmp / f"section_{i:02d}.jpg"
            add_lyrics_overlay(raw_img, sec_name, sec_lyrics, overlay_img)

            section_images.append(overlay_img)
            section_durations.append(sec_dur)

        # 3. ffmpeg で動画生成
        success = build_video_from_sections(
            section_images,
            section_durations,
            audio_path,
            mp4_path,
            raw_dur,
        )

        if not success:
            return None

    return mp4_path


def _make_blank_image(out_path: Path, label: str = ""):
    """フォールバック: 黒背景の画像を生成する。"""
    if PILLOW_OK:
        img = Image.new("RGB", (VIDEO_W, VIDEO_H), (20, 20, 40))
        draw = ImageDraw.Draw(img)
        font = find_font(48)
        draw.text((VIDEO_W // 2, VIDEO_H // 2), label,
                  font=font, fill=(200, 200, 200), anchor="mm" if hasattr(draw, 'textbbox') else None)
        img.save(str(out_path), "JPEG")
    else:
        # ffmpeg で黒画像
        subprocess.run([
            FFMPEG_CMD, "-y", "-f", "lavfi",
            "-i", f"color=black:size={VIDEO_W}x{VIDEO_H}:rate=1",
            "-vframes", "1", str(out_path)
        ], capture_output=True)


def main():
    parser = argparse.ArgumentParser(description="歌詞アニメーション動画を生成する")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    if not _ffmpeg_path:
        print("❌ ffmpeg が見つかりません。")
        print("   Windows: winget install Gyan.FFmpeg")
        sys.exit(1)
    else:
        print(f"✅ ffmpeg: {FFMPEG_CMD}")

    if not PILLOW_OK:
        print("⚠️  Pillow が未インストールです（テキスト合成なし）: pip install Pillow")

    print(f"🎬 Agent③ 動画化 v2 開始: {args.date}")

    data    = load_results(args.date)
    songs   = data.get("songs", [])
    out_dir = Path("output") / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    if not songs:
        print("⚠️  songs が空です。")
        sys.exit(1)

    seen    = set()
    ok      = 0
    failed  = 0

    for song in songs:
        status = song.get("status", "complete")
        if status not in ("complete", ""):
            print(f"  スキップ（未完了）: {song.get('id')}")
            continue
        sid = song.get("id")
        if sid in seen:
            print(f"  スキップ（重複）: {sid}")
            continue
        seen.add(sid)

        print(f"\n  処理中: {song.get('title','?')} [{song.get('style_label', '')}]")
        mp4 = make_video(song, out_dir, args.date)
        if mp4:
            song["video_path"] = str(mp4)
            ok += 1
        else:
            failed += 1

    save_results(args.date, data)

    print(f"\n{'='*50}")
    print(f"  動画化完了: {ok} 曲 / 失敗: {failed} 曲")
    print(f"  保存先: output/{args.date}/")
    print(f"{'='*50}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
