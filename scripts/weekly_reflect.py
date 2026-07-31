"""先週のTOP10推奨と実績リターンを比較し、軸別重みを自動調整する。

使い方:
    python scripts/weekly_reflect.py
    python scripts/weekly_reflect.py --date 2026-07-30
"""
import argparse
import json
import os
from datetime import datetime, timedelta

from jinja2 import Environment, FileSystemLoader

WEIGHTS_PATH = os.path.join("config", "scoring_weights.json")
TEMPLATE_DIR = os.path.join("scripts", "templates")
MAX_WEIGHT_DELTA = 0.2
AXES = ["technical", "fundamental", "momentum", "news"]


def parse_args():
    parser = argparse.ArgumentParser(description="週次振り返り・重み調整")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    return parser.parse_args()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def available_score_dates():
    if not os.path.isdir("data"):
        return []
    return sorted(
        d for d in os.listdir("data")
        if os.path.exists(os.path.join("data", d, "scores.json"))
    )


def nearest_on_or_before(dates: list, target: str):
    candidates = [d for d in dates if d <= target]
    return candidates[-1] if candidates else None


def pearson(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / (var_x ** 0.5 * var_y ** 0.5)


def render_insufficient_data(today: str, reason: str):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("reflection.html.j2")
    html = template.render(
        date=today,
        insufficient=True,
        insufficient_reason=reason,
        accuracy_table=[],
        axis_stats=[],
        weight_before={},
        weight_after={},
        update_reason="",
        next_week_watch=[],
    )
    os.makedirs("reports", exist_ok=True)
    with open(os.path.join("reports", f"{today}_reflection.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    args = parse_args()
    today = args.date

    score_dates = available_score_dates()
    today_date = nearest_on_or_before(score_dates, today)
    if today_date is None:
        print(f"データなし: data/{today} 以前に scores.json が見つかりません")
        render_insufficient_data(today, "スコア履歴データがまだ蓄積されていません。")
        return

    week_ago_target = (datetime.strptime(today_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    week_ago_date = nearest_on_or_before(score_dates, week_ago_target)

    today_scores = load_json(os.path.join("data", today_date, "scores.json"), {"scores": []})

    if week_ago_date is None or week_ago_date == today_date:
        print("データ不足: 1週間以上前のスコア履歴がまだありません。重み調整はスキップします。")
        render_insufficient_data(
            today_date,
            "1週間以上前のスコア履歴がまだ蓄積されていないため、振り返り評価と重み調整をスキップしました。"
            "運用開始から7日以上経過すると自動的に評価が始まります。",
        )
        return

    week_ago_scores = load_json(os.path.join("data", week_ago_date, "scores.json"), {"scores": []})

    today_price_by_code = {s["code"]: s["currentPrice"] for s in today_scores["scores"]}
    week_ago_by_code = {s["code"]: s for s in week_ago_scores["scores"]}

    # 銘柄別の予測 vs 実績
    accuracy_rows = []
    axis_series = {axis: {"scores": [], "returns": []} for axis in AXES}

    for code, past in week_ago_by_code.items():
        if code not in today_price_by_code or past["currentPrice"] <= 0:
            continue
        actual_return_pct = (today_price_by_code[code] - past["currentPrice"]) / past["currentPrice"] * 100

        for axis in AXES:
            axis_series[axis]["scores"].append(past[axis]["score"])
            axis_series[axis]["returns"].append(actual_return_pct)

        accuracy_rows.append({
            "code": code,
            "name": past["name"],
            "predictedScore": past["totalScore"],
            "actualReturnPct": actual_return_pct,
            "hit": actual_return_pct > 0,
        })

    accuracy_rows.sort(key=lambda r: r["predictedScore"], reverse=True)
    top10_rows = accuracy_rows[:10]

    # 軸別相関係数
    axis_stats = []
    for axis in AXES:
        corr = pearson(axis_series[axis]["scores"], axis_series[axis]["returns"])
        axis_stats.append({"axis": axis, "correlation": corr})

    # 重み調整（±0.2の範囲でクランプ）
    weights = load_json(WEIGHTS_PATH, {a: 1.0 for a in AXES})
    weight_before = {a: weights.get(a, 1.0) for a in AXES}
    weight_after = {}
    reason_lines = []

    for stat in axis_stats:
        axis = stat["axis"]
        corr = stat["correlation"]
        raw_delta = corr * 0.4
        delta = max(-MAX_WEIGHT_DELTA, min(MAX_WEIGHT_DELTA, raw_delta))
        new_weight = max(0.2, round(weight_before[axis] + delta, 2))
        weight_after[axis] = new_weight
        direction = "引き上げ" if delta > 0 else ("引き下げ" if delta < 0 else "維持")
        reason_lines.append(
            f"{axis}: 相関係数 {corr:.2f} → 重み {weight_before[axis]:.2f} → {new_weight:.2f}（{direction}, Δ{delta:+.2f}）"
        )

    update_reason = "先週TOP10推奨銘柄群の週次リターンとの相関に基づき自動調整。\n" + "\n".join(reason_lines)

    weights.update(weight_after)
    weights["last_updated"] = today_date
    weights["update_reason"] = update_reason
    save_json(WEIGHTS_PATH, weights)

    next_week_watch = today_scores["scores"][:10]

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("reflection.html.j2")
    html = template.render(
        date=today_date,
        insufficient=False,
        week_ago_date=week_ago_date,
        accuracy_table=top10_rows,
        axis_stats=axis_stats,
        weight_before=weight_before,
        weight_after=weight_after,
        update_reason=update_reason,
        next_week_watch=next_week_watch,
    )
    os.makedirs("reports", exist_ok=True)
    with open(os.path.join("reports", f"{today_date}_reflection.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"完了: reports/{today_date}_reflection.html を生成し、重みを更新しました")
    for line in reason_lines:
        print(f"  {line}")


if __name__ == "__main__":
    main()
