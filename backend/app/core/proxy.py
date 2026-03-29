"""
Proxy handler — the full request lifecycle for POST /v1/chat/completions.
Every request flows through: cache → policy → router → LLM → log → respond.
"""
import time
from sqlalchemy.orm import Session
from app.core.analyzer import analyze_prompt, extract_last_user_message
from app.core.cost_estimator import estimate_cost, calculate_cost_saved, estimate_tokens
from app.core.policy_engine import run_all_checks
from app.core.router import select_model
from app.core.cache import cache
from app.core.logger import log_request, log_alert
from app.services.llm_service import registry
from app.utils.helpers import truncate_text, safe_divide
from app.config import settings
from datetime import datetime, timezone, timedelta


class PolicyViolationError(Exception):
    def __init__(self, reason: str, blocked_by: str):
        self.reason = reason
        self.blocked_by = blocked_by
        super().__init__(reason)


async def handle_proxy_request(
    request_body: dict,
    db: Session,
) -> dict:
    """
    Full proxy lifecycle:
    1. Extract prompt from messages
    2. Check cache → return immediately if hit
    3. Analyze prompt (complexity, task type)
    4. Estimate cost
    5. Run policy checks
    6. Smart route to best model
    7. Call LLM (real or mock)
    8. Log everything to DB
    9. Check and fire alerts
    10. Store in cache
    11. Return OpenAI-compatible response
    """
    start_time = time.time()

    messages = request_body.get("messages", [])
    requested_model = request_body.get("model", "")
    max_tokens = request_body.get("max_tokens", 1024)

    # --- 1. Extract the user prompt ---
    prompt = extract_last_user_message(messages)
    if not prompt:
        prompt = "empty prompt"

    # --- 2. Cache check ---
    cache_key_model = requested_model or settings.default_cheap_model
    cached = cache.get(prompt, cache_key_model)
    if cached:
        # Log the cached hit
        analysis = analyze_prompt(prompt)
        prompt_tokens = analysis["estimated_tokens"]
        cost = estimate_cost(cache_key_model, prompt_tokens, 0)

        log_request(
            db=db,
            prompt=prompt,
            model_requested=requested_model,
            model_used=cache_key_model,
            provider="cache",
            routing_decision="cache_hit",
            routing_reason="Exact prompt+model match found in semantic cache",
            estimated_cost_usd=0.0,
            cost_saved_usd=cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            status="success",
            latency_ms=int((time.time() - start_time) * 1000),
            is_cached=True,
            is_mock=cached.get("mock", False),
            response_preview=truncate_text(
                cached.get("choices", [{}])[0].get("message", {}).get("content", ""), 300
            ),
        )
        return cached

    # --- 3. Analyze prompt ---
    analysis = analyze_prompt(prompt)
    prompt_tokens = analysis["estimated_tokens"]

    # --- 4. Estimate cost for policy checks ---
    check_model = requested_model or settings.default_cheap_model
    estimated_cost = estimate_cost(check_model, prompt_tokens, int(prompt_tokens * 0.3))

    # --- 5. Run all policy checks ---
    policy_result = run_all_checks(
        db=db,
        model=requested_model,
        tokens=prompt_tokens,
        estimated_cost=estimated_cost,
    )

    if not policy_result.allowed:
        # Log the blocked request
        log_request(
            db=db,
            prompt=prompt,
            model_requested=requested_model,
            model_used=requested_model or "blocked",
            provider="policy",
            routing_decision="blocked",
            routing_reason=policy_result.reason,
            estimated_cost_usd=0.0,
            cost_saved_usd=0.0,
            prompt_tokens=prompt_tokens,
            status="blocked",
            error_message=policy_result.reason,
            latency_ms=int((time.time() - start_time) * 1000),
        )
        raise PolicyViolationError(
            reason=policy_result.reason,
            blocked_by=policy_result.blocked_by,
        )

    # --- 6. Smart routing ---
    routing = select_model(
        db=db,
        analysis=analysis,
        requested_model=requested_model if requested_model in settings.allowed_models else None,
    )
    final_model = routing.model
    provider_name = routing.provider

    # --- 7. Call LLM ---
    llm_response = await registry.call(
        model=final_model,
        messages=messages,
        max_tokens=max_tokens,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    # Handle LLM error
    if llm_response.error:
        log_request(
            db=db,
            prompt=prompt,
            model_requested=requested_model,
            model_used=final_model,
            provider=provider_name,
            routing_decision=routing.decision,
            routing_reason=routing.reason,
            estimated_cost_usd=0.0,
            cost_saved_usd=0.0,
            prompt_tokens=prompt_tokens,
            status="error",
            error_message=llm_response.error,
            latency_ms=latency_ms,
            is_mock=llm_response.mock,
        )
        return _error_response(llm_response.error, final_model)

    # --- 8. Calculate final cost ---
    actual_cost = estimate_cost(
        final_model,
        llm_response.prompt_tokens,
        llm_response.completion_tokens,
    )
    cost_saved = calculate_cost_saved(
        model_used=final_model,
        model_requested=requested_model or final_model,
        prompt_tokens=llm_response.prompt_tokens,
        completion_tokens=llm_response.completion_tokens,
    )

    # --- 9. Log the successful request ---
    log_request(
        db=db,
        prompt=prompt,
        model_requested=requested_model,
        model_used=final_model,
        provider=provider_name,
        routing_decision=routing.decision,
        routing_reason=routing.reason,
        estimated_cost_usd=actual_cost,
        cost_saved_usd=cost_saved,
        prompt_tokens=llm_response.prompt_tokens,
        completion_tokens=llm_response.completion_tokens,
        status="success",
        latency_ms=latency_ms,
        is_cached=False,
        is_mock=llm_response.mock,
        response_preview=truncate_text(llm_response.content, 300),
    )

    # --- 10. Fire alerts if needed ---
    _check_and_fire_alerts(db, actual_cost)

    # --- 11. Build OpenAI-compatible response ---
    response = _build_response(llm_response, final_model, routing)

    # Store in cache
    cache.set(prompt, cache_key_model, response, cost=actual_cost)

    return response


def _build_response(llm_response, model: str, routing) -> dict:
    """Return an OpenAI-compatible response object."""
    return {
        "id": f"tokenops-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": llm_response.content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "total_tokens": llm_response.prompt_tokens + llm_response.completion_tokens,
        },
        "tokenops": {
            "routing_decision": routing.decision,
            "routing_reason": routing.reason,
            "original_model_requested": routing.original_request,
            "mock": llm_response.mock,
            "provider": llm_response.provider,
        },
    }


