# coding: utf-8
"""
AI Template Demo — テンプレート + 被写体からPollinations AIで
印刷商品モックアップ画像を生成するデモスクリプト。

使い方:
  python scripts/ai_template_demo.py --template printer_clone --subject "fluffy white cat"
  python scripts/ai_template_demo.py --list
"""

import argparse
import re
import sys
import urllib.parse
import urllib.request
import zlib
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_FILE = REPO_ROOT / "config" / "templates.json"
OUTPUT_DIR = REPO_ROOT / "output" / "ai_template_demo"


def load_templates() -> list[dict]:
    import json
    return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))


def get_template(name: str) -> dict | None:
    return next((t for t in load_templates() if t["name"] == name), None)


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "subject"


def download_image(prompt: str, out_path: Path, width: int, height: int,
                    seed: int, timeout: int = 90) -> bool:
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"
    )
    print(f"  prompt: {prompt[:100]}...")
    print(f"  requesting image (seed={seed}, {width}x{height})...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if len(data) < 1000:
            raise ValueError("response too small, likely an error page")
        out_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"  image generation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", help="config/templates.json 内のテンプレート名")
    parser.add_argument("--subject", help="生成したい被写体の説明文")
    parser.add_argument("--seed", type=int, default=None,
                         help="固定シード（未指定なら subject から自動生成）")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--list", action="store_true", help="利用可能なテンプレート一覧を表示")
    args = parser.parse_args()

    if args.list:
        print("Available templates:")
        for t in load_templates():
            print(f"  {t['name']:<20} {t.get('label', '')}")
        return

    if not args.template or not args.subject:
        parser.error("--template and --subject are required (or use --list)")

    template = get_template(args.template)
    if template is None:
        names = ", ".join(t["name"] for t in load_templates())
        print(f"ERROR: unknown template '{args.template}'. Available: {names}")
        sys.exit(1)

    prompt = template["prompt_template"].format(subject=args.subject)
    width = template.get("width", 1024)
    height = template.get("height", 1024)
    seed = args.seed if args.seed is not None else (zlib.crc32(args.subject.encode("utf-8")) % 100000)

    out_dir = Path(args.output_dir) / args.template
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{slugify(args.subject)}-{timestamp}.jpg"

    print(f"\n=== AI Template Demo: {template.get('label', args.template)} ===")
    print(f"  subject: {args.subject}")

    if download_image(prompt, out_path, width, height, seed):
        print(f"\ndone: {out_path}")
    else:
        print("\nERROR: image generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
