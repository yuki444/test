"""fetch_data.py の出力を読み込み、全銘柄をスコアリングする。

使い方:
    python scripts/score_stocks.py
    python scripts/score_stocks.py --date 2026-07-30
"""
import argparse
import json
import os
import sys
from datetime import datetime

from scoring import calculate_stock_score
from universe import STOCK_UNIVERSE

WEIGHTS_PATH = os.path.join("config", "scoring_weights.json")


def parse_args():
    parser = argparse.ArgumentParser(description="銘柄スコアリング")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    return parser.parse_args()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    args = parse_args()
    raw_dir = os.path.join("data", args.date, "raw")
    if not os.path.isdir(raw_dir):
        print(f"エラー: {raw_dir} が見つかりません。先に fetch_data.py を実行してください", file=sys.stderr)
        sys.exit(1)

    weights = load_json(WEIGHTS_PATH, {"technical": 1.0, "fundamental": 1.0, "momentum": 1.0, "news": 1.0})

    scores = []
    for stock in STOCK_UNIVERSE:
        code = stock["code"]
        quotes = load_json(os.path.join(raw_dir, f"{code}_quotes.json"), [])
        statements = load_json(os.path.join(raw_dir, f"{code}_statements.json"), [])

        score = calculate_stock_score({"code": code, "name": stock["name"]}, quotes, statements, weights)
        scores.append(score)

    scores.sort(key=lambda s: s["totalScore"], reverse=True)

    out_path = os.path.join("data", args.date, "scores.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "date": args.date,
                "generatedAt": datetime.now().isoformat(),
                "weights": weights,
                "scores": scores,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"完了: {len(scores)}銘柄をスコアリングし {out_path} に保存しました")
    print("TOP10:")
    for s in scores[:10]:
        print(f"  {s['code']} {s['name']}: {s['totalScore']:.1f}pt")


if __name__ == "__main__":
    main()
