import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT,
                shares REAL NOT NULL DEFAULT 0,
                avg_cost REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                trade_type TEXT NOT NULL CHECK(trade_type IN ('BUY', 'SELL')),
                shares REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL NOT NULL DEFAULT 0,
                trade_date TEXT NOT NULL,
                notes TEXT,
                realized_pnl REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT,
                target_price REAL,
                category TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('決算', '配当', '優待', 'その他')),
                event_date TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
    finally:
        conn.close()


def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- Holdings ----------

def get_all_holdings():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM holdings ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_holding_by_ticker(ticker: str):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM holdings WHERE ticker=?", (ticker,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_holding(ticker, name, shares, avg_cost, notes):
    conn = get_connection()
    try:
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO holdings (ticker, name, shares, avg_cost, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (ticker, name, shares, avg_cost, notes, now, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_holding(id, **kwargs):
    conn = get_connection()
    try:
        kwargs["updated_at"] = now_iso()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [id]
        conn.execute(f"UPDATE holdings SET {sets} WHERE id=?", vals)
        conn.commit()
    finally:
        conn.close()


def upsert_holding_from_trade(ticker, name, shares_delta, price, trade_type):
    """Update or create holding based on a trade. Returns updated/created holding id."""
    conn = get_connection()
    try:
        now = now_iso()
        row = conn.execute("SELECT * FROM holdings WHERE ticker=?", (ticker,)).fetchone()
        if row is None:
            if trade_type == "BUY":
                cur = conn.execute(
                    "INSERT INTO holdings (ticker, name, shares, avg_cost, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                    (ticker, name, shares_delta, price, None, now, now)
                )
                conn.commit()
                return cur.lastrowid
            return None
        else:
            holding = dict(row)
            if trade_type == "BUY":
                old_cost = holding["avg_cost"] * holding["shares"]
                new_shares = holding["shares"] + shares_delta
                new_avg = (old_cost + price * shares_delta) / new_shares if new_shares > 0 else price
                conn.execute(
                    "UPDATE holdings SET shares=?, avg_cost=?, updated_at=?, name=COALESCE(?, name) WHERE ticker=?",
                    (new_shares, new_avg, now, name, ticker)
                )
            else:  # SELL
                new_shares = holding["shares"] - shares_delta
                if new_shares <= 0:
                    conn.execute("DELETE FROM holdings WHERE ticker=?", (ticker,))
                else:
                    conn.execute(
                        "UPDATE holdings SET shares=?, updated_at=? WHERE ticker=?",
                        (new_shares, now, ticker)
                    )
            conn.commit()
            return holding["id"]
    finally:
        conn.close()


def delete_holding(id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM holdings WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()


# ---------- Trades ----------

def get_all_trades():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM trades ORDER BY trade_date DESC, created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_trade(ticker, trade_type, shares, price, fee, trade_date, notes, realized_pnl):
    conn = get_connection()
    try:
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO trades (ticker, trade_type, shares, price, fee, trade_date, notes, realized_pnl, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (ticker, trade_type, shares, price, fee, trade_date, notes, realized_pnl, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_trade(id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM trades WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()


# ---------- Watchlist ----------

def get_all_watchlist():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM watchlist ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_watchlist(ticker, name, target_price, category, notes):
    conn = get_connection()
    try:
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO watchlist (ticker, name, target_price, category, notes, created_at) VALUES (?,?,?,?,?,?)",
            (ticker, name, target_price, category, notes, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_watchlist(id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM watchlist WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()


# ---------- Events ----------

def get_all_events():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM events ORDER BY event_date ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_upcoming_events(days=30):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE event_date >= date('now') AND event_date <= date('now', '+' || ? || ' days') ORDER BY event_date ASC",
            (days,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_event(ticker, event_type, event_date, description):
    conn = get_connection()
    try:
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO events (ticker, event_type, event_date, description, created_at) VALUES (?,?,?,?,?)",
            (ticker, event_type, event_date, description, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_event(id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM events WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()
