from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from typing import Any

from src.config import Settings


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ChatRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def init(self) -> None:
        _ensure_parent(self.settings.db_path)
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_profiles (
                    phone TEXT PRIMARY KEY,
                    name TEXT,
                    language TEXT,
                    summary_text TEXT,
                    opted_out INTEGER NOT NULL DEFAULT 0,
                    last_seen_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY,
                    phone TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_phone_created ON chat_messages(phone, id)")
            cols = [r[1] for r in conn.execute("PRAGMA table_info(chat_profiles)").fetchall()]
            if "summary_text" not in cols:
                conn.execute("ALTER TABLE chat_profiles ADD COLUMN summary_text TEXT")
            if "opted_out" not in cols:
                conn.execute("ALTER TABLE chat_profiles ADD COLUMN opted_out INTEGER NOT NULL DEFAULT 0")
            conn.commit()

    def mark_message_processed(self, message_id: str, phone: str) -> bool:
        with _connect(self.settings.db_path) as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO processed_messages (message_id, phone, created_at) VALUES (?, ?, ?)",
                (message_id, phone, now_iso()),
            )
            conn.commit()
        return cur.rowcount > 0

    def set_opted_out(self, phone: str) -> None:
        ts = now_iso()
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chat_profiles (phone, opted_out, updated_at, last_seen_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET
                  opted_out=1,
                  updated_at=excluded.updated_at,
                  last_seen_at=excluded.last_seen_at
                """,
                (phone, ts, ts),
            )
            conn.commit()

    def is_opted_out(self, phone: str) -> bool:
        with _connect(self.settings.db_path) as conn:
            row = conn.execute("SELECT opted_out FROM chat_profiles WHERE phone=?", (phone,)).fetchone()
        return bool(row and row[0])

    def append_memory(self, phone: str, role: str, content: str) -> None:
        ts = str(time.time())
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                "INSERT INTO chat_messages (phone, role, content, created_at) VALUES (?, ?, ?, ?)",
                (phone, role, content, ts),
            )
            conn.execute(
                """
                INSERT INTO chat_profiles (phone, updated_at, last_seen_at)
                VALUES (?, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET
                  updated_at=excluded.updated_at,
                  last_seen_at=excluded.last_seen_at
                """,
                (phone, ts, ts),
            )
            conn.execute(
                """
                DELETE FROM chat_messages
                WHERE phone = ?
                  AND id NOT IN (
                    SELECT id FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT ?
                  )
                """,
                (phone, phone, self.settings.max_history_messages * 4),
            )
            summary = self._build_summary(conn, phone)
            conn.execute("UPDATE chat_profiles SET summary_text=?, updated_at=? WHERE phone=?", (summary, ts, phone))
            conn.commit()

    def get_profile_summary(self, phone: str) -> str:
        with _connect(self.settings.db_path) as conn:
            row = conn.execute("SELECT summary_text FROM chat_profiles WHERE phone=?", (phone,)).fetchone()
        if not row:
            return ""
        return (row[0] or "").strip()

    def get_history(self, phone: str) -> list[dict[str, str]]:
        with _connect(self.settings.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT role, content FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT ?",
                (phone, self.settings.max_history_messages),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    @staticmethod
    def _build_summary(conn: sqlite3.Connection, phone: str) -> str:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT 16",
            (phone,),
        ).fetchall()
        user_points: list[str] = []
        assistant_points: list[str] = []
        for role, content in reversed(rows):
            clean = (content or "").strip().replace("\n", " ")
            if not clean:
                continue
            if role == "user" and len(user_points) < 8:
                user_points.append(clean[:140])
            if role == "assistant" and len(assistant_points) < 4:
                assistant_points.append(clean[:140])
        parts = []
        if user_points:
            parts.append("Cliente disse: " + " | ".join(user_points))
        if assistant_points:
            parts.append("Bot respondeu: " + " | ".join(assistant_points))
        return " || ".join(parts)[:1200]


class MarketingRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def init(self) -> None:
        _ensure_parent(self.settings.db_path)
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_customers (
                    phone TEXT PRIMARY KEY,
                    name TEXT,
                    status TEXT NOT NULL DEFAULT 'idle',
                    current_sequence_id TEXT,
                    current_step INTEGER DEFAULT 0,
                    last_product_bought TEXT,
                    next_send_at TEXT,
                    last_purchase_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id TEXT,
                    phone TEXT NOT NULL,
                    product TEXT NOT NULL,
                    approved_at TEXT,
                    raw_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_marketing_purchase_unique
                ON marketing_purchases(purchase_id, phone, product)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    sequence_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    provider_status TEXT,
                    provider_message_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_customer_after_purchase(
        self,
        phone: str,
        name: str | None,
        product: str,
        approved_at: str | None,
        sequence: dict[str, Any] | None,
    ) -> None:
        ts = now_iso()
        purchase_dt = approved_at or ts
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                INSERT INTO marketing_customers (phone, name, status, current_sequence_id, current_step, last_product_bought, next_send_at, last_purchase_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET
                  name=excluded.name,
                  status=excluded.status,
                  current_sequence_id=excluded.current_sequence_id,
                  current_step=excluded.current_step,
                  last_product_bought=excluded.last_product_bought,
                  next_send_at=excluded.next_send_at,
                  last_purchase_at=excluded.last_purchase_at,
                  updated_at=excluded.updated_at
                """,
                (
                    phone,
                    name,
                    "active" if sequence else "idle",
                    sequence.get("id") if sequence else None,
                    0,
                    product,
                    ts if sequence else None,
                    purchase_dt,
                    ts,
                ),
            )
            conn.commit()

    def save_purchase(self, purchase_id: str | None, phone: str, product: str, approved_at: str | None, raw_payload: dict[str, Any]) -> None:
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO marketing_purchases (purchase_id, phone, product, approved_at, raw_payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (purchase_id, phone, product, approved_at, json.dumps(raw_payload, ensure_ascii=False), now_iso()),
            )
            conn.commit()

    def get_due_customers(self, limit: int = 50) -> list[sqlite3.Row]:
        with _connect(self.settings.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM marketing_customers
                WHERE status = 'active'
                  AND current_sequence_id IS NOT NULL
                  AND next_send_at IS NOT NULL
                  AND datetime(next_send_at) <= datetime(?)
                ORDER BY datetime(next_send_at) ASC
                LIMIT ?
                """,
                (now_iso(), limit),
            ).fetchall()
        return rows

    def update_customer_state(self, phone: str, *, step: int, next_send_at: str | None, status: str) -> None:
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                "UPDATE marketing_customers SET current_step=?, next_send_at=?, status=?, updated_at=? WHERE phone=?",
                (step, next_send_at, status, now_iso(), phone),
            )
            conn.commit()

    def store_message_log(self, phone: str, sequence_id: str, step_index: int, text: str, provider_status: str, provider_message_id: str | None) -> None:
        with _connect(self.settings.db_path) as conn:
            conn.execute(
                """
                INSERT INTO marketing_messages (phone, sequence_id, step_index, text, provider_status, provider_message_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (phone, sequence_id, step_index, text, provider_status, provider_message_id, now_iso()),
            )
            conn.commit()

    def already_sent_marketing_today(self, phone: str, day_start_iso: str) -> bool:
        with _connect(self.settings.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM marketing_messages WHERE phone = ? AND datetime(created_at) >= datetime(?)",
                (phone, day_start_iso),
            ).fetchone()
        return bool(row and row[0] > 0)

    def stats(self) -> dict[str, int]:
        with _connect(self.settings.db_path) as conn:
            return {
                "customers_total": conn.execute("SELECT COUNT(*) FROM marketing_customers").fetchone()[0],
                "customers_active": conn.execute("SELECT COUNT(*) FROM marketing_customers WHERE status='active'").fetchone()[0],
                "customers_waiting_purchase": conn.execute("SELECT COUNT(*) FROM marketing_customers WHERE status='waiting_purchase'").fetchone()[0],
                "purchases_total": conn.execute("SELECT COUNT(*) FROM marketing_purchases").fetchone()[0],
                "messages_sent_total": conn.execute("SELECT COUNT(*) FROM marketing_messages").fetchone()[0],
            }
