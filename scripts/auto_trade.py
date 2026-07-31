"""前日のポートフォリオを引き継ぎ、売却ルール評価とTOP10均等配分の仮想買付を行う。

使い方:
    python scripts/auto_trade.py
    python scripts/auto_trade.py --date 2026-07-30
"""
import argparse
import glob
import json
import os
import sys
import uuid
from datetime import datetime

INITIAL_CASH = 5_000_000
MAX_POSITIONS = 10
TRADE_RULES_PATH = os.path.join("config", "trade_rules.json")


def parse_args():
    parser = argparse.ArgumentParser(description="仮想売買実行")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    return parser.parse_args()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_previous_portfolio(today: str):
    candidates = sorted(glob.glob(os.path.join("data", "*", "portfolio.json")))
    candidates = [c for c in candidates if os.path.basename(os.path.dirname(c)) < today]
    if not candidates:
        return None
    return load_json(candidates[-1], None)


def init_portfolio():
    return {"cash": INITIAL_CASH, "positions": []}


def evaluate_sell(position: dict, current_price: float, today: str, rules: dict):
    buy_price = position["buyPrice"]
    peak_price = max(position.get("peakPrice", buy_price), current_price)
    position["peakPrice"] = peak_price
    position["currentPrice"] = current_price

    change_pct = (current_price - buy_price) / buy_price * 100 if buy_price else 0
    days_held = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(position["buyDate"], "%Y-%m-%d")).days

    stop_loss_pct = position["sellRules"].get("stopLoss", rules.get("stop_loss_pct"))
    take_profit_pct = position["sellRules"].get("takeProfit", rules.get("take_profit_pct"))
    trailing_stop_pct = position["sellRules"].get("trailingStop", rules.get("trailing_stop_pct"))
    days_to_hold = position["sellRules"].get("daysToHold", rules.get("days_to_hold"))

    if stop_loss_pct is not None and change_pct <= -stop_loss_pct:
        return f"損切りルール発動: 取得価格比 {change_pct:.1f}%（設定 -{stop_loss_pct}%）"

    if take_profit_pct is not None and change_pct >= take_profit_pct:
        return f"利確ルール発動: 取得価格比 +{change_pct:.1f}%（設定 +{take_profit_pct}%）"

    if trailing_stop_pct is not None:
        drop_from_peak = (peak_price - current_price) / peak_price * 100 if peak_price else 0
        if drop_from_peak >= trailing_stop_pct:
            return f"トレーリングストップ発動: 高値 {peak_price:.0f}円から {drop_from_peak:.1f}%下落（設定 {trailing_stop_pct}%）"

    if days_to_hold is not None and days_held >= days_to_hold:
        return f"保有期間満了: {days_held}日保有（設定 {days_to_hold}日）"

    return None


def main():
    args = parse_args()
    today = args.date

    scores_data = load_json(os.path.join("data", today, "scores.json"), None)
    if scores_data is None:
        print(f"エラー: data/{today}/scores.json が見つかりません。先に score_stocks.py を実行してください", file=sys.stderr)
        sys.exit(1)

    price_by_code = {s["code"]: s["currentPrice"] for s in scores_data["scores"]}
    name_by_code = {s["code"]: s["name"] for s in scores_data["scores"]}

    portfolio = find_previous_portfolio(today) or init_portfolio()
    trade_rules = load_json(TRADE_RULES_PATH, {"stop_loss_pct": 8, "take_profit_pct": 25, "trailing_stop_pct": None, "days_to_hold": 30})

    trades = []

    # 1. 既存ポジションの売却ルール評価
    remaining_positions = []
    for position in portfolio["positions"]:
        current_price = price_by_code.get(position["code"], position["currentPrice"])
        reason = evaluate_sell(position, current_price, today, trade_rules)

        if reason:
            proceeds = position["shares"] * current_price
            cost = position["shares"] * position["buyPrice"]
            pnl = proceeds - cost
            pnl_pct = (pnl / cost * 100) if cost else 0
            portfolio["cash"] += proceeds
            trades.append({
                "id": str(uuid.uuid4()),
                "code": position["code"],
                "name": position["name"],
                "type": "sell",
                "shares": position["shares"],
                "price": current_price,
                "date": today,
                "reason": reason,
                "pnl": round(pnl, 0),
                "pnlPct": round(pnl_pct, 2),
            })
        else:
            remaining_positions.append(position)

    portfolio["positions"] = remaining_positions

    # 2. TOP10のうち未保有銘柄を均等配分で買付
    held_codes = {p["code"] for p in portfolio["positions"]}
    top10 = scores_data["scores"][:10]
    new_candidates = [s for s in top10 if s["code"] not in held_codes]

    open_slots = MAX_POSITIONS - len(portfolio["positions"])
    to_buy = new_candidates[:max(open_slots, 0)]

    if to_buy and portfolio["cash"] > 0:
        allocation = portfolio["cash"] / len(to_buy)
        for s in to_buy:
            price = s["currentPrice"]
            if price <= 0:
                continue
            shares = int(allocation // price)
            if shares <= 0:
                continue
            cost = shares * price
            portfolio["cash"] -= cost
            portfolio["positions"].append({
                "id": str(uuid.uuid4()),
                "code": s["code"],
                "name": s["name"],
                "shares": shares,
                "buyPrice": price,
                "buyDate": today,
                "currentPrice": price,
                "peakPrice": price,
                "sellRules": {
                    "stopLoss": trade_rules.get("stop_loss_pct"),
                    "takeProfit": trade_rules.get("take_profit_pct"),
                    "trailingStop": trade_rules.get("trailing_stop_pct"),
                    "daysToHold": trade_rules.get("days_to_hold"),
                },
            })
            trades.append({
                "id": str(uuid.uuid4()),
                "code": s["code"],
                "name": s["name"],
                "type": "buy",
                "shares": shares,
                "price": price,
                "date": today,
                "reason": f"スコア{s['totalScore']:.1f}pt でTOP10入り、均等配分{allocation:,.0f}円枠で買付",
                "pnl": None,
                "pnlPct": None,
            })

    # 3. 既存保有銘柄の評価額を最新化（今日買っていない銘柄）
    for position in portfolio["positions"]:
        if position["code"] in price_by_code:
            position["currentPrice"] = price_by_code[position["code"]]
            position["peakPrice"] = max(position.get("peakPrice", position["currentPrice"]), position["currentPrice"])
        position.setdefault("name", name_by_code.get(position["code"], position["code"]))

    total_position_value = sum(p["shares"] * p["currentPrice"] for p in portfolio["positions"])
    portfolio["date"] = today
    portfolio["totalValue"] = round(portfolio["cash"] + total_position_value, 0)

    out_dir = os.path.join("data", today)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "portfolio.json"), "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "trades.json"), "w", encoding="utf-8") as f:
        json.dump(trades, f, ensure_ascii=False, indent=2)

    print(f"完了: 保有 {len(portfolio['positions'])}銘柄, 現金 {portfolio['cash']:,.0f}円, 総資産 {portfolio['totalValue']:,.0f}円")
    print(f"本日の売買: {len(trades)}件")
    for t in trades:
        print(f"  {t['type']} {t['code']} {t['name']} {t['shares']}株 @{t['price']:.0f}円 - {t['reason']}")


if __name__ == "__main__":
    main()
