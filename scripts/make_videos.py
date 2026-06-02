"""Agent 3: Generate a cover image and combine it with each song's audio into a video.

For every song in output/<date>/results.json this script:
  1. Generates a style-matched cover image via Pollinations AI (free, no API key)
  2. Downloads the song's audio from its Suno audio_url
  3. Combines image + audio into an MP4 with ffmpeg
  4. Records the local video path back into results.json

Requires ffmpeg to be installed (preinstalled on GitHub Actions ubuntu runners).
"""
import argparse
import json
import subprocess
import sys
import urllib.parse
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
STYLES_FILE = REPO_ROOT / "config" / "styles.json"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def load_styles() -> dict:
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    return {s["name"]: s for s in styles}


def generate_image(prompt: str, dest: Path, width: int = 1280, height: int = 720) -> None:
    """Generate a cover image with Pollinations AI (free, no key, no signup)."""
    encoded = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}/{encoded}"
    params = {"width": width, "height": height, "nologo": "true", "model": "flux"}
    resp = requests.get(url, params=params, timeout=180)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def download_audio(audio_url: str, dest: Path) -> None:
    resp = requests.get(audio_url, timeout=300, stream=True)
    resp.raise_for_status()
    with dest.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def make_video(image_path: Path, audio_path: Path, dest: Path) -> None:
    """Combine a static image and audio track into an MP4 using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-1000:]}")


def main():
    parser = argparse.ArgumentParser(description="Make videos from generated songs")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date (YYYY-MM-DD)")
    args = parser.parse_args()

    output_dir = REPO_ROOT / "output" / args.date
    results_file = output_dir / "results.json"
    if not results_file.exists():
        print(f"ERROR: No results.json at {results_file}. Run generate_music.py first.")
        sys.exit(1)

    data = json.loads(results_file.read_text(encoding="utf-8"))
    styles = load_styles()
    title = data.get("title", "Untitled")

    media_dir = output_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    errors = []
    for song in data.get("songs", []):
        style_name = song["style"]
        label = song.get("style_label", style_name)
        print(f"[{label}] Building video...")

        try:
            style = styles.get(style_name, {})
            image_prompt = style.get("image_prompt", f"album cover art for {title}, {label}")

            image_path = media_dir / f"{style_name}.png"
            audio_path = media_dir / f"{style_name}.mp3"
            video_path = media_dir / f"{style_name}.mp4"

            print(f"  Generating cover image...")
            generate_image(image_prompt, image_path)

            audio_url = song.get("audio_url", "")
            if not audio_url:
                raise RuntimeError("song has no audio_url")
            print(f"  Downloading audio...")
            download_audio(audio_url, audio_path)

            print(f"  Encoding video with ffmpeg...")
            make_video(image_path, audio_path, video_path)

            song["image_path"] = str(image_path.relative_to(REPO_ROOT))
            song["video_path"] = str(video_path.relative_to(REPO_ROOT))
            print(f"  Done: {video_path}")
        except Exception as e:
            print(f"  ERROR [{label}]: {e}")
            errors.append({"style": style_name, "stage": "make_video", "error": str(e)})

    data.setdefault("errors", []).extend(errors)
    results_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    made = sum(1 for s in data.get("songs", []) if s.get("video_path"))
    print(f"\nDone! {made} videos built in {media_dir}")
    if errors:
        print(f"{len(errors)} error(s) — see results.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
