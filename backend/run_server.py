"""
TokenOps server entry point.
Run with: python run_server.py
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 50)
    print("  TokenOps Backend")
    print("=" * 50)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )