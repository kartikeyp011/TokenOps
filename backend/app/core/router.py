"""
Smart routing engine — decides which model to actually use.
Strategy: policy first → budget-aware → quality-aware → cheapest viable.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.core.cost_estimator import get_cheapest_model, get_premium_model, get_model_tier, estimate_cost
from app.models.db_models import RequestLog
from app.utils.helpers import safe_divide


@dataclass
class RouterDecision:
    model: str
    provider: str
    decision: str   # pass_through | cheapest | quality | budget_fallback | default
    reason: str
    original_request: str  # what the client asked for


def _get_today_spend(db: Session) -> float:
    """Sum all successful costs today."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= today_start, RequestLog.status == "success")
        .all()
    )
    return sum(r.estimated_cost_usd for r in rows)


def _infer_provider(model: str) -> str:
    """Infer provider name from model string."""
    m = model.lower()
    if m.startswith("gemini"):
        return "google"
    if any(x in m for x in ["llama", "mixtral"]):
        return "groq"
    return "unknown"


def select_model(
    db: Session,
    analysis: dict,
    requested_model: str = None,
) -> RouterDecision:
    """
    Hybrid routing strategy:
    1. If client requested a specific allowed model → honor it (pass-through)
    2. If today's budget spend > 80% of cap → force cheapest model
    3. If prompt requires high quality (complex/coding) → use premium model
    4. Default → cheapest viable model

    Args:
        db: DB session for spend lookups
        analysis: output of analyzer.analyze_prompt()
        requested_model: what the client asked for (may be None)

    Returns:
        RouterDecision with the final model choice and reasoning
    """
    # --- Step 1: Honor explicit model request if it's allowed ---
    if requested_model and requested_model in settings.allowed_models:
        provider = _infer_provider(requested_model)
        return RouterDecision(
            model=requested_model,
            provider=provider,
            decision="pass_through",
            reason=f"Client explicitly requested '{requested_model}' — honoring request",
            original_request=requested_model or "not specified",
        )

    # --- Step 2: Budget pressure check ---
    today_spend = _get_today_spend(db)
    budget_cap = settings.daily_budget_cap_usd
    budget_pct_used = safe_divide(today_spend, budget_cap)

    if budget_pct_used >= settings.alert_budget_pct_warning:
        cheapest = get_cheapest_model()
        provider = _infer_provider(cheapest)
        return RouterDecision(
            model=cheapest,
            provider=provider,
            decision="budget_fallback",
            reason=f"Budget at {budget_pct_used*100:.0f}% (${today_spend:.4f}/${budget_cap}) — routing to cheapest model",
            original_request=requested_model or "not specified",
        )

    # --- Step 3: Quality decision based on prompt analysis ---
    requires_high_quality = analysis.get("requires_high_quality", False)
    complexity = analysis.get("complexity", "simple")
    task_type = analysis.get("task_type", "general")

    if requires_high_quality:
        premium = get_premium_model()
        provider = _infer_provider(premium)
        return RouterDecision(
            model=premium,
            provider=provider,
            decision="quality",
            reason=f"Prompt is '{complexity}' complexity and task type '{task_type}' — routing to premium model",
            original_request=requested_model or "not specified",
        )

    # --- Step 4: Default — cheapest viable model ---
    cheapest = get_cheapest_model()
    provider = _infer_provider(cheapest)
    return RouterDecision(
        model=cheapest,
        provider=provider,
        decision="cheapest",
        reason=f"Simple '{task_type}' prompt — routing to cheapest model for cost efficiency",
        original_request=requested_model or "not specified",
    )