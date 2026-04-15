import json
import os
import re
from typing import Any

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None


def gemini_enabled() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip() and genai is not None)


def gemini_model_name() -> str:
    return (os.getenv("GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash").strip()


def configure_gemini() -> None:
    if gemini_enabled():
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", "").strip())


def clip_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def extract_json_object(raw_text: str) -> dict[str, Any] | None:
    text = (raw_text or "").strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    return None


def normalize_business_insight(payload: dict[str, Any] | None, fallback: dict[str, Any] | None = None, raw_text: str = "") -> dict[str, Any]:
    base = payload if isinstance(payload, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}

    def normalized_list(key: str, limit: int = 5) -> list[str]:
        values = base.get(key)
        if not isinstance(values, list):
            values = fallback.get(key)
        if not isinstance(values, list):
            return []
        cleaned: list[str] = []
        for item in values[:limit]:
            text = clip_text(item, 220)
            if text:
                cleaned.append(text)
        return cleaned

    headline = clip_text(base.get("headline") or fallback.get("headline") or "Business guidance is ready.", 220)
    priority = clip_text(base.get("priority") or fallback.get("priority") or "Monitor", 40)

    return {
        "headline": headline,
        "priority": priority,
        "recommendations": normalized_list("recommendations"),
        "interpretation": normalized_list("interpretation"),
        "business_impact": normalized_list("business_impact"),
        "watchouts": normalized_list("watchouts"),
        "raw_text": clip_text(raw_text, 4000),
    }


def build_business_prompt(demo_name: str, context: dict[str, Any]) -> str:
    compact_context = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    return f"""You are a practical supply chain decision advisor.

Your job is to interpret analytical results for a business user and give action-oriented recommendations.

Rules:
1. Use only the supplied result context.
2. Focus on business decisions, operational impact, and what to do next.
3. Do not mention model names, ML metrics, training details, algorithms, or evaluation methodology unless absolutely required.
4. Put recommendations in plain business language.
5. Keep each bullet concise and specific.
6. Return strict JSON only. No markdown. No code fences.

Return this JSON shape exactly:
{{
  "headline": "1-2 sentence executive takeaway",
  "priority": "High|Medium|Monitor",
  "recommendations": ["specific action", "specific action", "specific action"],
  "interpretation": ["what the output means", "what the output means"],
  "business_impact": ["commercial or operational implication", "commercial or operational implication"],
  "watchouts": ["risk to monitor", "risk to monitor"]
}}

Demo:
{demo_name}

Result context:
{compact_context}
"""


def generate_business_insight(demo_name: str, context: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if not gemini_enabled():
        return normalize_business_insight(None, fallback=fallback)

    try:
        configure_gemini()
        prompt = build_business_prompt(demo_name, context)
        model = genai.GenerativeModel(gemini_model_name())
        response = model.generate_content(prompt)
        raw_text = str(getattr(response, "text", "") or "").strip()
        parsed = extract_json_object(raw_text)
        return normalize_business_insight(parsed, fallback=fallback, raw_text=raw_text)
    except Exception as exc:
        return normalize_business_insight(
            None,
            fallback=fallback,
            raw_text=f"AI insight unavailable: {clip_text(exc, 220)}",
        )
