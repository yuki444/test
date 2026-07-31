"""Yahoo Financeから対象30銘柄の日次株価・財務情報を取得する（認証不要）。

使い方:
    python scripts/fetch_data.py                    # 今日の日付で全銘柄取得
    python scripts/fetch_data.py --date 2026-07-30   # 日付指定
"""
import argparse
import json
import os
import time
from datetime import datetime, timedelta

from universe import STOCK_UNIVERSE
from yahoo_client import get_daily_quotes, get_financial_info

QUOTES_DAYS_BACK = 90
REQUEST_INTERVAL_SEC = 0.5


def parse_args():
    parser = argparse.ArgumentParser(description="Yahoo Finance株価・財務データ取得")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    return parser.parse_args()


def main():
    args = parse_args()

    out_dir = os.path.join("data", args.date, "raw")
    os.makedirs(out_dir, exist_ok=True)

    date_to = datetime.strptime(args.date, "%Y-%m-%d")
    date_from = date_to - timedelta(days=QUOTES_DAYS_BACK)

    for stock in STOCK_UNIVERSE:
        code = stock["code"]
        print(f"取得中: {code} {stock['name']}")

        quotes = get_daily_quotes(code, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
        with open(os.path.join(out_dir, f"{code}_quotes.json"), "w", encoding="utf-8") as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)

        statements = get_financial_info(code)
        with open(os.path.join(out_dir, f"{code}_statements.json"), "w", encoding="utf-8") as f:
            json.dump(statements, f, ensure_ascii=False, indent=2)

        time.sleep(REQUEST_INTERVAL_SEC)  # Yahoo Finance側への配慮（非公式API）

    print(f"完了: {len(STOCK_UNIVERSE)}銘柄のデータを {out_dir} に保存しました")


if __name__ == "__main__":
    main()
