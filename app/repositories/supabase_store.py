import asyncio
from datetime import datetime, timezone
from app.models.conversation import ConversationState

class SupabaseStore:
    """Repository using Supabase's PostgREST client; blocking SDK calls run off-loop."""
    def __init__(self, client): self.client = client
    async def _run(self, fn): return await asyncio.to_thread(fn)
    async def get_or_create_session(self, phone: str) -> tuple[dict, dict]:
        result = await self._run(lambda: self.client.table("contacts").select("*").eq("phone_number", phone).limit(1).execute())
        if result.data: contact = result.data[0]
        else: contact = (await self._run(lambda: self.client.table("contacts").insert({"phone_number":phone}).execute())).data[0]
        result = await self._run(lambda: self.client.table("conversations").select("*").eq("contact_id", contact["id"]).limit(1).execute())
        if result.data: conv = result.data[0]
        else: conv = (await self._run(lambda: self.client.table("conversations").insert({"contact_id":contact["id"]}).execute())).data[0]
        conv["draft"] = conv.get("draft") or {}; return contact, conv
    async def update_conversation(self, contact_id, state: ConversationState, draft: dict, enabled: bool = True):
        values = {"current_state":state.value,"draft":draft,"automation_enabled":enabled,"last_customer_message_at":datetime.now(timezone.utc).isoformat(),"updated_at":datetime.now(timezone.utc).isoformat()}
        await self._run(lambda: self.client.table("conversations").update(values).eq("contact_id",contact_id).execute())
    async def update_name(self, contact_id, name: str): await self._run(lambda: self.client.table("contacts").update({"name":name}).eq("id",contact_id).execute())
    async def message_exists(self, message_id: str) -> bool:
        result = await self._run(lambda: self.client.table("messages").select("id").eq("whatsapp_message_id",message_id).limit(1).execute()); return bool(result.data)
    async def add_message(self, contact_id, message_id, direction: str, kind: str, content: str):
        data={"contact_id":contact_id,"whatsapp_message_id":message_id,"direction":direction,"message_type":kind,"content":content}
        await self._run(lambda: self.client.table("messages").insert(data).execute())
    async def create_appointment(self, contact: dict, draft: dict, request_key: str):
        data={"contact_id":contact["id"],"request_key":request_key,"name":draft["name"],"phone_number":contact["phone_number"],"treatment":draft["treatment"],"preferred_date":draft["date"],"preferred_time":draft["time"],"status":"requested"}
        await self._run(lambda: self.client.table("appointments").upsert(data,on_conflict="request_key").execute())
    async def reset(self, phone: str):
        contact,_=await self.get_or_create_session(phone); await self.update_conversation(contact["id"],ConversationState.MAIN_MENU,{},True)
    async def list_table(self, table: str) -> list[dict]:
        if table not in {"contacts","conversations","messages","appointments"}: raise ValueError("Invalid table")
        rows=(await self._run(lambda:self.client.table(table).select("*").order("created_at",desc=True).execute())).data
        if table=="conversations":
            for row in rows: row.pop("draft",None)
        return rows
    async def stats(self) -> dict:
        contacts,conversations,appointments,handoffs=await asyncio.gather(
            self._run(lambda:self.client.table("contacts").select("id",count="exact").execute()),
            self._run(lambda:self.client.table("conversations").select("id",count="exact").execute()),
            self._run(lambda:self.client.table("appointments").select("id",count="exact").execute()),
            self._run(lambda:self.client.table("conversations").select("id",count="exact").eq("current_state","WAITING_FOR_HUMAN").execute()))
        return {"contacts":contacts.count or 0,"conversations":conversations.count or 0,"appointment_requests":appointments.count or 0,"human_handoffs":handoffs.count or 0}

