# coding: utf-8
"""
Agent③ — 動画化スクリプト

Suno が生成した音声 (MP3/WAV) にサムネイル画像を合成して MP4 を作成します。
ffmpeg が必要です（GitHub Actions の ubuntu-latest にはデフォルトで入っています）。

使い方:
  python scripts/make_videos.py --date 2026-06-25

output/YYYY-MM-DD/results.json を読み込み、
output/YYYY-MM-DD/<song_id>.mp4 を生成して results.json を更新します。
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────

# サムネイル画像のデフォルト（リポジトリに置く）
DEFAULT_THUMBNAIL = Path("assets/thumbnail.jpg")

# ffmpeg コマンド（GitHub Actions は "ffmpeg"、ローカルは PATH 次第）
FFMPEG_CMD = os.environ.get("FFMPEG_CMD", "ffmpeg")

# ── ヘルパー ──────────────────────────────────────────────────────────────────

def load_results(date_str: str) -> dict:
    p = Path("output") / date_str / "results.json"
    if not p.exists():
        raise FileNotFoundError(f"results.json が見つかりません: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_results(date_str: str, data: dict):
    p = Path("output") / date_str / "results.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def download_file(url: str, dest: Path):
    """URL からファイルをダウンロードする。"""
    print(f"    ⬇  ダウンロード中: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())
    print(f"    ✅ 保存: {dest}")


def make_thumbnail(song: dict, out_dir: Path) -> Path:
    """
    サムネイル画像を用意する。
    1. 曲の image_url があればダウンロード
    2. なければ assets/thumbnail.jpg を使用
    3. assets/thumbnail.jpg もなければデフォルトの黒背景を生成
    """
    thumb_path = out_dir / f"{song['id']}_thumb.jpg"

    if thumb_path.exists():
        return thumb_path

    # Suno の曲データには image_url が含まれることがある
    image_url = song.get("image_url") or song.get("image_large_url")
    if image_url:
        try:
            download_file(image_url, thumb_path)
            return thumb_path
        except Exception as e:
            print(f"    ⚠️  アートワーク取得失敗: {e} → デフォルトサムネイルを使用")

    if DEFAULT_THUMBNAIL.exists():
        import shutil
        shutil.copy(DEFAULT_THUMBNAIL, thumb_path)
        return thumb_path

    # フォールバック: ffmpeg で黒背景 + タイトルテキストを生成
    title = song.get("title", "Suno AI Music")[:50]
    cmd = [
        FFMPEG_CMD, "-y",
        "-f", "lavfi",
        "-i", "color=black:size=1280x720:rate=1",
        "-vframes", "1",
        "-vf", f"drawtext=text='{title}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        str(thumb_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return thumb_path


def make_video(song: dict, out_dir: Path) -> Path | None:
    """
    音声ファイル + サムネイル画像 → MP4 を生成する。
    生成済みなら既存ファイルを返す。
    """
    song_id  = song["id"]
    mp4_path = out_dir / f"{song_id}.mp4"

    if mp4_path.exists():
        print(f"  ✅ 既に存在: {mp4_path.name}")
        return mp4_path

    # 音声ファイルをダウンロード
    audio_url = song.get("audio_url")
    if not audio_url:
        print(f"  ⚠️  audio_url なし、スキップ: {song_id}")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        audio_path = tmp / f"{song_id}.mp3"
        try:
            download_file(audio_url, audio_path)
        except Exception as e:
            print(f"  ❌ 音声ダウンロード失敗: {e}")
            return None

        # サムネイル取得
        try:
            thumb_path = make_thumbnail(song, out_dir)
        except Exception as e:
            print(f"  ⚠️  サムネイル生成失敗: {e} → 黒背景でフォールバック")
            thumb_path = None

        # ffmpeg で MP4 生成
        # -loop 1: 画像を動画の長さ分ループ
        # -shortest: 音声が終わったら映像も終了
        title = song.get("title", "Suno AI Music")
        tags  = song.get("tags", "")

        if thumb_path and thumb_path.exists():
            cmd = [
                FFMPEG_CMD, "-y",
                "-loop", "1",
                "-i", str(thumb_path),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                # YouTube 推奨: 1280x720
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                # メタデータ
                "-metadata", f"title={title}",
                "-metadata", f"comment={tags}",
                str(mp4_path),
            ]
        else:
            # 画像なし: 黒背景
            cmd = [
                FFMPEG_CMD, "-y",
                "-f", "lavfi", "-i", "color=black:size=1280x720:rate=30",
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-metadata", f"title={title}",
                str(mp4_path),
            ]

        print(f"  🎬 MP4 生成中: {song_id}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ ffmpeg エラー:\n{result.stderr[-500:]}")
            return None

        size_mb = mp4_path.stat().st_size / 1_048_576
        print(f"  ✅ MP4 生成完了: {mp4_path.name} ({size_mb:.1f} MB)")
        return mp4_path


# ── メイン ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Suno 曲から MP4 動画を生成する")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日 (YYYY-MM-DD)")
    args = parser.parse_args()

    print(f"🎬 Agent③ 動画化 開始: {args.date}")

    data    = load_results(args.date)
    songs   = data.get("songs", [])
    out_dir = Path("output") / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    if not songs:
        print("⚠️  songs が空です。generate_music.py が正常に実行されましたか？")
        sys.exit(1)

    updated = 0
    failed  = 0

    for song in songs:
        if song.get("status") != "complete":
            print(f"  スキップ（未完了）: {song.get('id')}")
            continue

        print(f"\n  処理中: {song.get('title','?')} ({song.get('id')})")
        mp4 = make_video(song, out_dir)
        if mp4:
            song["video_path"] = str(mp4)
            updated += 1
        else:
            failed += 1

    # results.json を更新（video_path を追加）
    save_results(args.date, data)

    print(f"\n{'='*50}")
    print(f"  動画化完了: {updated} 曲 / 失敗: {failed} 曲")
    print(f"{'='*50}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
