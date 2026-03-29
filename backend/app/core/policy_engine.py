"""
Policy enforcement engine.
All policies are config-driven — values come from settings or DB at runtime.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.models.db_models import RequestLog, PolicyConfig


@dataclass
class PolicyResult:
    allowed: bool
    reason: str
    blocked_by: str = None  # which policy blocked it


def _get_policy_value(db: Session, policy_name: str, default):
    """
    Read a policy value from DB if it exists, else fall back to default.
    This allows runtime policy updates via PUT /api/policies/{name}.
    """
    row = db.query(PolicyConfig).filter(PolicyConfig.policy_name == policy_name).first()
    if row:
        try:
            # Attempt numeric conversion
            val = row.policy_value
            if "." in val:
                return float(val)
            return int(val)
        except (ValueError, TypeError):
            return row.policy_value
    return default


def check_token_limit(db: Session, tokens: int) -> PolicyResult:
    """Block requests that exceed the token limit."""
    limit = _get_policy_value(db, "max_tokens_per_request", settings.max_tokens_per_request)
    if tokens > limit:
        return PolicyResult(
            allowed=False,
            reason=f"Prompt exceeds token limit: {tokens} tokens > {limit} limit",
            blocked_by="token_limit",
        )
    return PolicyResult(allowed=True, reason="Token limit OK")


def check_daily_budget(db: Session, estimated_cost: float) -> PolicyResult:
    """Block if adding this request would exceed today's daily budget cap."""
    cap = _get_policy_value(db, "daily_budget_cap_usd", settings.daily_budget_cap_usd)

    # Sum today's costs from request logs
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = (
        db.query(RequestLog)
        .filter(
            RequestLog.timestamp >= today_start,
            RequestLog.status == "success",
        )
        .all()
    )
    today_total = sum(r.estimated_cost_usd for r in result)

    if today_total + estimated_cost > cap:
        return PolicyResult(
            allowed=False,
            reason=f"Daily budget cap reached: ${today_total:.4f} spent + ${estimated_cost:.4f} new > ${cap} cap",
            blocked_by="daily_budget",
        )
    return PolicyResult(allowed=True, reason=f"Budget OK (${today_total:.4f} / ${cap} used today)")


def check_rate_limit(db: Session) -> PolicyResult:
    """Block if too many requests in the last 60 seconds."""
    limit = _get_policy_value(db, "rate_limit_rpm", settings.rate_limit_rpm)

    one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
    count = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= one_minute_ago)
        .count()
    )

    if count >= limit:
        return PolicyResult(
            allowed=False,
            reason=f"Rate limit exceeded: {count} requests in last 60s (limit: {limit})",
            blocked_by="rate_limit",
        )
    return PolicyResult(allowed=True, reason=f"Rate OK ({count}/{limit} rpm)")


def check_model_allowed(db: Session, model: str) -> PolicyResult:
    """Block if the requested model is not in the allowed list."""
    if not model:
        return PolicyResult(allowed=True, reason="No model specified, router will decide")

    allowed = settings.allowed_models
    if model not in allowed:
        return PolicyResult(
            allowed=False,
            reason=f"Model '{model}' is not in allowed list: {allowed}",
            blocked_by="model_restriction",
        )
    return PolicyResult(allowed=True, reason=f"Model '{model}' is allowed")


def run_all_checks(
    db: Session,
    model: str,
    tokens: int,
    estimated_cost: float,
) -> PolicyResult:
    """
    Run all policy checks in order. Returns the first failure, or pass.
    Order matters: token → rate → model → budget (cheapest checks first).
    """
    checks = [
        lambda: check_token_limit(db, tokens),
        lambda: check_rate_limit(db),
        lambda: check_model_allowed(db, model),
        lambda: check_daily_budget(db, estimated_cost),
    ]

    for check in checks:
        result = check()
        if not result.allowed:
            return result

    return PolicyResult(allowed=True, reason="All policy checks passed")