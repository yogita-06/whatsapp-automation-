from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.dependencies import require_admin_key
from app.models.conversation import ConversationState
from app.utils.phone import normalize_phone

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin_key)])

@router.get("/leads")
async def leads(request: Request): return await request.app.state.store.list_table("contacts")
@router.get("/appointments")
async def appointments(request: Request): return await request.app.state.store.list_table("appointments")
@router.get("/conversations")
async def conversations(request: Request): return await request.app.state.store.list_table("conversations")
@router.get("/messages")
async def messages(request: Request): return await request.app.state.store.list_table("messages")
@router.get("/conversations/{phone}")
async def conversation(phone: str, request: Request):
    try: contact, conv = await request.app.state.store.get_or_create_session(normalize_phone(phone))
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    return {"contact":contact,"conversation":conv}
@router.post("/conversations/{phone}/resume")
async def resume(phone: str, request: Request):
    contact, _ = await request.app.state.store.get_or_create_session(normalize_phone(phone))
    await request.app.state.store.update_conversation(contact["id"], ConversationState.MAIN_MENU, {}, True)
    return {"status":"resumed","state":"MAIN_MENU"}
@router.post("/conversations/{phone}/reset")
async def reset(phone: str, request: Request):
    await request.app.state.store.reset(normalize_phone(phone)); return {"status":"reset","state":"MAIN_MENU"}
@router.get("/stats")
async def stats(request: Request):
    return await request.app.state.store.stats()
