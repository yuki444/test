"""Generate original, unique character designs for the manga series via Claude API.

Designed to ensure characters don't resemble existing popular manga characters.
Run standalone, or called from manga_init.py.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"

from claude_client import ClaudeClient


# Characters to explicitly avoid resembling
AVOID_CHARACTERS = """
以下の有名キャラクターとの類似を絶対に避けること：
- ナルト（うずまきナルト）：金髪、頬のひげ印、橙色の服、チャクラ系魔法
- 孫悟空（ドラゴンボール）：黒い尖りまくった髪、道着、気、超変身
- ルフィ（ワンピース）：麦わら帽子、ゴム体質、赤い服
- 黒崎一護（ブリーチ）：オレンジ色の髪、大きな黒い刀
- 緑谷出久（ヒロアカ）：緑のボサボサ髪、そばかす、ヒーロースーツ
- 竈門炭治郎（鬼滅）：炭色の髪に赤い模様、市松模様の服、炎/水の呼吸
- エドワード・エルリック（ハガレン）：金髪ポニーテール、赤いコート、鋼鉄の腕
- 夜神月（デスノート）：黒い目、冷酷な笑み
- セーラームーン型：変身ヒロイン
- ハリー・ポッター型：眼鏡、額の傷、杖
"""

SYSTEM_PROMPT = f"""\
あなたはプロのキャラクターデザイナー兼少年漫画作家です。
完全にオリジナルで、既存漫画キャラクターに似ていないキャラクターを設計します。

## 絶対に避けるべき既存キャラクター
{AVOID_CHARACTERS}

## 独自性のルール
1. シルエットテスト：輪郭だけで誰かわかる独特な外形
2. カラーパレット：既存の有名キャラクターと被らない色の組み合わせ
3. 能力/技：世界観から自然に導かれるオリジナルの力
4. 服装：世界観に根ざした独自のデザイン（学校の制服ではない）
5. 顔の特徴：特定のトレードマーク（既存作品のコピーでない）

## 出力形式
指定されたJSONフォーマットを厳守し、すべてのフィールドを埋めること。
visual_en は画像生成AI（DALL-E 3）に渡すため、英語で30語以内の具体的な描写。
"""


def build_prompt(series_info: dict, existing_chars: dict, char_role: str, char_hints: str) -> str:
    existing_names = list(existing_chars.keys()) if existing_chars else []
    series_title = series_info.get("title", "少年漫画シリーズ")
    series_concept = series_info.get("concept", "魔法学院×火の呪い")

    return f"""シリーズ「{series_title}」のキャラクターを設計してください。

## シリーズ設定
コンセプト: {series_concept}
世界観: 詠唱魔法が支配する社会。生まれながらの「火の呪い」は禁忌とされている。

## 依頼
役割: {char_role}
ヒント・方向性: {char_hints}
{f"既存キャラクター（との差別化が必要）: {', '.join(existing_names)}" if existing_names else ""}

以下のJSONを出力してください：

{{
  "name_jp": "キャラクター名（日本語・カタカナや和名）",
  "name_reading": "よみがな",
  "role": "{char_role}",
  "age": 年齢（整数）,
  "visual_en": "英語外見描写（30語以内）。髪型・色、目の色・形、体格、服装の核心を含む。既存キャラと被らない描写",
  "hair": "髪の詳細（色・スタイル・長さ・特徴）",
  "eyes": "目の詳細（色・形・表情の傾向）",
  "height_build": "身長・体格",
  "signature_item": "このキャラだけの特徴的アイテムや外見マーク",
  "outfit_description": "服装の詳細（世界観に合ったオリジナルデザイン）",
  "personality_jp": "性格・口調・癖（日本語、150字以内）",
  "background_jp": "バックグラウンド（日本語、200字以内）",
  "ability_jp": "能力・強さ（日本語）",
  "ability_unique_point": "なぜ既存作品の能力と違うか（日本語）",
  "first_appearance": 初登場章番号（整数）,
  "originality_check": "どの点が既存の有名キャラと異なるか（日本語、箇条書き3点）"
}}
"""


def validate_character(char: dict) -> list[str]:
    """Check for obvious plagiarism red flags."""
    warnings = []
    visual = (char.get("visual_en", "") + char.get("hair", "")).lower()
    name = char.get("name_jp", "")

    red_flags = [
        ("spiky black hair", "スパイキー黒髪（悟空・ナルト系）"),
        ("blonde spiky", "金色スパイキー（ナルト・悟空系）"),
        ("orange outfit", "橙色の服（ナルト系）"),
        ("red coat", "赤いコート（エドワード系）"),
        ("straw hat", "麦わら帽子（ルフィ系）"),
        ("orange hair", "オレンジ髪（一護系）"),
        ("checkered", "市松模様（炭治郎系）"),
    ]
    for flag, desc in red_flags:
        if flag in visual:
            warnings.append(f"注意: {desc} が検出されました")

    return warnings


def save_character_sheet(char: dict, output_dir: Path) -> Path:
    name = char.get("name_jp", "unknown").replace(" ", "_")
    sheet_path = output_dir / f"{name}.md"

    content = f"""# {char['name_jp']}（{char.get('name_reading', '')}）

