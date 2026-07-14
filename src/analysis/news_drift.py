"""News-narrative drift — how the media story about a company has shifted over time.

Uses Claude's built-in web search to compare the dominant news narrative around an
earlier period (anchored to the prior filing's period) against recent coverage, and
reports storylines that emerged or faded plus clear sentiment shifts. Supplementary
to the filing-based Narrative Drift; degrades to hidden when there isn't enough
historical coverage to make a real comparison.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from dotenv import load_dotenv

from config import CLAUDE_MODEL_FAST, CLAUDE_MAX_TOKENS_PER_SOURCE
from src.analysis.prompts import NEWS_DRIFT_SYSTEM_PROMPT, NEWS_DRIFT_USER_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

_NEWS_KINDS = ("emerged", "faded", "sentiment")

# Claude's web_search wraps cited text in <cite index="...">...</cite> markup.
# Strip the tags but keep the inner text so summaries read cleanly.
_CITE_TAG = re.compile(r"</?cite[^>]*>", re.IGNORECASE)


def _strip_citations(text: str) -> str:
    """Remove <cite …> / </cite> markup from web-search text, keeping the content."""
    return _CITE_TAG.sub("", text).strip()


@dataclass
class NewsDriftItem:
    """A single detected shift in the news narrative."""

    kind: str      # one of _NEWS_KINDS
    label: str
    summary: str


@dataclass
class NewsDriftResult:
    """How the news narrative shifted between the prior period and now."""

    prior_period: str = ""
    headline: str = ""
    items: list[NewsDriftItem] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None
    available: bool = False   # True only when real shifts were found

    @property
    def counts(self) -> dict[str, int]:
        """Return the number of shifts of each kind."""
        tally = {k: 0 for k in _NEWS_KINDS}
        for item in self.items:
            if item.kind in tally:
                tally[item.kind] += 1
        return tally


def detect_news_drift(company_name: str, ticker: str, prior_period: str) -> NewsDriftResult:
    """Compare the news narrative around `prior_period` to recent coverage via web search.

    Args:
        company_name: Legal company name.
        ticker: Stock ticker (falls back to the name when unavailable).
        prior_period: Human-readable earlier period to anchor on, e.g. "Mar 2025".

    Returns:
        NewsDriftResult. `available` is False when there aren't enough real shifts
        (including when historical coverage is too thin to compare).
    """
    result = NewsDriftResult(prior_period=prior_period)
    if not prior_period:
        return result

    user_prompt = NEWS_DRIFT_USER_PROMPT.format(
        company_name=company_name,
        ticker=ticker if ticker and ticker.upper() != "N/A" else company_name,
        prior_period=prior_period,
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=CLAUDE_MAX_TOKENS_PER_SOURCE,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=NEWS_DRIFT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = next(
            (b.text for b in reversed(response.content) if b.type == "text"),
            "",
        )
        return _parse_news_drift(raw_text, result)
    except Exception as exc:
        logger.error("News-narrative drift web search failed: %s", exc)
        result.error = str(exc)
        return result


def _extract_json(text: str) -> str:
    """Extract the first balanced JSON object from text that may have preamble."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def _parse_news_drift(raw_text: str, result: NewsDriftResult) -> NewsDriftResult:
    """Parse the JSON news-drift response; `available` is set only if real shifts exist."""
    for candidate in (raw_text, _extract_json(raw_text)):
        try:
            data = json.loads(candidate, strict=False)
        except (json.JSONDecodeError, AttributeError):
            continue
        result.headline = _strip_citations(data.get("headline", ""))
        items: list[NewsDriftItem] = []
        for it in data.get("shifts", []):
            kind = str(it.get("kind", "")).lower().strip()
            if kind not in _NEWS_KINDS or not it.get("summary"):
                continue
            items.append(
                NewsDriftItem(
                    kind=kind,
                    label=_strip_citations(it.get("label", "")),
                    summary=_strip_citations(it.get("summary", "")),
                )
            )
        result.items = items
        result.raw_response = raw_text
        result.available = bool(items)
        return result

    logger.warning("Could not parse news-drift JSON. Preview: %s", raw_text[:200])
    result.error = "Could not parse news-drift response as JSON."
    return result
