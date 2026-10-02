import json
import aiosqlite
from app.core.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY AUTOINCREMENT, phone_number TEXT UNIQUE NOT NULL, name TEXT, email TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER UNIQUE NOT NULL, current_state TEXT NOT NULL DEFAULT 'NEW', automation_enabled INTEGER NOT NULL DEFAULT 1, draft TEXT NOT NULL DEFAULT '{}', last_customer_message_at TEXT, follow_up_due_at TEXT, follow_up_status TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(contact_id) REFERENCES contacts(id));
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER NOT NULL, whatsapp_message_id TEXT UNIQUE, direction TEXT NOT NULL CHECK(direction IN ('incoming','outgoing')), message_type TEXT NOT NULL, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(contact_id) REFERENCES contacts(id));
CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER NOT NULL, request_key TEXT UNIQUE NOT NULL, name TEXT NOT NULL, phone_number TEXT NOT NULL, treatment TEXT NOT NULL, preferred_date TEXT NOT NULL, preferred_time TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'requested', notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(contact_id) REFERENCES contacts(id));
"""

class LocalDatabase:
    def __init__(self, path: str | None = None): self.path = path or get_settings().local_database_path
    async def initialize(self):
        async with aiosqlite.connect(self.path) as db: await db.executescript(SCHEMA); await db.commit()
    async def execute(self, sql: str, params: tuple = ()) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(sql, params); await db.commit(); return cur.lastrowid
    async def one(self, sql: str, params: tuple = ()) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row; cur = await db.execute(sql, params); row = await cur.fetchone(); return dict(row) if row else None
    async def all(self, sql: str, params: tuple = ()) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row; cur = await db.execute(sql, params); return [dict(r) for r in await cur.fetchall()]

db = LocalDatabase()

