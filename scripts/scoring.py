"""Stock scoring logic (mirrors stock-app/src/utils/scoring.ts).

Four axes, weighted by config/scoring_weights.json:
  technical (max 90) / fundamental (max 75) / momentum (max 45) / news (max 45)
"""
from datetime import datetime, timezone

from technicals import ema_array, macd, period_return, rsi, sma, volume_ratio


def _tech_score(closes: list, volumes: list) -> dict:
    score = 0
    details = []

    ma5 = sma(closes, 5)
    ma25 = sma(closes, 25)
    ma50 = sma(closes, 50)
    last = closes[-1]

    if len(closes) >= 25 and ma5 > ma25:
        score += 20
        details.append(f"MA5({ma5:.0f}) > MA25({ma25:.0f}) ✓ 短期上昇トレンド")

    if len(closes) >= 50 and ma25 > ma50:
        score += 30
        details.append("MA25 > MA50 ✓ ゴールデンクロス圏")

    rsi_val = rsi(closes)
    if 30 <= rsi_val <= 55:
        score += 20
        details.append(f"RSI {rsi_val:.1f} ✓ 売られすぎからの回復ゾーン")
    elif rsi_val < 30:
        score += 8
        details.append(f"RSI {rsi_val:.1f} △ 売られすぎ水準")
    elif rsi_val > 70:
        details.append(f"RSI {rsi_val:.1f} ✗ 買われすぎ水準")

    m = macd(closes)
    if m["crossed_up"]:
        score += 20
        details.append("MACDゴールデンクロス発生 ✓")
    elif m["is_bullish"]:
        score += 10
        details.append(f"MACDヒストグラム プラス({m['histogram']:.2f}) ✓")

    vr = volume_ratio(volumes, 20)
    if vr >= 2.0:
        score += 10
        details.append(f"出来高急増 ✓ 20日平均比 {vr * 100:.0f}%")
    elif vr >= 1.5:
        score += 5
        details.append(f"出来高増加 {vr * 100:.0f}%")

    period_high = max(closes[-60:])
    high_ratio = last / period_high if period_high else 0
    if high_ratio >= 0.95:
        score += 10
        details.append(f"期間高値圏 {high_ratio * 100:.1f}% ✓")

    return {"score": score, "max": 90, "details": details}


def _fund_score(current_price: float, statements: list) -> dict:
    details = []
    if not statements:
        return {"score": 0, "max": 75, "details": ["財務データなし"]}

    score = 0
    s = statements[0]
    bps = s.get("BookValuePerShare") or 0
    eps = s.get("EarningsPerShare") or 0
    div_annual = s.get("ResultDividendPerShareAnnual") or s.get("ForecastDividendPerShareAnnual") or 0

    if bps > 0:
        pbr = current_price / bps
        if pbr < 1.0:
            score += 20
            details.append(f"PBR {pbr:.2f}倍 ✓ 解散価値以下")
        elif pbr < 2.0:
            score += 10
            details.append(f"PBR {pbr:.2f}倍 ✓ 割安圏")
        else:
            details.append(f"PBR {pbr:.2f}倍")

    if eps > 0:
        per = current_price / eps
        if per < 12:
            score += 20
            details.append(f"PER {per:.1f}倍 ✓ 割安")
        elif per < 20:
            score += 12
            details.append(f"PER {per:.1f}倍 ✓ 適正圏")
        elif per < 30:
            score += 4
            details.append(f"PER {per:.1f}倍")
        else:
            details.append(f"PER {per:.1f}倍 ✗ 割高")

        score += 15
        details.append(f"EPS {eps:.0f}円 ✓ 黒字")
    elif eps < 0:
        details.append(f"EPS {eps:.0f}円 ✗ 赤字")

    if div_annual > 0 and current_price > 0:
        div_yield = (div_annual / current_price) * 100
        if div_yield >= 3:
            score += 20
            details.append(f"配当利回り {div_yield:.1f}% ✓ 高配当")
        elif div_yield >= 2:
            score += 12
            details.append(f"配当利回り {div_yield:.1f}% ✓")
        elif div_yield > 0:
            score += 5
            details.append(f"配当利回り {div_yield:.1f}%")
    else:
        details.append("無配当")

    return {"score": score, "max": 75, "details": details}


