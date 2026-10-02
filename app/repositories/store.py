import json
from datetime import datetime, timezone
from app.database.local import LocalDatabase, db
from app.models.conversation import ConversationState

class Store:
    def __init__(self, database: LocalDatabase = db): self.db = database
    async def get_or_create_session(self, phone: str) -> tuple[dict, dict]:
        contact = await self.db.one("SELECT * FROM contacts WHERE phone_number=?", (phone,))
        if not contact:
            cid = await self.db.execute("INSERT INTO contacts(phone_number) VALUES(?)", (phone,)); contact = await self.db.one("SELECT * FROM contacts WHERE id=?", (cid,))
        conv = await self.db.one("SELECT * FROM conversations WHERE contact_id=?", (contact["id"],))
        if not conv:
            await self.db.execute("INSERT INTO conversations(contact_id) VALUES(?)", (contact["id"],)); conv = await self.db.one("SELECT * FROM conversations WHERE contact_id=?", (contact["id"],))
        conv["draft"] = json.loads(conv.get("draft") or "{}")
        conv["automation_enabled"] = bool(conv["automation_enabled"])
        return contact, conv
    async def update_conversation(self, contact_id: int, state: ConversationState, draft: dict, enabled: bool = True):
        await self.db.execute("UPDATE conversations SET current_state=?, draft=?, automation_enabled=?, last_customer_message_at=?, updated_at=CURRENT_TIMESTAMP WHERE contact_id=?", (state.value, json.dumps(draft), int(enabled), datetime.now(timezone.utc).isoformat(), contact_id))
    async def update_name(self, contact_id: int, name: str):
        await self.db.execute("UPDATE contacts SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (name, contact_id))
    async def message_exists(self, message_id: str) -> bool:
        return bool(await self.db.one("SELECT id FROM messages WHERE whatsapp_message_id=?", (message_id,)))
    async def add_message(self, contact_id: int, message_id: str | None, direction: str, kind: str, content: str):
        await self.db.execute("INSERT OR IGNORE INTO messages(contact_id,whatsapp_message_id,direction,message_type,content) VALUES(?,?,?,?,?)", (contact_id, message_id, direction, kind, content))
    async def create_appointment(self, contact: dict, draft: dict, request_key: str):
        await self.db.execute("INSERT OR IGNORE INTO appointments(contact_id,request_key,name,phone_number,treatment,preferred_date,preferred_time) VALUES(?,?,?,?,?,?,?)", (contact["id"], request_key, draft["name"], contact["phone_number"], draft["treatment"], draft["date"], draft["time"]))
    async def reset(self, phone: str):
        contact, _ = await self.get_or_create_session(phone); await self.update_conversation(contact["id"], ConversationState.MAIN_MENU, {}, True)
    async def list_table(self, table: str) -> list[dict]:
        allowed = {"contacts", "conversations", "messages", "appointments"}
        if table not in allowed: raise ValueError("Invalid table")
        rows = await self.db.all(f"SELECT * FROM {table} ORDER BY id DESC")
        for row in rows:
            if table == "conversations": row.pop("draft", None)
        return rows
    async def stats(self) -> dict:
        async def count(table: str, where: str = "1=1"):
            row = await self.db.one(f"SELECT COUNT(*) count FROM {table} WHERE {where}"); return row["count"]
        return {"contacts":await count("contacts"),"conversations":await count("conversations"),"appointment_requests":await count("appointments"),"human_handoffs":await count("conversations", "current_state='WAITING_FOR_HUMAN'")}
