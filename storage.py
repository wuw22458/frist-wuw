import os
import sqlite3
import time
from datetime import datetime, timedelta

from config import get_app_dir, load_config


DB_PATH = os.path.join(get_app_dir(), "history.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            content TEXT,
            image_path TEXT,
            created_at REAL NOT NULL,
            is_pinned INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at
        ON clipboard_items(created_at DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_is_pinned
        ON clipboard_items(is_pinned)
    """)
    conn.commit()
    conn.close()


def add_item(content_type, content=None, image_path=None):
    conn = get_conn()
    now = time.time()
    conn.execute(
        "INSERT INTO clipboard_items (content_type, content, image_path, created_at) VALUES (?, ?, ?, ?)",
        (content_type, content, image_path, now),
    )
    conn.commit()

    # 检查上限
    cfg = load_config()
    max_items = cfg.get("max_items", 500)
    conn.execute("""
        DELETE FROM clipboard_items WHERE id NOT IN (
            SELECT id FROM clipboard_items ORDER BY is_pinned DESC, created_at DESC LIMIT ?
        )
    """, (max_items,))
    conn.commit()
    conn.close()


def get_items(search_text=None, limit=None):
    conn = get_conn()
    if search_text:
        query = """
            SELECT id, content_type, content, image_path, created_at, is_pinned
            FROM clipboard_items
            WHERE content LIKE ?
            ORDER BY is_pinned DESC, created_at DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query, (f"%{search_text}%",)).fetchall()
    else:
        query = """
            SELECT id, content_type, content, image_path, created_at, is_pinned
            FROM clipboard_items
            ORDER BY is_pinned DESC, created_at DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def get_item_by_id(item_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, content_type, content, image_path, created_at, is_pinned FROM clipboard_items WHERE id = ?",
        (item_id,),
    ).fetchone()
    conn.close()
    return row


def toggle_pin(item_id):
    conn = get_conn()
    conn.execute("""
        UPDATE clipboard_items SET is_pinned = CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (item_id,))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_conn()
    row = conn.execute("SELECT image_path FROM clipboard_items WHERE id = ?", (item_id,)).fetchone()
    if row and row[0] and os.path.exists(row[0]):
        try:
            os.remove(row[0])
        except Exception:
            pass
    conn.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def cleanup_expired():
    cfg = load_config()
    days = cfg.get("retention_days", 3)
    cutoff = time.time() - (days * 24 * 3600)
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, image_path FROM clipboard_items WHERE is_pinned = 0 AND created_at < ?",
        (cutoff,),
    ).fetchall()
    for row in rows:
        if row[1] and os.path.exists(row[1]):
            try:
                os.remove(row[1])
            except Exception:
                pass
    conn.execute("DELETE FROM clipboard_items WHERE is_pinned = 0 AND created_at < ?", (cutoff,))
    conn.commit()
    conn.close()
