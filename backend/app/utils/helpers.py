"""
Shared utility functions used across the entire backend.
"""
from datetime import datetime, timezone, timedelta
import hashlib


def format_usd(amount: float) -> str:
    """Format a float as a USD string. e.g. 0.004231 → '$0.004231'"""
    if amount == 0:
        return "$0.0000"
    if amount < 0.001:
        return f"${amount:.6f}"
    if amount < 1:
        return f"${amount:.4f}"
    return f"${amount:.2f}"


def truncate_text(text: str, max_chars: int = 300) -> str:
    """Truncate text for previews stored in logs."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def estimate_tokens(text: str) -> int:
    """
    Fast token approximation without external tokenizer.
    Rule of thumb: ~1.3 tokens per word, minimum 1.
    """
    if not text:
        return 0
    word_count = len(text.split())
    return max(1, int(word_count * 1.3))


def get_today_range() -> tuple:
    """Return (start_of_today, end_of_today) as UTC datetime objects."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def get_last_n_days_range(n: int) -> tuple:
    """Return (start, end) for the last N days in UTC."""
    now = datetime.now(timezone.utc)
    end = now.replace(hour=23, minute=59, second=59)
    start = (now - timedelta(days=n - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that never raises ZeroDivisionError."""
    if denominator == 0:
        return default
    return numerator / denominator


def make_dedup_key(alert_type: str, window_minutes: int = 5) -> str:
    """
    Create a deduplication key for alerts.
    Same alert type within the same time window = same key = no duplicate.
    """
    now = datetime.now(timezone.utc)
    window_bucket = now.minute // window_minutes
    raw = f"{alert_type}:{now.date()}:{now.hour}:{window_bucket}"
    return hashlib.md5(raw.encode()).hexdigest()


def mask_api_key(key: str) -> str:
    """Show first 4 and last 4 chars only. e.g. sk-ab...xyz1"""
    if not key or len(key) < 10:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def infer_provider_from_model(model: str) -> str:
    """Infer the provider name from a model string."""
    model_lower = model.lower()
    if model_lower.startswith("gemini"):
        return "google"
    if any(x in model_lower for x in ["llama", "mixtral", "groq"]):
        return "groq"
    if any(x in model_lower for x in ["gpt", "openai"]):
        return "openai"
    return "unknown"


def time_bucket_label(dt: datetime, bucket_minutes: int = 5) -> str:
    """Return a time bucket string like '14:35' for grouping sparklines."""
    bucket = (dt.minute // bucket_minutes) * bucket_minutes
    return f"{dt.hour:02d}:{bucket:02d}"