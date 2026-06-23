"""Generate today's manga scene (Japanese) and ChatGPT image prompts (English)."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"

from claude_client import ClaudeClient


SYSTEM_PROMPT = """\
あなたはプロの少年漫画作家です。毎日1ページ分のシーン（8〜12コマ）を執筆します。
以下の制約を厳守してください：
- シーン概要・コマ割り・セリフはすべて日本語で書く
- <PROMPTS>セクションの画像プロンプトは英語で書く
- 各コマのプロンプトには、そのコマに登場するキャラクターのvisual_en（外見描写）を必ず先頭に含める
- 少年漫画らしい躍動感・テンポのある展開を意識する
- 最終コマはクリフハンガーで終わり、明日への引きを作る
- 指定された4つのXMLタグ（<DRAFT>、<PROMPTS>、<ROLLING_SUMMARY>、<CLIFFHANGER>）を必ず出力する
"""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_chapter_section(master_text: str, chapter_num: int) -> str:
    pattern = rf'#{1,3} 第{chapter_num}章.+?(?=#{1,3} 第\d+章|$)'
    match = re.search(pattern, master_text, re.DOTALL)
    return match.group(0).strip() if match else ""


def load_recent_drafts(n: int = 2) -> list[tuple[str, str]]:
    chapters_dir = MANGA_DIR / "chapters"
    if not chapters_dir.exists():
        return []
    dated_dirs = sorted(
        [d for d in chapters_dir.iterdir() if d.is_dir() and d.name != ""],
        reverse=True,
    )
    results = []
    for d in dated_dirs[:n]:
        draft_file = d / "draft.md"
        if draft_file.exists():
            results.append((d.name, draft_file.read_text(encoding="utf-8")))
    return results


def extract_tag(text: str, tag: str) -> str:
    match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    if not match:
        raise ValueError(f"タグ <{tag}> が見つかりませんでした")
    return match.group(1).strip()


def build_prompt(state: dict, series: dict, characters: dict,
                 chapter_section: str, recent_drafts: list[tuple[str, str]],
                 target_date: str) -> str:
    chapter = state["current_chapter"]
    page = state["current_page"]
    chapter_info = state["chapter_map"].get(str(chapter), {})
    chapter_title = chapter_info.get("title", "")
    is_first_page = state["total_pages_generated"] == 0

    chars_compact = json.dumps(
        {name: {"role": c["role"], "visual_en": c["visual_en"], "personality_jp": c["personality_jp"]}
         for name, c in characters.items()},
        ensure_ascii=False, indent=2
    )

    if is_first_page:
        context_block = "（連載初回。第1章の冒頭から自然な形で始めてください）"
        recent_block = "（前回のドラフトなし。新連載の開始です）"
    else:
        summary = state.get("story_summary_rolling") or "（要約なし）"
        cliffhanger = state.get("recent_cliffhanger") or "（なし）"
        context_block = f"# これまでのストーリー\n{summary}\n\n# 直前のクリフハンガー\n{cliffhanger}"
        if recent_drafts:
            parts = []
            for d_date, d_content in recent_drafts:
                truncated = d_content[:800] + ("..." if len(d_content) > 800 else "")
                parts.append(f"=== {d_date} ===\n{truncated}")
            recent_block = "\n\n".join(parts)
        else:
            recent_block = "（前回のドラフトなし）"

    art_style = series.get("art_style", "dynamic shonen manga, clean ink lines, screen tone shading, expressive faces")
    panels_min = series.get("panels_per_page_min", 8)
    panels_max = series.get("panels_per_page_max", 12)

    return f"""# シリーズ情報
タイトル: {series.get("title", "")}
ジャンル: {series.get("genre", "shonen")}
絵柄スタイル: {art_style}

# 現在の章
第{chapter}章「{chapter_title}」

## 章の概要（マスターシナリオより）
{chapter_section or "（章情報なし）"}

{context_block}

# 直近のドラフト（継続性のため）
{recent_block}

# キャラクター情報
{chars_compact}

# 本日のタスク（{target_date}）
第{chapter}章「{chapter_title}」の**{page}ページ目**を執筆してください。
コマ数は{panels_min}〜{panels_max}コマの範囲で自然に決めてください。

以下の4つのXMLタグを必ずこの順番で出力してください。

<DRAFT>
# 第{chapter}章「{chapter_title}」— {page}ページ目

## シーン概要
（状況・舞台・登場人物・感情の説明を1〜2段落）

## パネル構成（Xコマ）

### コマ1
**状況**: （場面の状況・アクション）
**台詞**: キャラ名「セリフ」（なければ省略）
**演出**: （カメラアングル・エフェクト・構図のメモ）

### コマ2
...
（コマ数まで続ける）
</DRAFT>

<PROMPTS>
# Image Prompts — Chapter {chapter}, Page {page}
## Art Style: {art_style}, black and white

## Panel 1
（英語プロンプト。登場キャラのvisual_enから始め、背景・アクション・構図を英語で描写。最後に "manga panel, black and white ink" を付ける）

