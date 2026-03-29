"""
GET /api/logs
Returns paginated request logs with optional filters.
Query params: page, page_size, status, provider, model
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_models import RequestLog
from app.utils.seed import ensure_seeded

router = APIRouter()


@router.get("/logs")
async def get_logs(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    status: str = Query(default=None),
    provider: str = Query(default=None),
    model: str = Query(default=None),
):
    ensure_seeded(db)

    query = db.query(RequestLog)

    # Apply filters
    if status:
        query = query.filter(RequestLog.status == status)
    if provider:
        query = query.filter(RequestLog.provider == provider)
    if model:
        query = query.filter(RequestLog.model_used == model)

    total = query.count()
    offset = (page - 1) * page_size

    rows = (
        query.order_by(RequestLog.timestamp.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    logs = []
    for r in rows:
        logs.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "prompt_preview": r.prompt_preview or "",
            "model_requested": r.model_requested or "",
            "model_used": r.model_used,
            "provider": r.provider,
            "routing_decision": r.routing_decision,
            "routing_reason": r.routing_reason or "",
            "estimated_cost_usd": r.estimated_cost_usd,
            "cost_saved_usd": r.cost_saved_usd,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "is_cached": r.is_cached,
            "is_mock": r.is_mock,
            "response_preview": r.response_preview or "",
            "error_message": r.error_message or "",
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "logs": logs,
        "filters_applied": {
            "status": status,
            "provider": provider,
            "model": model,
        },
    }