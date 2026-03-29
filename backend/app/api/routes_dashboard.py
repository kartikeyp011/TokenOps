"""
GET /api/dashboard
Returns aggregated KPIs, sparkline data, and provider breakdown.
Hybrid: real data from DB if available, else seeded realistic data.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.db.database import get_db
from app.models.db_models import RequestLog, AlertRecord
from app.core.cache import cache
from app.utils.helpers import safe_divide, time_bucket_label
from app.utils.seed import ensure_seeded

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    ensure_seeded(db)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    # Today's logs
    today_logs = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= today_start)
        .all()
    )

    total_requests_today = len(today_logs)
    successful = [r for r in today_logs if r.status == "success"]
    total_cost_today = round(sum(r.estimated_cost_usd for r in successful), 6)
    total_saved_today = round(sum(r.cost_saved_usd for r in successful), 6)
    cached_hits = sum(1 for r in today_logs if r.is_cached)

    # Top model used today
    model_counts = {}
    for r in successful:
        model_counts[r.model_used] = model_counts.get(r.model_used, 0) + 1
    top_model = max(model_counts, key=model_counts.get) if model_counts else "none"

    # Active alerts
    active_alerts = (
        db.query(AlertRecord)
        .filter(AlertRecord.resolved == False)
        .count()
    )

    # Cache hit rate from in-memory cache
    cache_stats = cache.stats()

    # Sparkline: requests per 5-min bucket over last hour
    hour_logs = [r for r in today_logs if r.timestamp >= one_hour_ago]
    buckets: dict[str, int] = {}
    for r in hour_logs:
        label = time_bucket_label(r.timestamp, 5)
        buckets[label] = buckets.get(label, 0) + 1

    # Fill in all 12 five-minute buckets for the last hour
    sparkline = []
    for i in range(11, -1, -1):
        bucket_time = now - timedelta(minutes=i * 5)
        label = time_bucket_label(bucket_time, 5)
        sparkline.append({"time": label, "requests": buckets.get(label, 0)})

    # Provider breakdown
    provider_stats = {}
    for r in successful:
        p = r.provider
        if p not in provider_stats:
            provider_stats[p] = {"count": 0, "cost": 0.0}
        provider_stats[p]["count"] += 1
        provider_stats[p]["cost"] = round(provider_stats[p]["cost"] + r.estimated_cost_usd, 6)

    return {
        "total_requests_today": total_requests_today,
        "total_cost_today_usd": total_cost_today,
        "cost_saved_today_usd": total_saved_today,
        "cache_hit_rate_pct": cache_stats["hit_rate_pct"],
        "active_alerts_count": active_alerts,
        "top_model_used": top_model,
        "daily_budget_cap_usd": 5.0,
        "budget_used_pct": round(safe_divide(total_cost_today, 5.0) * 100, 1),
        "requests_last_hour": sparkline,
        "provider_breakdown": provider_stats,
        "cache_stats": cache_stats,
        "seeded": False,
    }