def _error_response(error: str, model: str) -> dict:
    """Return a structured error in OpenAI-compatible format."""
    return {
        "id": f"tokenops-error-{int(time.time())}",
        "object": "chat.completion",
        "model": model,
        "error": {
            "message": error,
            "type": "provider_error",
        },
        "choices": [],
    }


def _check_and_fire_alerts(db: Session, current_cost: float):
    """
    After every successful request, check if any alert conditions are met.
    Alerts are deduplicated — won't fire the same type twice in 5 minutes.
    """
    from app.models.db_models import RequestLog

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # -- Alert 1: Daily budget exceeded or near limit --
    today_logs = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= today_start, RequestLog.status == "success")
        .all()
    )
    today_total = sum(r.estimated_cost_usd for r in today_logs)
    budget_cap = settings.daily_budget_cap_usd

    if today_total >= budget_cap:
        log_alert(
            db=db,
            alert_type="budget_exceeded",
            severity="critical",
            message=f"Daily budget cap of ${budget_cap} has been exceeded. Total spent today: ${today_total:.4f}",
        )
    elif today_total >= budget_cap * settings.alert_budget_pct_warning:
        log_alert(
            db=db,
            alert_type="budget_warning",
            severity="warning",
            message=f"Daily budget at {(today_total/budget_cap*100):.0f}% (${today_total:.4f} / ${budget_cap})",
        )

    # -- Alert 2: Cost spike detection --
    if len(today_logs) >= 3:
        avg_cost = safe_divide(
            sum(r.estimated_cost_usd for r in today_logs[:-1]),
            len(today_logs) - 1,
        )
        if avg_cost > 0 and current_cost > avg_cost * settings.alert_spike_multiplier:
            log_alert(
                db=db,
                alert_type="cost_spike",
                severity="warning",
                message=f"Cost spike detected: ${current_cost:.6f} is {current_cost/avg_cost:.1f}x the daily average (${avg_cost:.6f})",
            )

    # -- Alert 3: High error rate --
    recent_logs = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=10))
        .all()
    )
    if len(recent_logs) >= 5:
        error_count = sum(1 for r in recent_logs if r.status == "error")
        error_rate = safe_divide(error_count, len(recent_logs))
        if error_rate >= settings.alert_error_rate_threshold:
            log_alert(
                db=db,
                alert_type="high_error_rate",
                severity="warning",
                message=f"High error rate: {error_rate*100:.0f}% of last {len(recent_logs)} requests failed",
            )

    # -- Alert 4: Rate surge --
    one_min_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
    recent_count = (
        db.query(RequestLog)
        .filter(RequestLog.timestamp >= one_min_ago)
        .count()
    )
    rpm_limit = settings.rate_limit_rpm
    if recent_count >= rpm_limit * settings.alert_rate_surge_pct:
        log_alert(
            db=db,
            alert_type="rate_surge",
            severity="warning",
            message=f"Rate surge: {recent_count} requests in last 60s (limit: {rpm_limit})",
        )