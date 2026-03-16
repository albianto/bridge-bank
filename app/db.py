import sqlite3
import os

DB_PATH = "/data/instance.db"

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT DEFAULT (datetime('now')),
            status TEXT,
            tx_count INTEGER DEFAULT 0,
            message TEXT
        )
    """)
    conn.commit()

def get_setting(key: str) -> str:
    with _conn() as conn:
        _ensure_tables(conn)
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else ""

def set_setting(key: str, value: str):
    with _conn() as conn:
        _ensure_tables(conn)
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        conn.commit()

def log_sync(status: str, tx_count: int = 0, message: str = ""):
    with _conn() as conn:
        _ensure_tables(conn)
        conn.execute(
            "INSERT INTO sync_log (status, tx_count, message) VALUES (?, ?, ?)",
            (status, tx_count, message)
        )
        conn.commit()

def get_recent_syncs(limit: int = 15) -> list:
    with _conn() as conn:
        _ensure_tables(conn)
        rows = conn.execute(
            "SELECT ran_at, status, tx_count, message FROM sync_log ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_last_sync() -> str:
    with _conn() as conn:
        _ensure_tables(conn)
        row = conn.execute(
            "SELECT ran_at FROM sync_log WHERE status = 'success' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["ran_at"] if row else ""
