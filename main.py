from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import logging

import database as db
import stock_service as svc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Japanese Stock Portfolio Manager")

# Initialize database on startup
@app.on_event("startup")
async def startup():
    db.init_db()

# ─────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────

class HoldingCreate(BaseModel):
    ticker: str
    shares: float
    avg_cost: float
    notes: Optional[str] = None


class HoldingUpdate(BaseModel):
    ticker: Optional[str] = None
    shares: Optional[float] = None
    avg_cost: Optional[float] = None
    notes: Optional[str] = None


class TradeCreate(BaseModel):
    ticker: str
    trade_type: str  # BUY or SELL
    shares: float
    price: float
    fee: float = 0.0
    trade_date: str  # YYYY-MM-DD
    notes: Optional[str] = None


class WatchlistCreate(BaseModel):
    ticker: str
    target_price: Optional[float] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class EventCreate(BaseModel):
    ticker: str
    event_type: str  # 決算, 配当, 優待, その他
    event_date: str  # YYYY-MM-DD
    description: Optional[str] = None


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def normalize(ticker: str) -> str:
    return svc.normalize_ticker(ticker)


def enrich_holding(h: dict) -> dict:
    """Add live price data to a holding dict."""
    ticker = h["ticker"]
    info = svc.get_stock_info(ticker)

    current_price = info.get("current_price")
    day_change = info.get("day_change")
    day_change_pct = info.get("day_change_pct")

    if current_price is not None:
        current_value = round(current_price * h["shares"], 2)
        cost_basis = round(h["avg_cost"] * h["shares"], 2)
        pnl = round(current_value - cost_basis, 2)
        pnl_pct = round(pnl / cost_basis * 100, 2) if cost_basis != 0 else 0
    else:
        current_value = None
        cost_basis = round(h["avg_cost"] * h["shares"], 2)
        pnl = None
        pnl_pct = None

    return {
        **h,
        "name": h.get("name") or info.get("name"),
        "current_price": current_price,
        "current_value": current_value,
        "cost_basis": cost_basis,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "day_change": day_change,
        "day_change_pct": day_change_pct,
    }


# ─────────────────────────────────────────────
# Portfolio routes
# ─────────────────────────────────────────────

@app.get("/api/portfolio")
def get_portfolio():
    holdings = db.get_all_holdings()
    enriched = [enrich_holding(h) for h in holdings]
    return enriched


@app.get("/api/portfolio/summary")
def get_portfolio_summary():
    holdings = db.get_all_holdings()
    enriched = [enrich_holding(h) for h in holdings]

    total_cost = sum(h["cost_basis"] for h in enriched)
    total_value = sum(h["current_value"] for h in enriched if h["current_value"] is not None)
    total_pnl = round(total_value - total_cost, 2)
    total_pnl_pct = round(total_pnl / total_cost * 100, 2) if total_cost != 0 else 0

    day_change_total = sum(
        (h["day_change"] or 0) * h["shares"]
        for h in enriched
        if h["day_change"] is not None
    )

    return {
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "day_change_total": round(day_change_total, 2),
        "count": len(enriched),
    }


@app.post("/api/portfolio", status_code=201)
def add_holding(payload: HoldingCreate):
    ticker = normalize(payload.ticker)
    info = svc.get_stock_info(ticker)
    name = info.get("name") or ticker

    existing = db.get_holding_by_ticker(ticker)
    if existing:
        raise HTTPException(status_code=400, detail=f"{ticker} は既に保有リストにあります。売買履歴から取引を記録してください。")

    holding_id = db.insert_holding(ticker, name, payload.shares, payload.avg_cost, payload.notes)
    holdings = db.get_all_holdings()
    h = next((h for h in holdings if h["id"] == holding_id), None)
    return enrich_holding(h) if h else {"id": holding_id}


@app.put("/api/portfolio/{holding_id}")
def update_holding(holding_id: int, payload: HoldingUpdate):
    updates = {}
    if payload.ticker is not None:
        updates["ticker"] = normalize(payload.ticker)
    if payload.shares is not None:
        updates["shares"] = payload.shares
    if payload.avg_cost is not None:
        updates["avg_cost"] = payload.avg_cost
    if payload.notes is not None:
        updates["notes"] = payload.notes

    if not updates:
        raise HTTPException(status_code=400, detail="更新するフィールドがありません")

    db.update_holding(holding_id, **updates)
    holdings = db.get_all_holdings()
    h = next((h for h in holdings if h["id"] == holding_id), None)
    if not h:
        raise HTTPException(status_code=404, detail="保有銘柄が見つかりません")
    return enrich_holding(h)


