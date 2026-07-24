# coding: utf-8
"""
AI加工テンプレート デモ（お試し版）

「テンプレート」＝ config/ai_templates.json に書かれた
  - プロンプトの装飾（プロンプトサフィックス）
  - ショット構成（何枚・どんな内容の画像を撮るか）
を読み込み、Pollinations（無料・無登録の画像生成API）で画像を作り、
ffmpeg（ローカルインストール済み・無料）でKen Burns風の動画に仕上げる。

課金なし・API登録なし。必要なのは ffmpeg と Pillow のみ（どちらもこのリポジトリで使用中）。

使い方:
  python scripts/ai_template_demo.py --template anime --subject "夜の街を歩く猫"
  python scripts/ai_template_demo.py --list
"""

import argparse
import json
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import subprocess

VIDEO_W, VIDEO_H = 1280, 720
FPS = 25
SHOT_DURATION = 3.0
CROSSFADE_SEC = 1.0
ZOOM_AMOUNT = 0.12

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_PATH = REPO_ROOT / "config" / "ai_templates.json"
OUT_DIR = REPO_ROOT / "output" / "ai_template_demo"

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "C:\\Windows\\Fonts\\meiryo.ttc",
    "C:\\Windows\\Fonts\\YuGothM.ttc",
    "C:\\Windows\\Fonts\\msgothic.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def find_font(size):
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_templates():
    return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))


def download_image(prompt, out_path, seed, timeout=90):
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={VIDEO_W}&height={VIDEO_H}&nologo=true&seed={seed}&enhance=true"
    )
    print(f"  [{seed}] generating: {prompt[:70]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    if len(data) < 1000:
        raise ValueError("image too small / generation failed")
    out_path.write_bytes(data)


def add_title_overlay(img_path, title, template_label, out_path):
    base = Image.open(str(img_path)).convert("RGB").resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, VIDEO_H - 140), (VIDEO_W, VIDEO_H)], fill=(0, 0, 0, 140))

    font_title = find_font(44)
    font_sub = find_font(24)
    draw.text((42, VIDEO_H - 120), title, font=font_title, fill=(255, 255, 255, 255))
    draw.text((44, VIDEO_H - 60), f"Template: {template_label}", font=font_sub, fill=(230, 210, 120, 255))

    result = Image.alpha_composite(base.convert("RGBA"), overlay)
    result.convert("RGB").save(str(out_path), "JPEG", quality=93)


def build_video(images, out_path):
    n = len(images)
    inputs = []
    for img in images:
        inputs += ["-loop", "1", "-i", str(img)]

    filter_parts = []
    dur_frames = int(SHOT_DURATION * FPS)
    for i in range(n):
        zoom_end = 1.0 + ZOOM_AMOUNT
        z_expr = (
            f"min({zoom_end:.3f},1.0+{ZOOM_AMOUNT:.3f}*on/{dur_frames})"
            if i % 2 == 0 else
            f"max(1.0,{zoom_end:.3f}-{ZOOM_AMOUNT:.3f}*on/{dur_frames})"
        )
        filter_parts.append(
            f"[{i}:v]scale={VIDEO_W*2}:{VIDEO_H*2}:flags=bicubic,"
            f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={dur_frames}:fps={FPS}:s={VIDEO_W}x{VIDEO_H},setsar=1[v{i}]"
        )

    if n == 1:
        last = "v0"
    else:
        offset = SHOT_DURATION - CROSSFADE_SEC
        filter_parts.append(f"[v0][v1]xfade=transition=fade:duration={CROSSFADE_SEC}:offset={offset:.2f}[xf1]")
        for i in range(2, n):
            offset += SHOT_DURATION - CROSSFADE_SEC
            filter_parts.append(f"[xf{i-1}][v{i}]xfade=transition=fade:duration={CROSSFADE_SEC}:offset={offset:.2f}[xf{i}]")
        last = f"xf{n-1}"

    # xfadeで結合した合計尺（各クロスフェード分だけ短くなる）
    total_dur = SHOT_DURATION * n - CROSSFADE_SEC * (n - 1)

    filter_complex = "; ".join(filter_parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{last}]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        # NOTE: zoompan -> xfade はこのffmpegバージョンでEOFが伝播せず、
        # -t を付けないとxfadeが最終フレームを無限に出力し続けて終わらない。
        "-t", f"{total_dur:.2f}",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        print("ffmpeg error: timed out after 180s (encoding stalled)")
        return False
    if result.returncode != 0:
        print("ffmpeg error:", result.stderr[-2000:])
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", help="テンプレート名 (config/ai_templates.json 参照)")
    parser.add_argument("--subject", help="動画の題材 (例: '夜の街を歩く猫')")
    parser.add_argument("--list", action="store_true", help="利用可能なテンプレート一覧を表示")
    args = parser.parse_args()

    templates = load_templates()

    if args.list or not args.template:
        print("利用可能なテンプレート:")
        for t in templates:
            print(f"  {t['name']:12s} - {t['label']}")
        if not args.template:
            return

    tpl = next((t for t in templates if t["name"] == args.template), None)
    if tpl is None:
        print(f"ERROR: unknown template '{args.template}'")
        sys.exit(1)

    subject = args.subject or "静かな風景"
    print(f"\n=== AI加工テンプレート デモ: {tpl['label']} / subject='{subject}' ===\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        overlay_images = []

        for i, shot in enumerate(tpl["shots"]):
            prompt = f"{subject}, {shot}, {tpl['prompt_suffix']}, no text, no watermark, high quality"
            raw = tmp / f"raw_{i}.jpg"
            try:
                download_image(prompt, raw, seed=i * 11 + 5)
            except Exception as e:
                print(f"\nERROR: 画像生成に失敗しました ({e})")
                print("  image.pollinations.ai への接続を確認してください"
                      "（社内プロキシ/ファイアウォールでブロックされていないか等）。")
                sys.exit(1)

            overlay = tmp / f"shot_{i}.jpg"
            title = subject if i == 0 else ""
            if title:
                add_title_overlay(raw, title, tpl["label"], overlay)
            else:
                overlay = raw
            overlay_images.append(overlay)

        out_path = OUT_DIR / f"{tpl['name']}_{subject[:10].replace(' ', '_')}.mp4"
        print(f"\n  encoding video ({len(overlay_images)} shots)...")
        ok = build_video(overlay_images, out_path)

        if ok:
            size_kb = out_path.stat().st_size // 1024
            print(f"\n=== done: {out_path} ({size_kb} KB) ===")
        else:
            print("\n=== failed ===")
            sys.exit(1)


if __name__ == "__main__":
    main()
