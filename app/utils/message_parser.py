from app.models.whatsapp import IncomingMessage
from app.utils.phone import normalize_phone

def parse_webhook_messages(payload: dict) -> list[IncomingMessage]:
    result: list[IncomingMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                phone = message.get("from")
                message_id = message.get("id")
                if not phone or not message_id:
                    continue
                kind = message.get("type", "unknown")
                text, interactive_id = "", None
                if kind == "text":
                    text = message.get("text", {}).get("body", "")
                elif kind == "interactive":
                    interactive = message.get("interactive", {})
                    reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
                    interactive_id = reply.get("id")
                    text = reply.get("title") or interactive_id or ""
                result.append(IncomingMessage(message_id=message_id, sender_phone=normalize_phone(phone), message_type=kind, text=text[:2000], interactive_id=interactive_id, timestamp=message.get("timestamp")))
    return result