def _mom_score(closes: list) -> dict:
    score = 0
    details = []

    ret5 = period_return(closes, 5) * 100
    ret20 = period_return(closes, 20) * 100
    ret60 = period_return(closes, 60) * 100

    if ret5 > 3:
        score += 15
        details.append(f"5日リターン +{ret5:.1f}% ✓")
    elif ret5 > 0:
        score += 8
        details.append(f"5日リターン +{ret5:.1f}%")
    else:
        details.append(f"5日リターン {ret5:.1f}%")

    if ret20 > 5:
        score += 20
        details.append(f"20日リターン +{ret20:.1f}% ✓")
    elif ret20 > 0:
        score += 10
        details.append(f"20日リターン +{ret20:.1f}%")
    else:
        details.append(f"20日リターン {ret20:.1f}%")

    if ret60 > 10:
        score += 10
        details.append(f"60日リターン +{ret60:.1f}% ✓")
    elif ret60 > 0:
        score += 5
        details.append(f"60日リターン +{ret60:.1f}%")

    return {"score": score, "max": 45, "details": details}


def _news_score(statements: list) -> dict:
    if not statements:
        return {"score": 0, "max": 45, "details": ["決算情報なし"]}

    score = 0
    details = []
    latest = statements[0]
    disclosed_date = datetime.strptime(latest["DisclosedDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - disclosed_date).days

    if days_since <= 7:
        score += 20
        details.append(f"直近決算開示 {days_since}日前 ✓ 最新情報")
    elif days_since <= 30:
        score += 10
        details.append(f"決算開示 {days_since}日前")
    else:
        details.append(f"直近決算 {days_since}日前")

    eps = latest.get("EarningsPerShare") or 0
    forecast_eps = latest.get("ForecastEarningsPerShare") or 0
    if forecast_eps != 0 and eps != 0:
        beat = (eps - forecast_eps) / abs(forecast_eps)
        if beat > 0.1:
            score += 25
            details.append(f"EPS 予想比 +{beat * 100:.0f}% 上振れ ✓")
        elif beat > 0.02:
            score += 12
            details.append(f"EPS 予想比 +{beat * 100:.0f}%")
        elif beat < -0.1:
            details.append(f"EPS 予想比 {beat * 100:.0f}% 下振れ ✗")

    operating_profit = latest.get("OperatingProfit") or 0
    if operating_profit > 0:
        score += 5
        details.append(f"営業利益 {operating_profit / 1e8:.0f}億円")

    return {"score": score, "max": 45, "details": details}


def calculate_stock_score(info: dict, quotes: list, statements: list, weights: dict) -> dict:
    empty = {
        "code": info["code"],
        "name": info["name"],
        "totalScore": 0,
        "technical": {"score": 0, "max": 90, "details": ["データ不足"], "weight": weights.get("technical", 1.0), "weightedScore": 0},
        "fundamental": {"score": 0, "max": 75, "details": ["データ不足"], "weight": weights.get("fundamental", 1.0), "weightedScore": 0},
        "momentum": {"score": 0, "max": 45, "details": ["データ不足"], "weight": weights.get("momentum", 1.0), "weightedScore": 0},
        "news": {"score": 0, "max": 45, "details": ["データ不足"], "weight": weights.get("news", 1.0), "weightedScore": 0},
        "currentPrice": 0,
        "priceChange": 0,
        "priceChangePct": 0,
        "rsi": 50,
        "reasoning": "直近5日分の株価データが不足しているためスコア計算不可。",
    }
    if len(quotes) < 5:
        return empty

    closes = [q.get("AdjustmentClose") or q["Close"] for q in quotes]
    volumes = [q.get("AdjustmentVolume") or q["Volume"] for q in quotes]
    current_price = closes[-1]
    prev_price = closes[-2] if len(closes) >= 2 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price * 100) if prev_price else 0

    technical = _tech_score(closes, volumes)
    fundamental = _fund_score(current_price, statements)
    momentum = _mom_score(closes)
    news = _news_score(statements)

    axes = {"technical": technical, "fundamental": fundamental, "momentum": momentum, "news": news}
    total = 0.0
    for name, axis in axes.items():
        w = weights.get(name, 1.0)
        weighted = axis["score"] * w
        axis["weight"] = w
        axis["weightedScore"] = round(weighted, 2)
        total += weighted

    reasoning_parts = []
    for label, axis in (("テクニカル", technical), ("ファンダメンタル", fundamental), ("モメンタム", momentum), ("ニュース", news)):
        if axis["details"]:
            reasoning_parts.append(f"[{label} {axis['score']}/{axis['max']}pt (重み{axis['weight']:.2f})] " + " / ".join(axis["details"]))
    reasoning = "\n".join(reasoning_parts)

    return {
        "code": info["code"],
        "name": info["name"],
        "totalScore": round(total, 2),
        "technical": technical,
        "fundamental": fundamental,
        "momentum": momentum,
        "news": news,
        "currentPrice": current_price,
        "priceChange": price_change,
        "priceChangePct": price_change_pct,
        "rsi": rsi(closes),
        "reasoning": reasoning,
    }
