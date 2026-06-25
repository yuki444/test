"""Prepare Canva manga page creation data from today's draft and prompts.

This script reads manga/chapters/YYYY-MM-DD/draft.md and prompts.md,
then outputs structured data that Claude Code uses with the Canva MCP tools
to create and export a manga page design.

Run via Claude Code (not standalone) — the actual Canva API calls happen
through the MCP tools available in the Claude Code session.

Usage:
    python scripts/manga_canva.py [--date YYYY-MM-DD] [--output json|prompt]
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"


def parse_panels_from_draft(draft_text: str) -> list[dict]:
    """Parse panel info from draft.md — situation, dialogue, staging."""
    panels = []
    pattern = r'### コマ(\d+)\s*\n(.*?)(?=### コマ\d+|\Z)'
    for match in re.finditer(pattern, draft_text, re.DOTALL):
        num = int(match.group(1))
        block = match.group(2).strip()

        situation = re.search(r'\*\*状況\*\*[:：]\s*(.+)', block)
        dialogue_match = re.search(r'\*\*台詞\*\*[:：]\s*(.+)', block)
        staging = re.search(r'\*\*演出\*\*[:：]\s*(.+)', block)

        panels.append({
            "num": num,
            "situation": situation.group(1).strip() if situation else "",
            "dialogue": dialogue_match.group(1).strip() if dialogue_match else "",
            "staging": staging.group(1).strip() if staging else "",
        })
    return panels


def parse_panels_from_prompts(prompts_text: str) -> list[dict]:
    """Parse English image prompts per panel from prompts.md."""
    panels = []
    pattern = r'## (?:Panel|パネル)\s+(\d+)\s*\n(.*?)(?=\n## (?:Panel|パネル)\s+\d+|\Z)'
    for match in re.finditer(pattern, prompts_text, re.DOTALL):
        num = int(match.group(1))
        prompt = match.group(2).strip()
        panels.append({"num": num, "prompt_en": prompt})
    return panels


def build_canva_query(draft_panels: list[dict], series: dict, chapter: int, page: int) -> str:
    """Build a Canva generate-design query for the manga page."""
    n = len(draft_panels)
    title = series.get("title", "少年漫画")
    art_style = series.get("art_style", "dynamic shonen manga, black and white")

    # Scene summary for the Canva query (first 3 panels give context)
    scene_summary = " | ".join(
        p["situation"][:40] for p in draft_panels[:3] if p["situation"]
    )

    return (
        f"manga comic page layout with {n} panels, black and white ink art, "
        f"shonen manga style, screen tone shading, dynamic action poses, "
        f"chapter {chapter} page {page} of '{title}', "
        f"scene: {scene_summary}"
    )


def build_canva_instructions(
    draft_panels: list[dict],
    prompt_panels: list[dict],
    series: dict,
    state: dict,
    target_date: str,
) -> dict:
    """Build full instructions for the Canva MCP workflow."""
    chapter = state["current_chapter"]
    page = state["current_page"]
    chapter_title = state["chapter_map"].get(str(chapter), {}).get("title", "")

    prompt_map = {p["num"]: p["prompt_en"] for p in prompt_panels}

    panels_combined = []
    for dp in draft_panels:
        panels_combined.append({
            "num": dp["num"],
            "situation_jp": dp["situation"],
            "dialogue_jp": dp["dialogue"],
            "staging_jp": dp["staging"],
            "image_prompt_en": prompt_map.get(dp["num"], ""),
        })

    canva_query = build_canva_query(draft_panels, series, chapter, page)

    return {
        "date": target_date,
        "chapter": chapter,
        "chapter_title": chapter_title,
        "page": page,
        "series_title": series.get("title", ""),
        "art_style": series.get("art_style", ""),
        "panel_count": len(panels_combined),
        "panels": panels_combined,
        "canva_generate_query": canva_query,
        "canva_design_type": "poster",
        "export_format": "png",
        "output_path": f"manga/chapters/{target_date}/page.png",
    }


def print_claude_instructions(instructions: dict) -> None:
    """Print step-by-step instructions for Claude Code to execute with Canva MCP."""
    d = instructions
    print("=" * 60)
    print(f"Canva 漫画ページ作成手順 — {d['date']}")
    print(f"第{d['chapter']}章「{d['chapter_title']}」{d['page']}ページ目")
    print("=" * 60)
    print()
    print("【Step 1】Canva でベースデザインを生成")
    print(f"  design_type: {d['canva_design_type']}")
    print(f"  query: {d['canva_generate_query']}")
    print()
    print("【Step 2】デザイン候補から選択して編集可能デザインを作成")
    print("  → create-design-from-candidate を使用")
    print()
    print("【Step 3】編集トランザクションを開始")
    print("  → start-editing-transaction を使用")
    print()
    print("【Step 4】テキスト要素を各コマのセリフで更新")
    for p in d["panels"]:
        if p["dialogue_jp"]:
            print(f"  コマ{p['num']}: {p['dialogue_jp']}")
    print()
    print("【Step 5】変更をコミット → commit-editing-transaction")
    print()
    print("【Step 6】PNG でエクスポート → export-design")
    print(f"  保存先: {d['output_path']}")
    print()
    print("【各コマの画像プロンプト（参考）】")
    for p in d["panels"][:3]:
        print(f"  コマ{p['num']}: {p['image_prompt_en'][:80]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Canva 漫画ページ作成データを準備します（Claude Code から実行）"
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="日付 (YYYY-MM-DD)")
    parser.add_argument("--output", choices=["json", "prompt"], default="prompt",
                        help="出力形式: json=JSONファイル保存, prompt=手順表示（デフォルト）")
    args = parser.parse_args()

    chapter_dir = MANGA_DIR / "chapters" / args.date
    draft_path = chapter_dir / "draft.md"
    prompts_path = chapter_dir / "prompts.md"

    if not draft_path.exists():
        print(f"ERROR: {draft_path} が見つかりません。先に manga_draft.py を実行してください。")
        raise SystemExit(1)

    state = json.loads((MANGA_DIR / "state.json").read_text(encoding="utf-8"))
    series = json.loads((MANGA_DIR / "config" / "series.json").read_text(encoding="utf-8"))

    draft_panels = parse_panels_from_draft(draft_path.read_text(encoding="utf-8"))
    prompt_panels = (
        parse_panels_from_prompts(prompts_path.read_text(encoding="utf-8"))
        if prompts_path.exists() else []
    )

    if not draft_panels:
        print("ERROR: draft.md からコマ情報を読み取れませんでした。")
        raise SystemExit(1)

    instructions = build_canva_instructions(
        draft_panels, prompt_panels, series, state, args.date
    )

    if args.output == "json":
        out_path = chapter_dir / "canva_instructions.json"
        out_path.write_text(
            json.dumps(instructions, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"保存: {out_path.relative_to(REPO_ROOT)}")
    else:
        print_claude_instructions(instructions)


if __name__ == "__main__":
    main()
