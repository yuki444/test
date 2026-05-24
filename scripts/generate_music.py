"""Generate songs in 5 styles from a lyrics file using Suno API."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from suno_client import SunoClient

REPO_ROOT = Path(__file__).parent.parent
STYLES_FILE = REPO_ROOT / "config" / "styles.json"

# Target: 4-5 minutes in seconds
TARGET_MIN = 4 * 60
TARGET_MAX = 5 * 60


def load_styles() -> list[dict]:
    return json.loads(STYLES_FILE.read_text(encoding="utf-8"))


def parse_lyrics_file(path: Path) -> dict:
    """Parse song.txt with optional metadata header.

    Header format (optional):
        title: My Song Title
        ---
        [Verse 1]
        lyrics here...
    """
    content = path.read_text(encoding="utf-8").strip()
    lines = content.split("\n")

    metadata = {}
    body_start = 0

    if lines and ":" in lines[0] and not lines[0].startswith("["):
        for i, line in enumerate(lines):
            if line.strip() == "---":
                body_start = i + 1
                break
            if ":" in line:
                key, _, val = line.partition(":")
                metadata[key.strip().lower()] = val.strip()

    lyrics = "\n".join(lines[body_start:]).strip()
    return {"title": metadata.get("title", "Untitled"), "lyrics": lyrics}


def get_duration(song: dict) -> float:
    return song.get("metadata", {}).get("duration", 0) or song.get("duration", 0) or 0


def generate_for_style(client: SunoClient, title: str, lyrics: str, style: dict) -> list[dict]:
    print(f"  [{style['label']}] Generating...")
    results = client.generate(
        prompt=lyrics,
        tags=style["tags"],
        title=f"{title} ({style['label']})",
    )

    songs = []
    for song in results:
        song_id = song["id"]
        if song.get("status") != "complete":
            print(f"    Waiting for {song_id}...")
            song = client.wait_for_completion(song_id)

        duration = get_duration(song)
        print(f"    Duration: {duration:.0f}s ({duration/60:.1f}min)")

        # Extend if shorter than 4 minutes
        if duration < TARGET_MIN:
            print(f"    Extending to reach 4-5 min target...")
            # Continue from 5 seconds before end to create a smooth join
            continue_at = max(0, duration - 5)
            ext_results = client.extend_audio(song_id, continue_at=continue_at)
            for ext in ext_results:
                ext_id = ext["id"]
                if ext.get("status") != "complete":
                    ext = client.wait_for_completion(ext_id)
                ext_dur = get_duration(ext)
                print(f"    Extended duration: {ext_dur:.0f}s ({ext_dur/60:.1f}min)")
                song = ext
                break

        songs.append({
            "id": song["id"],
            "style": style["name"],
            "style_label": style["label"],
            "title": song.get("title", title),
            "audio_url": song.get("audio_url", ""),
            "video_url": song.get("video_url", ""),
            "image_url": song.get("image_url", ""),
            "duration_sec": get_duration(song),
            "tags": style["tags"],
        })

    return songs


def main():
    parser = argparse.ArgumentParser(description="Generate songs from lyrics using Suno AI")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date (YYYY-MM-DD)")
    parser.add_argument("--styles", nargs="+", metavar="STYLE_NAME",
                        help="Limit to specific style names from config/styles.json")
    args = parser.parse_args()

    lyrics_file = REPO_ROOT / "lyrics" / args.date / "song.txt"
    if not lyrics_file.exists():
        print(f"ERROR: No lyrics file at {lyrics_file}")
        print(f"Create it using the template at lyrics/template/song.txt")
        sys.exit(1)

    output_dir = REPO_ROOT / "output" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_lyrics_file(lyrics_file)
    title = parsed["title"]
    lyrics = parsed["lyrics"]
    print(f"Generating: \"{title}\"  ({args.date})")

    client = SunoClient()

    try:
        limit = client.get_limit()
        print(f"Credits: {limit}")
    except Exception as e:
        print(f"Warning: could not check credits: {e}")

    all_styles = load_styles()
    if args.styles:
        active_styles = [s for s in all_styles if s["name"] in args.styles]
        if not active_styles:
            print(f"ERROR: No styles matched. Available: {[s['name'] for s in all_styles]}")
            sys.exit(1)
    else:
        active_styles = all_styles

    all_songs = []
    errors = []

    for style in active_styles:
        try:
            songs = generate_for_style(client, title, lyrics, style)
            all_songs.extend(songs)
        except Exception as e:
            print(f"  ERROR [{style['label']}]: {e}")
            errors.append({"style": style["name"], "error": str(e)})

    results = {
        "date": args.date,
        "title": title,
        "songs": all_songs,
        "errors": errors,
    }

    results_file = output_dir / "results.json"
    results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone! {len(all_songs)} songs generated in {len(active_styles)} styles.")
    print(f"Results: {results_file}")

    for song in all_songs:
        dur = song["duration_sec"]
        print(f"  [{song['style_label']}] {dur:.0f}s ({dur/60:.1f}min) → {song['audio_url']}")

    if errors:
        print(f"\n{len(errors)} error(s) occurred — see results.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
