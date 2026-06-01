"""
毎日 Yahoo Finance から終値を取得して financial-planner/prices.json を更新する。
GitHub Actions から平日 16:00 JST (07:00 UTC) に実行。
"""

import json
import os
from datetime import date

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run: pip install yfinance")
    raise

JP_TICKERS = [
    '1343.T', '1357.T', '1605.T', '2181.T', '2502.T', '2503.T',
    '2695.T', '2871.T', '3350.T', '3421.T', '3962.T', '4188.T',
    '4452.T', '4502.T', '5288.T', '6971.T', '7203.T', '7267.T',
    '7388.T', '7522.T', '7867.T', '8267.T', '8410.T', '8473.T',
    '9201.T', '9432.T', '9433.T', '9434.T', '9830.T',
]
US_TICKERS = ['ACN', 'CXSE', 'DAL', 'MSFT', 'TDOC', 'TLT', 'VTRS']
FX_TICKER = 'USDJPY=X'

all_tickers = JP_TICKERS + US_TICKERS + [FX_TICKER]

print(f"Fetching {len(all_tickers)} tickers...")
prices = {}
errors = []

for ticker in all_tickers:
    try:
        hist = yf.Ticker(ticker).history(period='5d')
        if hist.empty:
            errors.append(f"{ticker}: no data")
            continue
        price = float(hist['Close'].dropna().iloc[-1])
        prices[ticker] = round(price, 4)
        print(f"  {ticker}: {price:.4f}")
    except Exception as e:
        errors.append(f"{ticker}: {e}")
        print(f"  ERROR {ticker}: {e}")

fx_rate = prices.pop(FX_TICKER, 145.0)

output = {
    "updated": str(date.today()),
    "fxRate": round(fx_rate, 2),
    "prices": prices,
}

out_path = os.path.join(os.path.dirname(__file__), '..', 'financial-planner', 'prices.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nDone: {len(prices)} prices saved. USDJPY={fx_rate:.2f}")
if errors:
    print("Errors:", errors)