@app.delete("/api/portfolio/{holding_id}")
def delete_holding(holding_id: int):
    db.delete_holding(holding_id)
    return {"ok": True}


# ─────────────────────────────────────────────
# Trade routes
# ─────────────────────────────────────────────

@app.get("/api/trades")
def get_trades():
    return db.get_all_trades()


@app.post("/api/trades", status_code=201)
def record_trade(payload: TradeCreate):
    ticker = normalize(payload.ticker)
    trade_type = payload.trade_type.upper()

    if trade_type not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="trade_type は BUY または SELL である必要があります")

    realized_pnl = None

    if trade_type == "SELL":
        holding = db.get_holding_by_ticker(ticker)
        if holding:
            cost = holding["avg_cost"]
            realized_pnl = round((payload.price - cost) * payload.shares - payload.fee, 2)
        else:
            realized_pnl = 0.0

    info = svc.get_stock_info(ticker)
    name = info.get("name") or ticker

    trade_id = db.insert_trade(
        ticker, trade_type, payload.shares, payload.price,
        payload.fee, payload.trade_date, payload.notes, realized_pnl
    )

    db.upsert_holding_from_trade(ticker, name, payload.shares, payload.price, trade_type)

    return {"id": trade_id, "realized_pnl": realized_pnl}


@app.delete("/api/trades/{trade_id}")
def delete_trade(trade_id: int):
    db.delete_trade(trade_id)
    return {"ok": True}


# ─────────────────────────────────────────────
# Watchlist routes
# ─────────────────────────────────────────────

@app.get("/api/watchlist")
def get_watchlist():
    items = db.get_all_watchlist()
    result = []
    for item in items:
        ticker = item["ticker"]
        info = svc.get_stock_info(ticker)
        current_price = info.get("current_price")
        target = item.get("target_price")

        distance = None
        distance_pct = None
        if current_price and target:
            distance = round(target - current_price, 2)
            distance_pct = round((target - current_price) / current_price * 100, 2)

        result.append({
            **item,
            "name": item.get("name") or info.get("name"),
            "current_price": current_price,
            "day_change": info.get("day_change"),
            "day_change_pct": info.get("day_change_pct"),
            "distance": distance,
            "distance_pct": distance_pct,
        })
    return result


@app.post("/api/watchlist", status_code=201)
def add_watchlist(payload: WatchlistCreate):
    ticker = normalize(payload.ticker)
    info = svc.get_stock_info(ticker)
    name = info.get("name") or ticker

    wl_id = db.insert_watchlist(ticker, name, payload.target_price, payload.category, payload.notes)
    return {"id": wl_id, "ticker": ticker, "name": name}


@app.delete("/api/watchlist/{wl_id}")
def delete_watchlist(wl_id: int):
    db.delete_watchlist(wl_id)
    return {"ok": True}


# ─────────────────────────────────────────────
# Events routes
# ─────────────────────────────────────────────

@app.get("/api/events")
def get_events():
    return db.get_all_events()


@app.get("/api/events/upcoming")
def get_upcoming_events():
    return db.get_upcoming_events(30)


@app.post("/api/events", status_code=201)
def add_event(payload: EventCreate):
    valid_types = ("決算", "配当", "優待", "その他")
    if payload.event_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"event_type は {valid_types} のいずれかである必要があります")

    event_id = db.insert_event(
        normalize(payload.ticker), payload.event_type,
        payload.event_date, payload.description
    )
    return {"id": event_id}


@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    db.delete_event(event_id)
    return {"ok": True}


# ─────────────────────────────────────────────
# Stock info routes
# ─────────────────────────────────────────────

@app.get("/api/stock/{ticker}")
def get_stock(ticker: str):
    ticker = normalize(ticker)
    return svc.get_stock_info(ticker)


@app.get("/api/stock/{ticker}/history")
def get_stock_history(ticker: str, period: str = "3m"):
    ticker = normalize(ticker)
    return svc.get_price_history(ticker, period)


# ─────────────────────────────────────────────
# Static files
# ─────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))
