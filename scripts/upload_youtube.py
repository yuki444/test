"""Agent 4: Upload each generated video to YouTube with title, description, and tags.

Reads output/<date>/results.json, uploads every song that has a local video_path
but no youtube_url yet, and records the resulting YouTube URL back into results.json
so re-runs are idempotent (already-uploaded videos are skipped).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from youtube_client import YouTubeClient

REPO_ROOT = Path(__file__).parent.parent
LYRICS_ROOT = REPO_ROOT / "lyrics"

# Default privacy for newly uploaded videos. Override with --privacy.
DEFAULT_PRIVACY = "unlisted"


def read_lyrics(date_str: str) -> str:
    path = LYRICS_ROOT / date_str / "song.txt"
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8")
    # Strip the optional "title: ...\n---" metadata header
    if "---" in content:
        _, _, body = content.partition("---")
        return body.strip()
    return content.strip()


def build_description(title: str, label: str, lyrics: str, tags: str, date_str: str) -> str:
    parts = [
        f"{title}",
        f"Style: {label}",
        "",
        "AI-generated music created with Suno AI.",
        f"Generated on {date_str}.",
        "",
        "── Lyrics ──",
        lyrics,
        "",
        f"#AImusic #{label.replace(' / ', ' #').replace(' ', '')} #SunoAI",
    ]
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Upload generated videos to YouTube")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date (YYYY-MM-DD)")
    parser.add_argument("--privacy", default=DEFAULT_PRIVACY,
                        choices=["public", "unlisted", "private"],
                        help="Privacy status for uploaded videos")
    args = parser.parse_args()

    output_dir = REPO_ROOT / "output" / args.date
    results_file = output_dir / "results.json"
    if not results_file.exists():
        print(f"ERROR: No results.json at {results_file}. Run make_videos.py first.")
        sys.exit(1)

    data = json.loads(results_file.read_text(encoding="utf-8"))
    title = data.get("title", "Untitled")
    lyrics = read_lyrics(args.date)

    client = YouTubeClient()

    errors = []
    uploaded = 0
    for song in data.get("songs", []):
        label = song.get("style_label", song["style"])

        if song.get("youtube_url"):
            print(f"[{label}] Already uploaded — skipping.")
            continue

        video_rel = song.get("video_path")
        if not video_rel:
            print(f"[{label}] No video_path — skipping (run make_videos.py first).")
            continue

        video_path = REPO_ROOT / video_rel
        if not video_path.exists():
            print(f"[{label}] Video file missing at {video_path} — skipping.")
            continue

        video_title = f"{title} ({label})"
        description = build_description(title, label, lyrics, song.get("tags", ""), args.date)
        tag_list = [t.strip() for t in song.get("tags", "").split(",") if t.strip()]
        tag_list += ["AI music", "Suno AI", label]

        print(f"[{label}] Uploading '{video_title}'...")
        try:
            resp = client.upload_video(
                video_path=str(video_path),
                title=video_title,
                description=description,
                tags=tag_list,
                privacy_status=args.privacy,
            )
            video_id = resp["id"]
            song["youtube_id"] = video_id
            song["youtube_url"] = f"https://youtu.be/{video_id}"
            print(f"  Uploaded: {song['youtube_url']}")
            uploaded += 1
        except Exception as e:
            print(f"  ERROR [{label}]: {e}")
            errors.append({"style": song["style"], "stage": "upload_youtube", "error": str(e)})

    data.setdefault("errors", []).extend(errors)
    results_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone! {uploaded} video(s) uploaded to YouTube.")
    if errors:
        print(f"{len(errors)} error(s) — see results.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
