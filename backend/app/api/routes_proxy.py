"""
Proxy route stub — real logic added in Phase 5.
POST /v1/chat/completions
"""
from fastapi import APIRouter, Depends
from app.dependencies import verify_api_key

router = APIRouter(tags=["Proxy"])


@router.post("/v1/chat/completions")
async def proxy_chat(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """Stub — will be replaced with full proxy logic in Phase 5."""
    return {
        "stub": True,
        "message": "Proxy endpoint stub. Full logic coming in Phase 5.",
        "received": request
    }