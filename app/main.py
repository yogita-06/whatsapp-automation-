from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import admin, demo, health, webhook
from app.core.logging import configure_logging
from app.database.local import db
from app.repositories.store import Store
from app.repositories.supabase_store import SupabaseStore
from app.database.supabase import get_supabase
from app.services.automation_service import AutomationService
from app.services.whatsapp_service import WhatsAppService

configure_logging()
@asynccontextmanager
async def lifespan(app: FastAPI):
    supabase = get_supabase()
    if supabase:
        app.state.store = SupabaseStore(supabase)
    else:
        await db.initialize()
        app.state.store = Store(db)
    app.state.automation = AutomationService(app.state.store)
    app.state.whatsapp = WhatsAppService()
    yield

app = FastAPI(title="WhatsApp Dental Automation", description="Rule-based WhatsApp Cloud API automation demo for a dental clinic.", version="1.0.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(demo.router)
app.include_router(admin.router)