## Panel 2
...
</PROMPTS>

<ROLLING_SUMMARY>
（これまでのストーリー全体の要約。今日のシーンを含めて200字以内の日本語で更新してください）
</ROLLING_SUMMARY>

<CLIFFHANGER>
（今日の最終コマの状況・引き。明日へのフックを1〜2文の日本語で）
</CLIFFHANGER>
"""


def update_state(state: dict, today: str, rolling_summary: str, cliffhanger: str) -> dict:
    chapter_str = str(state["current_chapter"])
    chapter_info = state["chapter_map"].get(chapter_str, {
        "title": "", "estimated_pages": 5, "pages": [], "status": "in_progress"
    })
    estimated = chapter_info.get("estimated_pages", 5)
    current_page = state["current_page"]

    chapter_info.setdefault("pages", []).append(current_page)
    chapter_info["status"] = "in_progress"
    state["chapter_map"][chapter_str] = chapter_info

    state["total_pages_generated"] += 1
    state["last_generated_date"] = today
    state["story_summary_rolling"] = rolling_summary
    state["recent_cliffhanger"] = cliffhanger

    if current_page >= estimated:
        chapter_info["status"] = "done"
        next_chapter = state["current_chapter"] + 1
        state["current_chapter"] = next_chapter
        state["current_page"] = 1
        next_ch_str = str(next_chapter)
        if next_ch_str not in state["chapter_map"]:
            state["chapter_map"][next_ch_str] = {
                "title": "", "estimated_pages": 5, "pages": [], "status": "in_progress"
            }
        else:
            state["chapter_map"][next_ch_str]["status"] = "in_progress"
        print(f"  第{state['current_chapter'] - 1}章完了 → 次回から第{next_chapter}章へ")
    else:
        state["current_page"] = current_page + 1

    return state


def main():
    parser = argparse.ArgumentParser(description="今日の漫画ドラフトとChatGPT用プロンプトを生成します")
    parser.add_argument("--date", default=date.today().isoformat(), help="日付 (YYYY-MM-DD)")
    parser.add_argument("--model", default="claude-opus-4-8", help="Claude モデル名")
    args = parser.parse_args()

    master_path = MANGA_DIR / "scenario" / "master.md"
    if not master_path.exists():
        print("ERROR: manga/scenario/master.md が見つかりません。先に manga_init.py を実行してください。")
        sys.exit(1)

    state_path = MANGA_DIR / "state.json"
    state = load_json(state_path)
    series = load_json(MANGA_DIR / "config" / "series.json")
    characters = load_json(MANGA_DIR / "scenario" / "characters.json")

    # Idempotency: skip if already generated today
    chapter_dir = MANGA_DIR / "chapters" / args.date
    if (chapter_dir / "draft.md").exists():
        print(f"{args.date} のドラフトは既に存在します。スキップします。")
        sys.exit(0)
    if state.get("last_generated_date") == args.date:
        print(f"本日 ({args.date}) は既に生成済みです。スキップします。")
        sys.exit(0)

    chapter = state["current_chapter"]
    page = state["current_page"]
    print(f"生成中: 第{chapter}章 {page}ページ目 ({args.date}) — {series.get('title', '')}")

    master_text = master_path.read_text(encoding="utf-8")
    chapter_section = extract_chapter_section(master_text, chapter)
    recent_drafts = load_recent_drafts(2)

    client = ClaudeClient(model=args.model)
    try:
        response = client.complete(
            system=SYSTEM_PROMPT,
            user=build_prompt(state, series, characters, chapter_section, recent_drafts, args.date),
            max_tokens=4096,
        )
    except Exception as e:
        print(f"ERROR: Claude API 呼び出し失敗: {e}")
        sys.exit(1)

    try:
        draft_text = extract_tag(response, "DRAFT")
        prompts_text = extract_tag(response, "PROMPTS")
        rolling_summary = extract_tag(response, "ROLLING_SUMMARY")
        cliffhanger = extract_tag(response, "CLIFFHANGER")
    except ValueError as e:
        print(f"ERROR: レスポンスのパースに失敗しました: {e}")
        print("--- Raw response (first 2000 chars) ---")
        print(response[:2000])
        sys.exit(1)

    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "draft.md").write_text(draft_text, encoding="utf-8")
    (chapter_dir / "prompts.md").write_text(prompts_text, encoding="utf-8")
    print(f"  manga/chapters/{args.date}/draft.md")
    print(f"  manga/chapters/{args.date}/prompts.md")

    updated = update_state(state, args.date, rolling_summary, cliffhanger)
    state_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  manga/state.json (更新済み)")

    print(f"\n完了: 第{chapter}章 {page}ページ目")
    print(f"  クリフハンガー: {cliffhanger[:80]}...")
    print(f"  次回: 第{updated['current_chapter']}章 {updated['current_page']}ページ目")
    print(f"\nChatGPT用プロンプト: manga/chapters/{args.date}/prompts.md")


if __name__ == "__main__":
    main()
