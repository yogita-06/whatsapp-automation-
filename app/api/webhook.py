import hashlib, hmac, logging
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from app.core.config import get_settings
from app.utils.message_parser import parse_webhook_messages

router = APIRouter(tags=["Webhook"])
log = logging.getLogger(__name__)

def verify_meta_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret or not signature.startswith("sha256="): return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)

@router.get("/webhook", summary="Verify Meta webhook")
async def verify_webhook(hub_mode: str | None = Query(None, alias="hub.mode"), hub_verify_token: str | None = Query(None, alias="hub.verify_token"), hub_challenge: str | None = Query(None, alias="hub.challenge")):
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token and hub_challenge is not None:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(403, "Webhook verification failed")

@router.post("/webhook", summary="Receive Meta WhatsApp events", status_code=200)
async def receive_webhook(request: Request):
    settings = get_settings(); body = await request.body()
    if settings.signature_required and not verify_meta_signature(body, request.headers.get("X-Hub-Signature-256"), settings.meta_app_secret):
        raise HTTPException(401, "Invalid webhook signature")
    try: payload = __import__("json").loads(body)
    except Exception as exc: raise HTTPException(400, "Malformed JSON payload") from exc
    try: messages = parse_webhook_messages(payload)
    except (TypeError, ValueError):
        log.warning("Ignoring malformed webhook event"); return {"status":"ignored"}
    for incoming in messages:
        try:
            reply, _, duplicate = await request.app.state.automation.process(incoming.sender_phone, incoming.text, incoming.message_id, incoming.message_type)
            if duplicate or not reply: continue
            await request.app.state.whatsapp.send_text_message(incoming.sender_phone, reply)
        except Exception:
            log.exception("Failed to process webhook message")
    return {"status":"received"}

