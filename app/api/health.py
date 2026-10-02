from fastapi import APIRouter
router = APIRouter(tags=["Health"])
@router.get("/", summary="Service information")
async def root(): return {"service":"WhatsApp Dental Automation","status":"running"}
@router.get("/health", summary="Health check")
async def health(): return {"status":"healthy"}

