"""
Seed data generator.
Runs once when the DB is empty. Inserts realistic fake data so the
frontend dashboard has something to display immediately.
"""
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.db_models import RequestLog, AlertRecord, PolicyConfig, SeedState
from app.config import settings

SAMPLE_PROMPTS = [
    "Explain how transformers work in machine learning",
    "Write a Python function to sort a list of dictionaries by a key",
    "Summarize the key differences between REST and GraphQL",
    "What is the capital of France?",
    "Implement a binary search algorithm in Python",
    "Write a SQL query to find duplicate rows in a table",
    "Explain the concept of gradient descent",
    "How do I reverse a string in Python?",
    "What are the SOLID principles in software engineering?",
    "Write a function to check if a number is prime",
    "Explain Docker containers vs virtual machines",
    "How does async/await work in Python?",
    "What is the difference between a list and a tuple?",
    "Write unit tests for a FastAPI endpoint",
    "Explain the CAP theorem in distributed systems",
]

MODELS = [
    ("llama3-8b-8192", "groq", "cheapest"),
    ("llama3-70b-8192", "groq", "quality"),
    ("gemini-1.5-flash", "google", "cheapest"),
    ("gemini-1.5-pro", "google", "quality"),
    ("mixtral-8x7b-32768", "groq", "cheapest"),
]

ROUTING_DECISIONS = [
    ("cheapest", "Simple general prompt — routing to cheapest model"),
    ("quality", "Complex coding prompt — routing to premium model"),
    ("pass_through", "Client explicitly requested this model"),
    ("budget_fallback", "Budget at 82% — routing to cheapest model"),
    ("cache_hit", "Exact prompt+model match found in semantic cache"),
]

DEFAULT_POLICIES = [
    ("max_tokens_per_request", "4096", "Maximum tokens allowed per single request"),
    ("daily_budget_cap_usd", "5.0", "Maximum USD spend allowed per day"),
    ("rate_limit_rpm", "50", "Maximum requests allowed per minute"),
    ("routing_strategy", "hybrid", "Routing strategy: cost_first | quality_first | hybrid"),
    ("allowed_models", "llama3-8b-8192,llama3-70b-8192,gemini-1.5-flash,gemini-1.5-pro,mixtral-8x7b-32768", "Comma-separated list of allowed model IDs"),
]


def _is_seeded(db: Session) -> bool:
    state = db.query(SeedState).filter(SeedState.id == 1).first()
    return state is not None and state.seeded


def _mark_seeded(db: Session):
    state = db.query(SeedState).filter(SeedState.id == 1).first()
    if state:
        state.seeded = True
        state.seeded_at = datetime.now(timezone.utc)
    else:
        db.add(SeedState(id=1, seeded=True, seeded_at=datetime.now(timezone.utc)))
    db.commit()


def _seed_policies(db: Session):
    for name, value, description in DEFAULT_POLICIES:
        existing = db.query(PolicyConfig).filter(PolicyConfig.policy_name == name).first()
        if not existing:
            db.add(PolicyConfig(
                policy_name=name,
                policy_value=value,
                description=description,
            ))
    db.commit()


def _seed_request_logs(db: Session):
    """Generate 7 days of realistic request log data."""
    now = datetime.now(timezone.utc)

    for day_offset in range(6, -1, -1):  # 6 days ago to today
        day_base = now - timedelta(days=day_offset)
        # More requests on recent days
        num_requests = random.randint(30, 120) if day_offset <= 2 else random.randint(10, 50)

        for _ in range(num_requests):
            # Random time in that day
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            ts = day_base.replace(hour=hour, minute=minute, second=random.randint(0, 59))

            prompt = random.choice(SAMPLE_PROMPTS)
            model_name, provider, tier = random.choice(MODELS)
            decision, reason = random.choice(ROUTING_DECISIONS)
            is_cached = decision == "cache_hit"
            is_error = random.random() < 0.04  # 4% error rate

            prompt_tokens = random.randint(20, 400)
            completion_tokens = random.randint(10, 200) if not is_error else 0

            # Cost from pricing table
            pricing = settings.model_pricing.get(model_name, {})
            cost = round(
                (prompt_tokens / 1000) * pricing.get("input_per_1k", 0.0001)
                + (completion_tokens / 1000) * pricing.get("output_per_1k", 0.0002),
                8
            )

            # Cost saved — compare to gpt-4o as baseline
            gpt4o = settings.model_pricing.get("gpt-4o", {})
            baseline_cost = round(
                (prompt_tokens / 1000) * gpt4o.get("input_per_1k", 0.005)
                + (completion_tokens / 1000) * gpt4o.get("output_per_1k", 0.015),
                8
            )
            cost_saved = max(0.0, round(baseline_cost - cost, 8))

            db.add(RequestLog(
                timestamp=ts,
                prompt=prompt,
                prompt_preview=prompt[:300],
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                model_requested=model_name,
                model_used=model_name,
                provider=provider if not is_cached else "cache",
                routing_decision=decision,
                routing_reason=reason,
                estimated_cost_usd=0.0 if is_cached else cost,
                cost_saved_usd=cost if is_cached else cost_saved,
                status="error" if is_error else "success",
                error_message="Provider timeout" if is_error else None,
                latency_ms=random.randint(150, 2500),
                is_cached=is_cached,
                is_mock=True,
                response_preview="Mock response generated by TokenOps." if not is_error else None,
            ))

    db.commit()


def _seed_alerts(db: Session):
    """Insert a few sample alerts — one resolved, two active."""
    now = datetime.now(timezone.utc)

    db.add(AlertRecord(
        timestamp=now - timedelta(hours=2),
        alert_type="budget_warning",
        severity="warning",
        message="Daily budget at 83% ($4.15 / $5.00)",
        resolved=True,
        resolved_at=now - timedelta(hours=1),
        dedup_key="seed-resolved-1",
    ))
    db.add(AlertRecord(
        timestamp=now - timedelta(minutes=45),
        alert_type="cost_spike",
        severity="warning",
        message="Cost spike detected: $0.003200 is 12.4x the daily average ($0.000258)",
        resolved=False,
        dedup_key="seed-active-1",
    ))
    db.add(AlertRecord(
        timestamp=now - timedelta(minutes=10),
        alert_type="rate_surge",
        severity="warning",
        message="Rate surge: 16 requests in last 60s (limit:520)",
        resolved=False,
        dedup_key="seed-active-2",
    ))
    db.commit()


def ensure_seeded(db: Session):
    """
    Entry point — called by every route handler.
    Runs the full seed if DB is empty. Safe to call repeatedly.
    """
    if _is_seeded(db):
        return

    # Check if there are real logs already
    log_count = db.query(RequestLog).count()
    if log_count > 0:
        _mark_seeded(db)
        return

    # Run all seeders
    _seed_policies(db)
    _seed_request_logs(db)
    _seed_alerts(db)
    _mark_seeded(db)