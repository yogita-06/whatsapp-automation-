from fastapi import APIRouter, HTTPException, Request
from app.core.config import get_settings
from app.models.whatsapp import DemoMessageRequest
from app.utils.phone import normalize_phone

router = APIRouter(prefix="/demo", tags=["Demo"])
@router.post("/message", summary="Run one local automation turn")
async def demo_message(body: DemoMessageRequest, request: Request):
    if not get_settings().demo_mode: raise HTTPException(404, "Demo mode is disabled")
    try: phone = normalize_phone(body.phone)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    reply, state, _ = await request.app.state.automation.process(phone, body.message)
    return {"reply":reply,"state":state.value}