## 基本情報
- **役割**: {char['role']}
- **年齢**: {char.get('age', '不明')}歳
- **初登場**: 第{char.get('first_appearance', 1)}章

## 外見
- **髪**: {char.get('hair', '')}
- **目**: {char.get('eyes', '')}
- **体格**: {char.get('height_build', '')}
- **特徴的アイテム**: {char.get('signature_item', '')}
- **服装**: {char.get('outfit_description', '')}

## 画像生成プロンプト（英語）
```
{char.get('visual_en', '')}
```

## 性格
{char.get('personality_jp', '')}

## バックグラウンド
{char.get('background_jp', '')}

## 能力
{char.get('ability_jp', '')}

**独自性**: {char.get('ability_unique_point', '')}

## 独自性チェック
{char.get('originality_check', '')}
"""
    sheet_path.write_text(content, encoding="utf-8")
    return sheet_path


def main():
    parser = argparse.ArgumentParser(description="オリジナルキャラクターを設計します")
    parser.add_argument("--role", required=True,
                        choices=["protagonist", "rival", "mentor", "antagonist", "support"],
                        help="キャラクターの役割")
    parser.add_argument("--hints", default="", help="デザインの方向性ヒント（任意）")
    parser.add_argument("--model", default="claude-opus-4-8", help="Claude モデル名")
    parser.add_argument("--add-to-scenario", action="store_true",
                        help="生成後に characters.json へ追加する")
    args = parser.parse_args()

    series_path = MANGA_DIR / "config" / "series.json"
    chars_path = MANGA_DIR / "scenario" / "characters.json"

    series_info = json.loads(series_path.read_text(encoding="utf-8")) if series_path.exists() else {}
    existing_chars = json.loads(chars_path.read_text(encoding="utf-8")) if chars_path.exists() else {}

    print(f"キャラクター設計中（役割: {args.role}）...")
    client = ClaudeClient(model=args.model)

    try:
        response = client.complete(
            system=SYSTEM_PROMPT,
            user=build_prompt(series_info, existing_chars, args.role, args.hints),
            max_tokens=2048,
        )
    except Exception as e:
        print(f"ERROR: Claude API 呼び出し失敗: {e}")
        sys.exit(1)

    # Extract JSON from response
    json_match = re.search(r'\{[\s\S]+\}', response)
    if not json_match:
        print("ERROR: JSONが見つかりませんでした")
        print(response[:1000])
        sys.exit(1)

    try:
        char = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print(f"ERROR: JSONパース失敗: {e}")
        print(json_match.group(0)[:500])
        sys.exit(1)

    # Validate originality
    warnings = validate_character(char)
    for w in warnings:
        print(f"  ⚠ {w}")

    # Save character sheet
    sheets_dir = MANGA_DIR / "scenario" / "character_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = save_character_sheet(char, sheets_dir)
    print(f"  キャラクターシート: {sheet_path.relative_to(REPO_ROOT)}")

    # Optionally add to characters.json
    if args.add_to_scenario:
        name = char["name_jp"]
        existing_chars[name] = {
            "role": char["role"],
            "visual_en": char["visual_en"],
            "personality_jp": char["personality_jp"],
            "first_appearance": char.get("first_appearance", 1),
        }
        chars_path.write_text(
            json.dumps(existing_chars, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  characters.json に追加: {name}")

    print(f"\n=== {char.get('name_jp', '')} ===")
    print(f"外見（EN）: {char.get('visual_en', '')}")
    print(f"性格: {char.get('personality_jp', '')[:80]}...")
    print(f"独自性: {char.get('originality_check', '')[:100]}...")


if __name__ == "__main__":
    main()
