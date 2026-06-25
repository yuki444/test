"""Generate manga panel images via OpenAI image generation API (DALL-E 3 / gpt-image-1)."""
import argparse
import base64
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANGA_DIR = REPO_ROOT / "manga"

try:
    import openai
except ImportError:
    print("ERROR: openai パッケージがインストールされていません。pip install openai を実行してください。")
    sys.exit(1)


def parse_panels(prompts_md: str) -> list[tuple[int, str]]:
    """Extract (panel_num, prompt_text) pairs from prompts.md."""
    panels = []
    # Match ## Panel N or ## パネル N blocks
    pattern = r'## (?:Panel|パネル)\s+(\d+)\s*\n(.*?)(?=\n## (?:Panel|パネル)\s+\d+|\Z)'
    for match in re.finditer(pattern, prompts_md, re.DOTALL):
        num = int(match.group(1))
        prompt = match.group(2).strip()
        if prompt:
            panels.append((num, prompt))
    return panels


def generate_image(client: openai.OpenAI, prompt: str, model: str, size: str) -> bytes:
    """Call OpenAI image API and return raw PNG bytes."""
    if model == "gpt-image-1":
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
        )
        b64 = response.data[0].b64_json
    else:
        # dall-e-3 supports response_format
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json",
        )
        b64 = response.data[0].b64_json

    if b64 is None:
        raise RuntimeError(f"APIからb64_jsonが返りませんでした: {response}")
    return base64.b64decode(b64)


def main():
    parser = argparse.ArgumentParser(description="漫画コマ画像をOpenAI APIで自動生成します")
    parser.add_argument("--date", default=date.today().isoformat(), help="日付 (YYYY-MM-DD)")
    parser.add_argument("--model", default="dall-e-3",
                        choices=["dall-e-3", "gpt-image-1"],
                        help="画像生成モデル (デフォルト: dall-e-3)")
    parser.add_argument("--size", default="1024x1024",
                        choices=["1024x1024", "1792x1024", "1024x1792"],
                        help="画像サイズ (デフォルト: 1024x1024)")
    parser.add_argument("--panels", nargs="+", type=int, metavar="N",
                        help="生成するコマ番号を指定 (省略=全コマ)")
    args = parser.parse_args()

    prompts_path = MANGA_DIR / "chapters" / args.date / "prompts.md"
    if not prompts_path.exists():
        print(f"ERROR: {prompts_path} が見つかりません。先に manga_draft.py を実行してください。")
        sys.exit(1)

    prompts_md = prompts_path.read_text(encoding="utf-8")
    panels = parse_panels(prompts_md)
    if not panels:
        print(f"ERROR: {prompts_path} からコマプロンプトが見つかりませんでした。")
        sys.exit(1)

    if args.panels:
        panels = [(n, p) for n, p in panels if n in args.panels]

    output_dir = MANGA_DIR / "chapters" / args.date / "panels"
    output_dir.mkdir(parents=True, exist_ok=True)

    client = openai.OpenAI()  # OPENAI_API_KEY from env
    results = []
    errors = []

    print(f"コマ画像を生成中: {args.date} / {len(panels)}コマ (モデル: {args.model})")

    for panel_num, prompt in panels:
        image_path = output_dir / f"panel_{panel_num:02d}.png"

        if image_path.exists():
            print(f"  コマ{panel_num}: スキップ（既存）")
            results.append({"panel": panel_num, "path": str(image_path.relative_to(REPO_ROOT))})
            continue

        print(f"  コマ{panel_num}: 生成中...")
        print(f"    プロンプト: {prompt[:80]}...")
        try:
            img_bytes = generate_image(client, prompt, args.model, args.size)
            image_path.write_bytes(img_bytes)
            print(f"    → {image_path.relative_to(REPO_ROOT)}")
            results.append({"panel": panel_num, "path": str(image_path.relative_to(REPO_ROOT))})
        except Exception as e:
            print(f"    ERROR: {e}")
            errors.append({"panel": panel_num, "error": str(e)})

    images_json = MANGA_DIR / "chapters" / args.date / "images.json"
    images_json.write_text(
        json.dumps({"date": args.date, "model": args.model, "panels": results, "errors": errors},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n完了: {len(results)}枚生成, {len(errors)}エラー")
    print(f"メタデータ: {images_json.relative_to(REPO_ROOT)}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
