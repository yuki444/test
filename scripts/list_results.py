"""List generated songs across all dates or a specific date."""
import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def show_results(date_dir: Path):
    results_file = date_dir / "results.json"
    if not results_file.exists():
        return
    data = json.loads(results_file.read_text(encoding="utf-8"))
    print(f"\n=== {data['date']} : {data['title']} ===")
    for song in data.get("songs", []):
        dur = song.get("duration_sec", 0)
        print(f"  [{song['style_label']}]  {dur:.0f}s ({dur/60:.1f}min)")
        if song.get("audio_url"):
            print(f"    Audio : {song['audio_url']}")
        if song.get("video_url"):
            print(f"    Video : {song['video_url']}")
    for err in data.get("errors", []):
        print(f"  [ERROR] {err['style']}: {err['error']}")


def main():
    parser = argparse.ArgumentParser(description="List generated songs")
    parser.add_argument("--date", help="Show only this date (YYYY-MM-DD)")
    args = parser.parse_args()

    output_root = REPO_ROOT / "output"
    if not output_root.exists():
        print("No output directory found. Run generate_music.py first.")
        return

    if args.date:
        show_results(output_root / args.date)
    else:
        for date_dir in sorted(output_root.iterdir()):
            if date_dir.is_dir():
                show_results(date_dir)


if __name__ == "__main__":
    main()
