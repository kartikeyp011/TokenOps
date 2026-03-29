"""
Audit logger — writes every request and alert to the database.
All functions are synchronous (SQLite doesn't need async).
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.db_models import RequestLog, AlertRecord
from app.utils.helpers import truncate_text, make_dedup_key


def log_request(
    db: Session,
    prompt: str,
    model_requested: str,
    model_used: str,
    provider: str,
    routing_decision: str,
    routing_reason: str,
    estimated_cost_usd: float,
    cost_saved_usd: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    status: str = "success",
    error_message: str = None,
    latency_ms: int = 0,
    is_cached: bool = False,
    is_mock: bool = False,
    response_preview: str = None,
) -> RequestLog:
    """Write a complete request record to the database."""
    entry = RequestLog(
        timestamp=datetime.now(timezone.utc),
        prompt=prompt,
        prompt_preview=truncate_text(prompt, 300),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        model_requested=model_requested or model_used,
        model_used=model_used,
        provider=provider,
        routing_decision=routing_decision,
        routing_reason=routing_reason,
        estimated_cost_usd=round(estimated_cost_usd, 8),
        cost_saved_usd=round(cost_saved_usd, 8),
        status=status,
        error_message=error_message,
        latency_ms=latency_ms,
        is_cached=is_cached,
        is_mock=is_mock,
        response_preview=truncate_text(response_preview or "", 300),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def log_alert(
    db: Session,
    alert_type: str,
    severity: str,
    message: str,
    deduplicate: bool = True,
) -> AlertRecord | None:
    """
    Write an alert to the database.
    If deduplicate=True, skip if same alert type was logged in the last 5 minutes.
    """
    dedup_key = make_dedup_key(alert_type, window_minutes=5)

    if deduplicate:
        existing = (
            db.query(AlertRecord)
            .filter(AlertRecord.dedup_key == dedup_key, AlertRecord.resolved == False)
            .first()
        )
        if existing:
            return None  # already logged, skip duplicate

    alert = AlertRecord(
        timestamp=datetime.now(timezone.utc),
        alert_type=alert_type,
        severity=severity,
        message=message,
        resolved=False,
        dedup_key=dedup_key,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert