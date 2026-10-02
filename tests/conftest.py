import os
os.environ.update({"DEMO_MODE":"true","ADMIN_API_KEY":"test-key","WHATSAPP_VERIFY_TOKEN":"verify-me","LOCAL_DATABASE_PATH":":memory:"})
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest_asyncio.fixture
async def client(tmp_path):
    from app.database.local import LocalDatabase
    from app.repositories.store import Store
    from app.services.automation_service import AutomationService
    from app.services.whatsapp_service import WhatsAppService
    database = LocalDatabase(str(tmp_path / "test.db")); await database.initialize()
    app.state.store = Store(database); app.state.automation = AutomationService(app.state.store); app.state.whatsapp = WhatsAppService()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c: yield c
