"""One-time setup: generate master scenario for a shonen manga series via Claude API."""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"

from claude_client import ClaudeClient


SYSTEM_PROMPT = """\
あなたはプロの少年漫画作家・シナリオライターです。長期連載漫画のシリーズ聖典を作成します。
以下の制約を厳守してください：
- タイトル・世界観・章概要・セリフは日本語で書く
- キャラクターのvisual_en（外見説明）はDALL-E等の画像生成AIに渡すプロンプト用のため、英語30語以内で具体的に書く
- 少年漫画らしいテーマ（友情・努力・成長・勝利）を軸に置く
- 4つのXMLタグを正確な形式で出力する

## キャラクター独自性の鉄則
以下の有名漫画キャラクターに似せることを絶対に禁止する：
- ナルト系：金/黒スパイキー髪・頬印・橙服・チャクラ
- ドラゴンボール系：尖りすぎた黒髪・道着・気・超変身
- ワンピース系：麦わら帽子・ゴム体質・赤い服
- ブリーチ系：オレンジ髪・大型斬魄刀
- ヒロアカ系：緑ボサボサ髪・そばかす・ヒーロースーツ
- 鬼滅系：市松模様・炎/水の呼吸・特定の目の形
- ハガレン系：金髪ポニー・赤コート・鋼の義肢
各キャラクターは「シルエットテスト」に合格すること（輪郭だけで識別可能な独自の外形）。
"""


def build_prompt(genre: str, concept: str) -> str:
    return f"""以下のコンセプトをもとに、少年漫画シリーズの完全な聖典を作成してください。

ジャンル: {genre}
コンセプト: {concept}

以下の4つのXMLタグをこの順序で必ず出力してください。

<SERIES_JSON>
{{
  "title": "シリーズタイトル（日本語）",
  "tagline": "キャッチコピー（日本語、20文字以内）",
  "art_style": "dynamic shonen manga, clean ink lines, screen tone shading, expressive faces",
  "genre": "{genre}",
  "total_chapters": 30,
  "panels_per_page_min": 8,
  "panels_per_page_max": 12
}}
</SERIES_JSON>

<CHARACTERS_JSON>
{{
  "キャラ名（日本語）": {{
    "role": "protagonist",
    "visual_en": "英語での外見描写（30語以内、画像生成プロンプト用）",
    "personality_jp": "性格・口調（日本語100字以内）",
    "first_appearance": 1
  }}
}}
</CHARACTERS_JSON>
※キャラクターは5〜8名定義してください。roleはprotagonist/rival/mentor/antagonist/supportのいずれか。

<CHAPTERS_JSON>
{{
  "1": {{"title": "章タイトル（日本語）", "estimated_pages": 5}},
  "2": {{"title": "章タイトル（日本語）", "estimated_pages": 6}},
  "3": {{"title": "章タイトル（日本語）", "estimated_pages": 5}},
  ...（30章まで続ける）
}}
</CHAPTERS_JSON>
※全30章のタイトルと推定ページ数（5〜8の範囲）を書いてください。

<MASTER_SCENARIO>
# タイトル

## 世界観
（世界の仕組み・ルール・雰囲気を3〜4段落で説明）

## テーマ
（この漫画が読者に伝えるメッセージ・問いかけ）

## 章構成（全30章）

### 第1章「章タイトル」
**概要**: ストーリーの流れを2〜3文で説明
**感情ビート**: 序幕／試練／葛藤／クライマックス／解決 のいずれか
**登場キャラ**: 名前を列挙
**重要イベント**: この章の核心となる出来事

### 第2章「章タイトル」
...（第30章まで続ける）
</MASTER_SCENARIO>
"""


def extract_tag(text: str, tag: str) -> str:
    match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    if not match:
        raise ValueError(f"タグ <{tag}> が見つかりませんでした")
    return match.group(1).strip()


def parse_json_tag(text: str, tag: str) -> dict:
    content = extract_tag(text, tag)
    content = re.sub(r'^```(?:json)?\n?', '', content).rstrip('`').strip()
    return json.loads(content)


def build_initial_state(chapters: dict) -> dict:
    chapter_map = {}
    for ch_num_str, ch_info in chapters.items():
        chapter_map[ch_num_str] = {
            "title": ch_info.get("title", ""),
            "estimated_pages": ch_info.get("estimated_pages", 5),
            "pages": [],
            "status": "in_progress" if ch_num_str == "1" else "planned",
        }
    return {
        "current_chapter": 1,
        "current_page": 1,
        "total_pages_generated": 0,
        "last_generated_date": None,
        "story_summary_rolling": "",
        "recent_cliffhanger": "",
        "chapter_map": chapter_map,
    }


def main():
    parser = argparse.ArgumentParser(description="少年漫画シリーズの聖典を生成します（初回のみ）")
    parser.add_argument("--genre", default="shonen", help="ジャンル (デフォルト: shonen)")
    parser.add_argument("--concept", required=True, help="ストーリーコンセプト（一文で）")
    parser.add_argument("--model", default="claude-opus-4-8", help="Claude モデル名")
    parser.add_argument("--force", action="store_true", help="既存シナリオを上書き")
    args = parser.parse_args()

    master_path = MANGA_DIR / "scenario" / "master.md"
    if master_path.exists() and not args.force:
        print(f"ERROR: {master_path} は既に存在します。上書きするには --force を使用してください。")
        sys.exit(1)

    print(f"シリーズ聖典を生成中... (モデル: {args.model})")
    client = ClaudeClient(model=args.model)

    try:
        response = client.complete(
            system=SYSTEM_PROMPT,
            user=build_prompt(args.genre, args.concept),
            max_tokens=8192,
        )
    except Exception as e:
        print(f"ERROR: Claude API 呼び出し失敗: {e}")
        sys.exit(1)

    try:
        series = parse_json_tag(response, "SERIES_JSON")
        characters = parse_json_tag(response, "CHARACTERS_JSON")
        chapters = parse_json_tag(response, "CHAPTERS_JSON")
        master_text = extract_tag(response, "MASTER_SCENARIO")
    except (ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: レスポンスのパースに失敗しました: {e}")
        print("--- Raw response (first 3000 chars) ---")
        print(response[:3000])
        sys.exit(1)

    (MANGA_DIR / "config").mkdir(parents=True, exist_ok=True)
    (MANGA_DIR / "scenario").mkdir(parents=True, exist_ok=True)

    series_path = MANGA_DIR / "config" / "series.json"
    series_path.write_text(json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {series_path}")

    chars_path = MANGA_DIR / "scenario" / "characters.json"
    chars_path.write_text(json.dumps(characters, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {chars_path}")

    master_path.write_text(master_text, encoding="utf-8")
    print(f"  {master_path}")

    state = build_initial_state(chapters)
    state_path = MANGA_DIR / "state.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {state_path}")

    total_estimated = sum(v.get("estimated_pages", 5) for v in chapters.values())
    print(f"\n=== 「{series.get('title', '(タイトル未設定)')}」の聖典を生成しました ===")
    print(f"キャラクター数: {len(characters)}名")
    print(f"全30章、合計約{total_estimated}ページを予定")
    print("\n次のステップ:")
    print("  1. manga/scenario/master.md を確認・編集してください")
    print("  2. git add manga/ && git commit -m 'feat: add manga scenario'")
    print("  3. 翌朝から: python scripts/manga_draft.py")


if __name__ == "__main__":
    main()
