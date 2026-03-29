"""
Cost estimation engine.
Uses the pricing table in config.py — no hardcoded values here.
"""
from app.config import settings
from app.utils.helpers import estimate_tokens


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int = 0) -> float:
    """
    Calculate the estimated cost in USD for a model call.
    Returns 0.0 if model is not in the pricing table.
    """
    pricing = settings.model_pricing.get(model)
    if not pricing:
        return 0.0

    input_cost = (prompt_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_per_1k"]
    return round(input_cost + output_cost, 8)


def estimate_cost_for_prompt(model: str, prompt: str) -> float:
    """Convenience: estimate cost from raw prompt text before calling the LLM."""
    tokens = estimate_tokens(prompt)
    # Assume completion ≈ 30% of prompt tokens as a conservative estimate
    completion_estimate = int(tokens * 0.3)
    return estimate_cost(model, tokens, completion_estimate)


def calculate_cost_saved(
    model_used: str,
    model_requested: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """
    How much money was saved by routing to a cheaper model.
    Returns positive value if we used a cheaper model, 0 if same or more expensive.
    """
    if model_used == model_requested:
        return 0.0

    cost_requested = estimate_cost(model_requested, prompt_tokens, completion_tokens)
    cost_used = estimate_cost(model_used, prompt_tokens, completion_tokens)
    saved = cost_requested - cost_used
    return max(0.0, round(saved, 8))


def get_cheapest_model(provider: str = None) -> str:
    """
    Return the cheapest available model, optionally filtered by provider.
    Picks the model with the lowest combined input+output rate.
    """
    cheapest_model = None
    cheapest_rate = float("inf")

    for model_name, pricing in settings.model_pricing.items():
        if model_name not in settings.allowed_models:
            continue
        if provider and pricing.get("provider") != provider:
            continue
        combined_rate = pricing["input_per_1k"] + pricing["output_per_1k"]
        if combined_rate < cheapest_rate:
            cheapest_rate = combined_rate
            cheapest_model = model_name

    return cheapest_model or settings.default_cheap_model


def get_premium_model(provider: str = None) -> str:
    """
    Return the highest quality model, optionally filtered by provider.
    Picks the model with the highest combined rate (proxy for quality).
    """
    best_model = None
    best_rate = 0.0

    for model_name, pricing in settings.model_pricing.items():
        if model_name not in settings.allowed_models:
            continue
        if provider and pricing.get("provider") != provider:
            continue
        combined_rate = pricing["input_per_1k"] + pricing["output_per_1k"]
        if combined_rate > best_rate:
            best_rate = combined_rate
            best_model = model_name

    return best_model or settings.default_premium_model


def get_model_tier(model: str) -> str:
    """Return 'cheap', 'mid', or 'premium' for a model."""
    pricing = settings.model_pricing.get(model, {})
    return pricing.get("tier", "mid")