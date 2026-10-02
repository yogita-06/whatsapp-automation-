from app.repositories.store import Store
class FollowUpService:
    def __init__(self, store: Store): self.store = store
    async def get_due_followups(self) -> list[dict]:
        """Return queued follow-ups. Sending must enforce Meta's service window/template rules."""
        return await self.store.db.all("SELECT * FROM conversations WHERE follow_up_status='pending' AND follow_up_due_at <= CURRENT_TIMESTAMP")

