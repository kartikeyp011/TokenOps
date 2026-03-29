"""
FastAPI shared dependencies.
- API key authentication
- DB session injection
"""
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.config import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Validate the X-API-Key header.
    Returns 401 if missing or wrong.
    All dashboard/API endpoints require this.
    The proxy endpoint /v1/chat/completions also uses this.
    """
    if x_api_key != settings.tokentamer_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid or missing X-API-Key header. Check your TokenOps API key.",
            },
        )
    return x_api_key


# Re-export get_db for convenience — routes import from here
__all__ = ["verify_api_key", "get_db"]