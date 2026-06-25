"""Generate a song in today's day-of-week style using Suno API."""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from suno_client import SunoClient

REPO_ROOT = Path(__file__).parent.parent
STYLES_FILE = REPO_ROOT / "config" / "styles.json"

# Target: 4-5 minutes in seconds
TARGET_MIN = 4 * 60
TARGET_MAX = 5 * 60


def load_styles() -> list[dict]:
    return json.loads(STYLES_FILE.read_text(encoding="utf-8"))


def get_today_style(target_date: str | None = None) -> dict | None:
    """今日の曜日に対応するスタイルを返す。"""
    all_styles = load_styles()
    # day_of_week が設定されているスタイルのみ
    day_styles = {s["day_of_week"]: s for s in all_styles if "day_of_week" in s}
    if not day_styles:
        return None
    if target_date:
        d = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        d = datetime.today()
    dow = d.weekday()  # 0=月, 6=日
    return day_styles.get(dow)


def parse_lyrics_file(path: Path) -> dict:
    """song.txt を解析してタイトルと歌詞本文を返す。"""
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
    """1スタイルで曲を生成する。"""
    label = style["label"]
    # gender / vocal_hint を tags に追加（Suno が声質をより合わせやすくなる）
    base_tags = style["tags"]
    vocal_hint = style.get("vocal_hint", "")
    full_tags = f"{base_tags}, {vocal_hint}".strip(", ") if vocal_hint else base_tags

    print(f"  [{label}] 生成中... (tags: {full_tags[:80]})")
    results = client.generate(
        prompt=lyrics,
        tags=full_tags,
        title=f"{title} ({label})",
    )

    songs = []
    for song in results:
        song_id = song["id"]
        if song.get("status") != "complete":
            print(f"    完了待ち: {song_id}...")
            song = client.wait_for_completion(song_id)

        duration = get_duration(song)
        print(f"    尺: {duration:.0f}s ({duration/60:.1f}分)")

        # 4分未満なら延長
        if duration < TARGET_MIN:
            print(f"    4-5分に延長中...")
            continue_at = max(0, duration - 5)
            ext_results = client.extend_audio(song_id, continue_at=continue_at)
            for ext in ext_results:
                ext_id = ext["id"]
                if ext.get("status") != "complete":
                    ext = client.wait_for_completion(ext_id)
                ext_dur = get_duration(ext)
                print(f"    延長後: {ext_dur:.0f}s ({ext_dur/60:.1f}分)")
                song = ext
                break

        songs.append({
            "id": song["id"],
            "style": style["name"],
            "style_label": style["label"],
            "day_of_week": style.get("day_of_week"),
            "title": song.get("title", title),
            "audio_url": song.get("audio_url", ""),
            "video_url": song.get("video_url", ""),
            "image_url": song.get("image_url", ""),
            "duration_sec": get_duration(song),
            "tags": full_tags,
            "gender": style.get("gender", "unisex"),
        })

    return songs


def main():
    parser = argparse.ArgumentParser(description="Suno AI で今日のスタイルの曲を生成する")
    parser.add_argument("--date", default=date.today().isoformat(), help="日付 (YYYY-MM-DD)")
    parser.add_argument("--styles", nargs="+", metavar="STYLE_NAME",
                        help="スタイル名を指定（省略時は今日の曜日スタイル）")
    parser.add_argument("--all-styles", action="store_true",
                        help="全スタイルで生成（旧来の動作）")
    args = parser.parse_args()

    lyrics_file = REPO_ROOT / "lyrics" / args.date / "song.txt"
    if not lyrics_file.exists():
        print(f"ERROR: 歌詞ファイルなし: {lyrics_file}")
        print(f"Cowork PM エージェントが自動生成するか、手動で作成してください")
        sys.exit(1)

    output_dir = REPO_ROOT / "output" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_lyrics_file(lyrics_file)
    title  = parsed["title"]
    lyrics = parsed["lyrics"]
    print(f'生成: "{title}"  ({args.date})')

    # スタイル選択
    all_styles = load_styles()
    if args.all_styles:
        active_styles = all_styles
        print(f"モード: 全スタイル ({len(active_styles)}種)")
    elif args.styles:
        active_styles = [s for s in all_styles if s["name"] in args.styles]
        if not active_styles:
            print(f"ERROR: スタイルが見つかりません。利用可能: {[s['name'] for s in all_styles]}")
            sys.exit(1)
        print(f"モード: 指定スタイル {[s['name'] for s in active_styles]}")
    else:
        # 今日の曜日スタイル（デフォルト）
        today_style = get_today_style(args.date)
        if today_style:
            active_styles = [today_style]
            dow_names = ["月", "火", "水", "木", "金", "土", "日"]
            dow = today_style.get("day_of_week", 0)
            print(f"モード: 今日の曜日スタイル ({dow_names[dow]}曜 = {today_style['label']})")
        else:
            active_styles = all_styles
            print(f"モード: 全スタイル（曜日設定なし）")

    client = SunoClient()
    try:
        limit = client.get_limit()
        print(f"クレジット: {limit}")
    except Exception as e:
        print(f"Warning: クレジット確認失敗: {e}")

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

    print(f"\n完了！ {len(all_songs)} 曲生成 ({len(active_styles)} スタイル)")
    print(f"結果: {results_file}")
    for song in all_songs:
        dur = song["duration_sec"]
        print(f"  [{song['style_label']}] {dur:.0f}s ({dur/60:.1f}分) → {song['audio_url']}")

    if errors:
        print(f"\n{len(errors)} エラー — results.json を確認してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
