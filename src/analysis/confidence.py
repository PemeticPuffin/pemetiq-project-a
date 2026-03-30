"""Confidence scoring utilities for CI Autopilot findings."""

from typing import Literal

ConfidenceLevel = Literal["High", "Medium", "Low", "Insufficient Data"]

VALID_CONFIDENCE_LEVELS: set[str] = {"High", "Medium", "Low", "Insufficient Data"}

# Maps confidence level to sort order (higher = more confident)
CONFIDENCE_ORDER: dict[str, int] = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
    "Insufficient Data": 0,
}

# Badge colors for UI rendering (matches Pemetiq brand spec)
CONFIDENCE_COLORS: dict[str, str] = {
    "High": "#2E7D32",
    "Medium": "#F57C00",
    "Low": "#C62828",
    "Insufficient Data": "#9E9E9E",
}


def normalize_confidence(raw: str) -> ConfidenceLevel:
    """Normalize a confidence string from LLM output to a valid level.

    Args:
        raw: Raw confidence string (e.g. "high", "MEDIUM", "insufficient data").

    Returns:
        One of the four canonical ConfidenceLevel values.
    """
    stripped = raw.strip()
    if stripped in VALID_CONFIDENCE_LEVELS:
        return stripped  # type: ignore[return-value]
    lower = stripped.lower()
    if "high" in lower:
        return "High"
    if "medium" in lower or "moderate" in lower:
        return "Medium"
    if "low" in lower:
        return "Low"
    return "Insufficient Data"


def confidence_color(level: str) -> str:
    """Return the hex color for a confidence level badge.

    Args:
        level: Confidence level string.

    Returns:
        Hex color string.
    """
    return CONFIDENCE_COLORS.get(level, CONFIDENCE_COLORS["Insufficient Data"])


def sort_findings_by_confidence(findings: list[dict]) -> list[dict]:
    """Sort a list of finding dicts by confidence level, highest first.

    Args:
        findings: List of dicts each containing a "confidence" key.

    Returns:
        Sorted list (High → Medium → Low → Insufficient Data).
    """
    return sorted(
        findings,
        key=lambda f: CONFIDENCE_ORDER.get(f.get("confidence", ""), 0),
        reverse=True,
    )
