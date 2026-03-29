"""
Prompt analyzer — classifies prompts before routing decisions are made.
All logic is heuristic-based (no external calls).
"""
from app.utils.helpers import estimate_tokens

# Keywords that indicate a complex or coding task
CODING_KEYWORDS = [
    "code", "function", "implement", "program", "script", "debug",
    "class", "algorithm", "api", "sql", "query", "refactor", "fix the bug",
    "write a", "build a", "create a", "develop"
]

EXPLANATION_KEYWORDS = [
    "explain", "summarize", "describe", "what is", "how does",
    "tell me about", "give me an overview", "define", "elaborate"
]

CREATIVE_KEYWORDS = [
    "write a story", "poem", "creative", "imagine", "fiction",
    "essay", "blog post", "marketing copy", "generate ideas"
]


def analyze_prompt(prompt: str) -> dict:
    """
    Analyze a prompt and return a classification dict.

    Returns:
        {
            "estimated_tokens": int,
            "complexity": "simple" | "medium" | "complex",
            "task_type": "coding" | "explanation" | "creative" | "general",
            "requires_high_quality": bool,
            "word_count": int
        }
    """
    if not prompt:
        return {
            "estimated_tokens": 0,
            "complexity": "simple",
            "task_type": "general",
            "requires_high_quality": False,
            "word_count": 0,
        }

    prompt_lower = prompt.lower()
    tokens = estimate_tokens(prompt)
    word_count = len(prompt.split())

    # Complexity classification
    if tokens < 200:
        complexity = "simple"
    elif tokens < 800:
        complexity = "medium"
    else:
        complexity = "complex"

    # Task type classification — check in priority order
    if any(kw in prompt_lower for kw in CODING_KEYWORDS):
        task_type = "coding"
    elif any(kw in prompt_lower for kw in EXPLANATION_KEYWORDS):
        task_type = "explanation"
    elif any(kw in prompt_lower for kw in CREATIVE_KEYWORDS):
        task_type = "creative"
    else:
        task_type = "general"

    # High quality needed if task is complex or involves coding
    requires_high_quality = (
        complexity == "complex"
        or task_type == "coding"
    )

    return {
        "estimated_tokens": tokens,
        "complexity": complexity,
        "task_type": task_type,
        "requires_high_quality": requires_high_quality,
        "word_count": word_count,
    }


def extract_last_user_message(messages: list) -> str:
    """
    Extract the last user message from an OpenAI-style messages array.
    Falls back to joining all content if no user message found.
    """
    if not messages:
        return ""

    # Walk backwards to find the last user message
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            # Handle array content (vision models)
            if isinstance(content, list):
                return " ".join(
                    part.get("text", "") for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )

    # Fallback: join all message content
    parts = []
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(content)
    return " ".join(parts)