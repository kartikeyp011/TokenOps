"""
GET /api/usage
Returns 7-day usage breakdown by day and by model.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.db.database import get_db
from app.models.db_models import RequestLog
from app.utils.helpers import safe_divide
from app.utils.seed import ensure_seeded

router = APIRouter()


@router.get("/usage")
async def get_usage(db: Session = Depends(get_db)):
    ensure_seeded(db)

    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    logs = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= seven_days_ago)
        .all()
    )

    # Daily breakdown — last 7 days
    daily: dict[str, dict] = {}
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily[day] = {
            "date": day,
            "requests": 0,
            "cost": 0.0,
            "cost_saved": 0.0,
            "cache_hits": 0,
            "errors": 0,
        }

    for r in logs:
        day = r.timestamp.strftime("%Y-%m-%d")
        if day not in daily:
            continue
        daily[day]["requests"] += 1
        if r.status == "success":
            daily[day]["cost"] = round(daily[day]["cost"] + r.estimated_cost_usd, 6)
            daily[day]["cost_saved"] = round(daily[day]["cost_saved"] + r.cost_saved_usd, 6)
        if r.is_cached:
            daily[day]["cache_hits"] += 1
        if r.status == "error":
            daily[day]["errors"] += 1

    # Model breakdown
    model_stats: dict[str, dict] = {}
    for r in logs:
        m = r.model_used
        if m not in model_stats:
            model_stats[m] = {
                "model": m,
                "provider": r.provider,
                "requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
            }
        model_stats[m]["requests"] += 1
        model_stats[m]["total_cost"] = round(
            model_stats[m]["total_cost"] + r.estimated_cost_usd, 6
        )
        model_stats[m]["total_tokens"] += r.total_tokens or 0

    # Add avg_cost_per_req
    for m in model_stats.values():
        m["avg_cost_per_req"] = round(
            safe_divide(m["total_cost"], m["requests"]), 8
        )

    # Totals
    all_success = [r for r in logs if r.status == "success"]
    total_tokens = sum(r.total_tokens or 0 for r in logs)
    total_latency = sum(r.latency_ms or 0 for r in all_success)

    return {
        "period": "last_7_days",
        "daily_usage": list(daily.values()),
        "model_breakdown": sorted(
            model_stats.values(), key=lambda x: x["requests"], reverse=True
        ),
        "total_requests": len(logs),
        "total_cost_usd": round(sum(r.estimated_cost_usd for r in all_success), 6),
        "total_tokens_processed": total_tokens,
        "avg_latency_ms": round(safe_divide(total_latency, len(all_success))),
        "total_cost_saved_usd": round(sum(r.cost_saved_usd for r in all_success), 6),
    }