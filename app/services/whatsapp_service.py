import httpx
from app.core.config import Settings, get_settings

class WhatsAppError(RuntimeError): pass

class WhatsAppService:
    def __init__(self, settings: Settings | None = None): self.settings = settings or get_settings()
    @property
    def endpoint(self) -> str:
        return f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/{self.settings.whatsapp_phone_number_id}/messages"
    async def _send(self, payload: dict) -> dict:
        if self.settings.demo_mode: return {"demo": True}
        if not self.settings.whatsapp_access_token or not self.settings.whatsapp_phone_number_id: raise WhatsAppError("WhatsApp credentials are not configured")
        headers = {"Authorization": f"Bearer {self.settings.whatsapp_access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
        if response.is_error: raise WhatsAppError(f"Meta API returned HTTP {response.status_code}")
        return response.json()
    async def send_text_message(self, to: str, text: str) -> dict:
        return await self._send({"messaging_product": "whatsapp", "to": to.lstrip("+"), "type": "text", "text": {"body": text}})
    async def send_interactive_buttons(self, to: str, body: str, buttons: list[dict]) -> dict:
        return await self._send({"messaging_product":"whatsapp","to":to.lstrip("+"),"type":"interactive","interactive":{"type":"button","body":{"text":body},"action":{"buttons":buttons}}})
    async def send_list_message(self, to: str, body: str, button: str, sections: list[dict]) -> dict:
        return await self._send({"messaging_product":"whatsapp","to":to.lstrip("+"),"type":"interactive","interactive":{"type":"list","body":{"text":body},"action":{"button":button,"sections":sections}}})
    async def mark_message_as_read(self, message_id: str) -> dict:
        return await self._send({"messaging_product":"whatsapp","status":"read","message_id":message_id})
    async def send_template_message(self, to: str, template_name: str, language_code: str, components: list[dict] | None = None) -> dict:
        template = {"name":template_name,"language":{"code":language_code}}
        if components: template["components"] = components
        return await self._send({"messaging_product":"whatsapp","to":to.lstrip("+"),"type":"template","template":template})

