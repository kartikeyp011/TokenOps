"""
TokenOps — FastAPI application entry point.
Registers all routes, middleware, and startup events.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.db.database import init_db, get_db
from app.dependencies import verify_api_key
from app.core.proxy import handle_proxy_request, PolicyViolationError

# Import all route modules
from app.api import (
    routes_dashboard,
    routes_usage,
    routes_logs,
    routes_alerts,
    routes_policies,
)

# ─────────────────────────────────────────────
# App initialization
# ─────────────────────────────────────────────

app = FastAPI(
    title="TokenOps",
    description="Autonomous AI Cost Intelligence Agent — proxy, route, analyze, and optimize LLM spending.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS — allow frontend on any port during development
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Startup event — create DB tables
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    print("🚀 TokenOps starting up...")
    init_db()
    print("✅ Database initialized")
    print(f"🔑 API Key: {settings.tokentamer_api_key[:8]}...")
    print(f"🤖 Gemini available: {bool(settings.gemini_api_key)}")
    print(f"🤖 Groq available: {bool(settings.groq_api_key)}")
    print(f"📊 Routing strategy: {settings.routing_strategy}")
    print(f"💰 Daily budget cap: ${settings.daily_budget_cap_usd}")

# ─────────────────────────────────────────────
# Health check — no auth required
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.gemini_api_key),
        "groq_configured": bool(settings.groq_api_key),
        "mock_mode": not (bool(settings.gemini_api_key) or bool(settings.groq_api_key)),
    }

# ─────────────────────────────────────────────
# Proxy endpoint — POST /v1/chat/completions
# OpenAI-compatible. Requires X-API-Key header.
# ─────────────────────────────────────────────

@app.post("/v1/chat/completions", tags=["Proxy"])
async def proxy_chat_completions(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Drop-in OpenAI-compatible proxy endpoint.
    Analyzes, routes, caches, and logs every request automatically.

    Required header: X-API-Key: <your-tokentamer-key>

    Request body (OpenAI format):
    {
        "model": "llama3-8b-8192",   (optional — router will decide if omitted)
        "messages": [
            {"role": "user", "content": "Your prompt here"}
        ],
        "max_tokens": 1024
    }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_json", "message": "Request body must be valid JSON"},
        )

    try:
        response = await handle_proxy_request(request_body=body, db=db)
        return JSONResponse(content=response)

    except PolicyViolationError as e:
        return JSONResponse(
            status_code=403,
            content={
                "error": "policy_violation",
                "message": e.reason,
                "blocked_by": e.blocked_by,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Check server logs.",
            },
        )

# ─────────────────────────────────────────────
# Dashboard API routes
# All require X-API-Key header
# ─────────────────────────────────────────────

app.include_router(
    routes_dashboard.router,
    prefix="/api",
    tags=["Dashboard"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    routes_usage.router,
    prefix="/api",
    tags=["Usage"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    routes_logs.router,
    prefix="/api",
    tags=["Logs"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    routes_alerts.router,
    prefix="/api",
    tags=["Alerts"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    routes_policies.router,
    prefix="/api",
    tags=["Policies"],
    dependencies=[Depends(verify_api_key)],
)

# ─────────────────────────────────────────────
# Global error handlers
# ─────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": f"Route {request.url.path} not found"},
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal server error"},
    )

# ─────────────────────────────────────────────
# Serve frontend files
# ─────────────────────────────────────────────

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")