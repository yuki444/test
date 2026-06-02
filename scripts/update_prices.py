"""
毎日 Yahoo Finance から終値・年間配当を取得して financial-planner/prices.json を更新する。
GitHub Actions から平日 07:00 UTC (16:00 JST) に実行。

prices.json フォーマット:
  {
    "updated": "YYYY-MM-DD",
    "fxRate": 145.0,
    "prices": {
      "ACN":    {"p": 187.07, "d": 5.72},   // p=終値(USD), d=年間配当/株(USD)
      "9433.T": {"p": 2686.0, "d": 145.0}   // p=終値(JPY), d=年間配当/株(JPY)
    }
  }
"""

import json
import os
from datetime import date, datetime, timezone, timedelta

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run: pip install yfinance")
    raise

JP_TICKERS = [
    '1343.T', '1357.T', '1605.T', '2181.T', '2502.T', '2503.T',
    '2695.T', '2871.T', '2928.T', '3350.T', '3421.T', '3962.T',
    '4188.T', '4452.T', '4502.T', '5288.T', '6971.T', '7203.T',
    '7267.T', '7272.T', '7388.T', '7522.T', '7867.T', '8173.T',
    '8267.T', '8410.T', '8473.T', '9201.T', '9432.T', '9433.T',
    '9434.T', '9830.T',
]
US_TICKERS = ['ACN', 'CXSE', 'DAL', 'MSFT', 'TDOC', 'TLT', 'VTRS']
CRYPTO_TICKERS = ['BTC-JPY', 'ETH-JPY']
FX_TICKER = 'USDJPY=X'


def get_price(ticker_obj):
    """最新終値を取得。"""
    try:
        hist = ticker_obj.history(period='5d')
        if not hist.empty:
            return float(hist['Close'].dropna().iloc[-1])
    except Exception:
        pass
    try:
        info = ticker_obj.info
        return float(
            info.get('regularMarketPrice') or
            info.get('currentPrice') or
            info.get('previousClose') or 0
        )
    except Exception:
        return 0.0


def get_annual_dividend(ticker_obj):
    """年間配当/株を取得。複数手段でフォールバック。"""
    # 手段1: info の dividendRate / trailingAnnualDividendRate
    try:
        info = ticker_obj.info
        rate = (info.get('dividendRate') or
                info.get('trailingAnnualDividendRate') or 0)
        if rate and float(rate) > 0:
            return round(float(rate), 2)
    except Exception:
        pass

    # 手段2: 過去12ヶ月の実配当を合算
    try:
        divs = ticker_obj.dividends
        if len(divs) > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(days=365)
            recent = divs[divs.index.tz_convert('UTC') > cutoff]
            if len(recent) > 0:
                return round(float(recent.sum()), 2)
    except Exception:
        pass

    return 0.0


all_tickers = JP_TICKERS + US_TICKERS + CRYPTO_TICKERS + [FX_TICKER]
print(f"Fetching {len(all_tickers)} tickers...")

prices = {}
errors = []

for sym in all_tickers:
    try:
        t = yf.Ticker(sym)
        price = get_price(t)
        if price == 0:
            errors.append(f"{sym}: price=0")
            continue

        if sym == FX_TICKER:
            prices[sym] = price
        elif sym in CRYPTO_TICKERS:
            short = sym.replace('-JPY', '')
            prices[short] = {"p": round(price, 0), "d": 0}
        else:
            div = get_annual_dividend(t)
            prices[sym] = {"p": round(price, 4), "d": div}
            flag = f" div={div}" if div > 0 else ""
            print(f"  {sym}: {price:.2f}{flag}")
    except Exception as e:
        errors.append(f"{sym}: {e}")
        print(f"  ERROR {sym}: {e}")

fx_rate = round(prices.pop(FX_TICKER, 145.0), 2)

output = {
    "updated": str(date.today()),
    "fxRate": fx_rate,
    "prices": prices,
}

out_path = os.path.join(os.path.dirname(__file__), '..', 'financial-planner', 'prices.json')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

total = len(prices)
with_div = sum(1 for v in prices.values() if isinstance(v, dict) and v.get('d', 0) > 0)
print(f"\nDone: {total} tickers saved (配当あり: {with_div}件). USDJPY={fx_rate}")
if errors:
    print("Errors:", errors)
