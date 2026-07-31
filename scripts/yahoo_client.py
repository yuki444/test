"""Yahoo Financeクライアント（yfinance経由、認証不要）。

出力スキーマは旧J-Quantsクライアントと互換にしてあるため、
scoring.py 側は変更不要。
"""
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

TICKER_SUFFIX = ".T"  # 東証銘柄


def _to_ticker(code: str) -> str:
    return f"{code}{TICKER_SUFFIX}"


def get_daily_quotes(code: str, date_from: str, date_to: str) -> list:
    ticker = yf.Ticker(_to_ticker(code))
    end_exclusive = (datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    hist = ticker.history(start=date_from, end=end_exclusive, auto_adjust=False)
    if hist is None or hist.empty:
        return []

    hist = hist.reset_index()
    quotes = []
    for _, row in hist.iterrows():
        close = row.get("Close")
        adj_close = row.get("Adj Close")
        if pd.isna(adj_close):
            adj_close = close
        volume = int(row.get("Volume") or 0)

        quotes.append({
            "Date": row["Date"].strftime("%Y-%m-%d"),
            "Code": code,
            "Open": round(float(row["Open"]), 1),
            "High": round(float(row["High"]), 1),
            "Low": round(float(row["Low"]), 1),
            "Close": round(float(close), 1),
            "Volume": volume,
            "AdjustmentClose": round(float(adj_close), 1),
            "AdjustmentVolume": volume,
        })
    return quotes


def _clean(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _latest_operating_profit(ticker: "yf.Ticker") -> float:
    # 四半期データに営業利益が無い銘柄があるため、年次データ・EBITまで順にフォールバック
    for attr in ("quarterly_income_stmt", "quarterly_financials", "income_stmt", "financials"):
        try:
            fin = getattr(ticker, attr)
        except Exception:
            continue
        if fin is None or fin.empty:
            continue
        for row_name in ("Operating Income", "Total Operating Income As Reported", "EBIT"):
            if row_name in fin.index:
                val = _clean(fin.loc[row_name].iloc[0])
                if val is not None:
                    return val
    return 0.0


def get_financial_info(code: str) -> list:
    """J-Quants の /fins/statements 互換形式で、直近の決算情報を1件返す。

    Yahoo Financeは日本株の「決算短信」の開示日そのものは提供しないため、
    実績決算日（get_earnings_dates）→ 直近四半期末日（mostRecentQuarter）の順で代用する。
    """
    ticker = yf.Ticker(_to_ticker(code))

    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    bps = _clean(info.get("bookValue")) or 0
    eps = _clean(info.get("trailingEps")) or 0
    forecast_eps = _clean(info.get("forwardEps")) or eps
    dividend_rate = _clean(info.get("dividendRate"))
    net_sales = _clean(info.get("totalRevenue")) or 0
    profit = _clean(info.get("netIncomeToCommon")) or 0

    disclosed_date = None
    eps_actual = eps
    eps_forecast = forecast_eps

    try:
        earnings = ticker.get_earnings_dates(limit=8)
        if earnings is not None and not earnings.empty:
            now = pd.Timestamp.now(tz=earnings.index.tz)
            past = earnings[earnings.index <= now].sort_index(ascending=False)
            if not past.empty:
                latest = past.iloc[0]
                disclosed_date = past.index[0].strftime("%Y-%m-%d")
                reported = _clean(latest.get("Reported EPS"))
                estimated = _clean(latest.get("EPS Estimate"))
                if reported is not None:
                    eps_actual = reported
                if estimated is not None:
                    eps_forecast = estimated
    except Exception:
        pass

    if disclosed_date is None:
        mrq = info.get("mostRecentQuarter")
        if mrq:
            disclosed_date = datetime.fromtimestamp(mrq).strftime("%Y-%m-%d")

    if disclosed_date is None:
        return []

    operating_profit = _latest_operating_profit(ticker)

    return [{
        "DisclosedDate": disclosed_date,
        "LocalCode": code,
        "TypeOfDocument": "YahooFinanceInfo",
        "BookValuePerShare": bps,
        "EarningsPerShare": eps_actual,
        "ForecastEarningsPerShare": eps_forecast,
        "ResultDividendPerShareAnnual": dividend_rate,
        "ForecastDividendPerShareAnnual": dividend_rate,
        "NetSales": net_sales,
        "OperatingProfit": operating_profit,
        "Profit": profit,
    }]
