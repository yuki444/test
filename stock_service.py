import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

# In-memory cache: {ticker: {"data": ..., "expires": timestamp}}
_cache: Dict[str, Dict] = {}
CACHE_TTL = 300  # 5 minutes


def normalize_ticker(ticker: str) -> str:
    """Normalize ticker to yfinance format. Append .T for TSE stocks if no suffix."""
    ticker = ticker.strip().upper()
    # If already has a suffix like .T, .OS, .N, etc., leave it
    if "." in ticker:
        return ticker
    # If it looks like a numeric Japanese ticker, append .T
    if ticker.isdigit() or (len(ticker) == 4 and ticker[:4].isdigit()):
        return ticker + ".T"
    return ticker


def _get_cached(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and entry["expires"] > time.time():
        return entry["data"]
    return None


def _set_cached(key: str, data: Any):
    _cache[key] = {"data": data, "expires": time.time() + CACHE_TTL}


def get_stock_info(ticker: str) -> Dict[str, Any]:
    """Get full stock information including current price and fundamentals."""
    ticker = normalize_ticker(ticker)
    cached = _get_cached(f"info:{ticker}")
    if cached is not None:
        return cached

    result = {
        "ticker": ticker,
        "name": None,
        "current_price": None,
        "previous_close": None,
        "day_change": None,
        "day_change_pct": None,
        "volume": None,
        "market_cap": None,
        "per": None,
        "dividend_yield": None,
        "week52_high": None,
        "week52_low": None,
        "currency": "JPY",
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        result["name"] = info.get("longName") or info.get("shortName") or ticker

        # Current price: try multiple fields
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("ask")
            or info.get("bid")
        )

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        if price is None and prev_close is not None:
            price = prev_close

        result["current_price"] = price
        result["previous_close"] = prev_close

        if price is not None and prev_close is not None and prev_close != 0:
            result["day_change"] = round(price - prev_close, 2)
            result["day_change_pct"] = round((price - prev_close) / prev_close * 100, 2)

        result["volume"] = info.get("volume") or info.get("regularMarketVolume")
        result["market_cap"] = info.get("marketCap")
        result["per"] = info.get("trailingPE") or info.get("forwardPE")
        dy = info.get("dividendYield")
        result["dividend_yield"] = round(dy * 100, 2) if dy else None
        result["week52_high"] = info.get("fiftyTwoWeekHigh")
        result["week52_low"] = info.get("fiftyTwoWeekLow")
        result["currency"] = info.get("currency", "JPY")

    except Exception as e:
        logger.warning(f"Error fetching info for {ticker}: {e}")

    _set_cached(f"info:{ticker}", result)
    return result


def get_current_price(ticker: str) -> Optional[float]:
    """Get just the current price (uses cached info if available)."""
    info = get_stock_info(ticker)
    return info.get("current_price")


def get_price_history(ticker: str, period: str = "3m") -> Dict[str, Any]:
    """
    Get price history for chart.
    period: '1m', '3m', '6m', '1y'
    Returns {dates: [...], prices: [...]}
    """
    ticker = normalize_ticker(ticker)
    cache_key = f"hist:{ticker}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    period_map = {
        "1m": "1mo",
        "3m": "3mo",
        "6m": "6mo",
        "1y": "1y",
    }
    yf_period = period_map.get(period, "3mo")

    result = {"dates": [], "prices": []}

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=yf_period, interval="1d")
        if not hist.empty:
            result["dates"] = [d.strftime("%Y-%m-%d") for d in hist.index]
            result["prices"] = [round(float(p), 2) for p in hist["Close"].tolist()]
    except Exception as e:
        logger.warning(f"Error fetching history for {ticker}: {e}")

    _set_cached(cache_key, result)
    return result


def get_batch_prices(tickers: list) -> Dict[str, Optional[float]]:
    """Get current prices for multiple tickers efficiently."""
    results = {}
    for ticker in tickers:
        try:
            info = get_stock_info(ticker)
            results[ticker] = info.get("current_price")
        except Exception:
            results[ticker] = None
    return results
