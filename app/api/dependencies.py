from fastapi import Header, HTTPException
from app.core.config import get_settings

async def require_admin_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_api_key
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid admin API key")

