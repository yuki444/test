"""Technical indicators (mirrors stock-app/src/utils/technicals.ts)."""


def sma(data: list, period: int) -> float:
    if len(data) < period:
        return 0
    return sum(data[-period:]) / period


def ema_array(data: list, period: int) -> list:
    if not data:
        return []
    k = 2 / (period + 1)
    result = [data[0]]
    for v in data[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses -= diff

    avg_gain = gains / period
    avg_loss = losses / period

    for i in range(period + 1, len(closes)):
        diff = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(0, diff)) / period
        avg_loss = (avg_loss * (period - 1) + max(0, -diff)) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(closes: list, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
    if len(closes) < slow_period + signal_period:
        return {"macd_line": 0, "signal_line": 0, "histogram": 0, "is_bullish": False, "crossed_up": False}

    ema_fast = ema_array(closes, fast_period)
    ema_slow = ema_array(closes, slow_period)
    macd_line_arr = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_arr = ema_array(macd_line_arr[-(signal_period + 10):], signal_period)

    last_macd = macd_line_arr[-1]
    prev_macd = macd_line_arr[-2] if len(macd_line_arr) >= 2 else 0
    last_signal = signal_arr[-1]
    prev_signal = signal_arr[-2] if len(signal_arr) >= 2 else 0
    histogram = last_macd - last_signal
    prev_histogram = prev_macd - prev_signal

    return {
        "macd_line": last_macd,
        "signal_line": last_signal,
        "histogram": histogram,
        "is_bullish": histogram > 0,
        "crossed_up": histogram > 0 and prev_histogram <= 0,
    }


def volume_ratio(volumes: list, period: int = 20) -> float:
    if len(volumes) < period + 1:
        return 1
    avg = sma(volumes[:-1], period)
    if avg == 0:
        return 1
    return volumes[-1] / avg


def period_return(closes: list, days: int) -> float:
    if len(closes) < days + 1:
        return 0
    current = closes[-1]
    past = closes[-1 - days]
    if past == 0:
        return 0
    return (current - past) / past
