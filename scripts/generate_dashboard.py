"""data/ 配下の全JSONを読み込み、docs/index.html と reports/YYYY-MM-DD_dashboard.html を生成する。

使い方:
    python scripts/generate_dashboard.py
    python scripts/generate_dashboard.py --date 2026-07-30
"""
import argparse
import glob
import json
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

INITIAL_CASH = 5_000_000
MAX_SCORE = 90 + 75 + 45 + 45
TEMPLATE_DIR = os.path.join("scripts", "templates")


def parse_args():
    parser = argparse.ArgumentParser(description="ダッシュボード生成")
    parser.add_argument("--date", default=None, help="指定なしなら data/ 内の最新日付を使用")
    return parser.parse_args()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def all_data_dates():
    return sorted(
        d for d in os.listdir("data")
        if os.path.isdir(os.path.join("data", d)) and len(d) == 10
    ) if os.path.isdir("data") else []


def build_chart_svg(history: list) -> str:
    width, height, pad = 900, 220, 40
    if not history:
        return '<div class="empty">資産推移データがまだありません</div>'

    values = [h["totalValue"] for h in history]
    vmin, vmax = min(values), max(values)
    if vmin == vmax:
        vmin -= 1
        vmax += 1

    n = len(history)
    plot_w = width - pad * 2
    plot_h = height - pad * 2

    def x_at(i):
        return pad + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)

    def y_at(v):
        return pad + plot_h - (v - vmin) / (vmax - vmin) * plot_h

    points = [(x_at(i), y_at(h["totalValue"])) for i, h in enumerate(history)]
    polyline_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    area_pts = f"{points[0][0]:.1f},{height - pad} " + polyline_pts + f" {points[-1][0]:.1f},{height - pad}"

    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#4f8cff" />'
        for x, y in points
    )
    labels = "".join(
        f'<text x="{x_at(i):.1f}" y="{height - 10}" font-size="11" fill="#8b93a7" text-anchor="middle">{h["date"][5:]}</text>'
        for i, h in enumerate(history)
    )
    value_labels = "".join(
        f'<text x="{x:.1f}" y="{y - 10:.1f}" font-size="11" fill="#e6e8ee" text-anchor="middle">{h["totalValue"]:,.0f}</text>'
        for (x, y), h in zip(points, history)
    )

    return f'''<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="資産推移チャート">
  <polygon points="{area_pts}" fill="#4f8cff" opacity="0.12" />
  <polyline points="{polyline_pts}" fill="none" stroke="#4f8cff" stroke-width="2.5" />
  {circles}
  {labels}
  {value_labels}
</svg>'''


def main():
    args = parse_args()
    dates = all_data_dates()
    date = args.date or (dates[-1] if dates else datetime.now().strftime("%Y-%m-%d"))

    scores_data = load_json(os.path.join("data", date, "scores.json"), {"scores": []})
    portfolio = load_json(os.path.join("data", date, "portfolio.json"), {"cash": INITIAL_CASH, "positions": [], "totalValue": INITIAL_CASH})

    top10 = scores_data.get("scores", [])[:10]

    positions = []
    unrealized_pnl_total = 0.0
    for p in portfolio.get("positions", []):
        cost = p["shares"] * p["buyPrice"]
        value = p["shares"] * p["currentPrice"]
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost else 0
        unrealized_pnl_total += pnl
        positions.append({**p, "pnl": pnl, "pnlPct": pnl_pct})

    # 全期間の売買履歴を集計
    all_trades = []
    for d in dates:
        all_trades.extend(load_json(os.path.join("data", d, "trades.json"), []))
    all_trades.sort(key=lambda t: t["date"], reverse=True)

    sell_trades = [t for t in all_trades if t["type"] == "sell"]
    win_count = sum(1 for t in sell_trades if (t.get("pnl") or 0) > 0)
    sell_count = len(sell_trades)
    win_rate = (win_count / sell_count * 100) if sell_count else 0.0

    realized_pnl_total = sum(t.get("pnl") or 0 for t in sell_trades)
    total_pnl = realized_pnl_total + unrealized_pnl_total
    total_pnl_pct = (total_pnl / INITIAL_CASH * 100) if INITIAL_CASH else 0

    # 直近7日の資産推移
    history = []
    for d in dates[-7:]:
        pf = load_json(os.path.join("data", d, "portfolio.json"), None)
        if pf and "totalValue" in pf:
            history.append({"date": d, "totalValue": pf["totalValue"]})
    if not history:
        history = [{"date": date, "totalValue": portfolio.get("totalValue", INITIAL_CASH)}]

    chart_svg = build_chart_svg(history)

    past_report_files = sorted(glob.glob(os.path.join("reports", "*_dashboard.html")), reverse=True)
    past_reports = [
        {"href": f"reports/{os.path.basename(p)}", "label": os.path.basename(p).replace("_dashboard.html", "")}
        for p in past_report_files
    ]

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("dashboard.html.j2")
    html = template.render(
        date=date,
        total_value=portfolio.get("totalValue", INITIAL_CASH),
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        win_rate=win_rate,
        win_count=win_count,
        sell_count=sell_count,
        top10=top10,
        max_score=MAX_SCORE,
        positions=positions,
        chart_svg=chart_svg,
        trade_history=all_trades[:50],
        past_reports=past_reports,
    )

    os.makedirs("docs", exist_ok=True)
    os.makedirs(os.path.join("docs", "reports"), exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    with open(os.path.join("docs", "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join("reports", f"{date}_dashboard.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join("docs", "reports", f"{date}_dashboard.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"完了: docs/index.html, reports/{date}_dashboard.html, docs/reports/{date}_dashboard.html を生成しました")


if __name__ == "__main__":
    main()
