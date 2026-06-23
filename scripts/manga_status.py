"""Display current manga series progress and optionally show a day's draft."""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"


def main():
    parser = argparse.ArgumentParser(description="漫画シリーズの進捗を表示します")
    parser.add_argument("--date", help="特定日のドラフト・プロンプトを表示 (YYYY-MM-DD)")
    args = parser.parse_args()

    state_path = MANGA_DIR / "state.json"
    if not state_path.exists():
        print("ERROR: manga/state.json が見つかりません。manga_init.py を先に実行してください。")
        sys.exit(1)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    series_path = MANGA_DIR / "config" / "series.json"
    series = json.loads(series_path.read_text(encoding="utf-8")) if series_path.exists() else {}

    title = series.get("title", "(タイトル未設定)")
    total = series.get("total_chapters", 30)
    chapter = state["current_chapter"]
    page = state["current_page"]
    total_pages = state["total_pages_generated"]
    last_date = state.get("last_generated_date") or "未生成"
    chapter_title = state["chapter_map"].get(str(chapter), {}).get("title", "")

    print(f"=== {title} ===")
    print(f"第{chapter}章「{chapter_title}」 / 全{total}章  |  {page}ページ目  |  累計{total_pages}ページ")
    print(f"最終生成日: {last_date}")

    summary = state.get("story_summary_rolling", "")
    if summary:
        print(f"\n【ストーリー要約】\n{summary}")

    cliffhanger = state.get("recent_cliffhanger", "")
    if cliffhanger:
        print(f"\n【直前のクリフハンガー】\n{cliffhanger}")

    chapters_dir = MANGA_DIR / "chapters"
    if chapters_dir.exists():
        dated_dirs = sorted(
            [d for d in chapters_dir.iterdir() if d.is_dir()],
            reverse=True,
        )[:5]
        if dated_dirs:
            print("\n【最近の生成履歴】")
            for d in dated_dirs:
                has_draft = (d / "draft.md").exists()
                has_prompts = (d / "prompts.md").exists()
                flags = " [draft]" if has_draft else ""
                flags += " [prompts]" if has_prompts else ""
                print(f"  {d.name}{flags}")

    if args.date:
        draft_path = chapters_dir / args.date / "draft.md"
        prompts_path = chapters_dir / args.date / "prompts.md"
        if draft_path.exists():
            print(f"\n{'=' * 60}")
            print(f"=== {args.date} ドラフト ===")
            print(draft_path.read_text(encoding="utf-8"))
        if prompts_path.exists():
            print(f"\n{'=' * 60}")
            print(f"=== {args.date} ChatGPT用プロンプト ===")
            print(prompts_path.read_text(encoding="utf-8"))
        if not draft_path.exists() and not prompts_path.exists():
            print(f"\n{args.date} のドラフトが見つかりません。")


if __name__ == "__main__":
    main()
