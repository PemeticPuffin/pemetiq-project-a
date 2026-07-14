"""Narrative drift detection — compares two SEC filings to surface what changed.

Given the latest filing and a year-ago comparable, a single Claude call diffs the
Risk Factors and MD&A sections and returns structured, quote-backed changes:
risk factors added or intensified, metrics quietly dropped, and shifts in
management tone. Every change must carry a verbatim quote so nothing is invented.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from dotenv import load_dotenv

from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS_SYNTHESIS, CLAUDE_TEMPERATURE
from src.analysis.prompts import DRIFT_SYSTEM_PROMPT, DRIFT_USER_PROMPT
from src.data.sec_edgar import SECFiling, format_sections_for_prompt

load_dotenv()
logger = logging.getLogger(__name__)

_KINDS = ("added", "intensified", "dropped", "tone")


@dataclass
class DriftItem:
    """A single detected change between two filings."""

    kind: str      # one of _KINDS
    label: str
    summary: str
    quote: str = ""
    section: str = ""  # "risk_factors" | "mda"


@dataclass
class DriftResult:
    """The narrative-drift comparison between two filings."""

    comparison_basis: str = ""       # e.g. "year-ago quarter"
    current_form: str = ""
    current_report_date: str = ""
    prior_form: str = ""
    prior_report_date: str = ""
    headline: str = ""
    items: list[DriftItem] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None
    available: bool = False          # True once a real comparison has run

    @property
    def counts(self) -> dict[str, int]:
        """Return the number of changes of each kind."""
        tally = {k: 0 for k in _KINDS}
        for item in self.items:
            if item.kind in tally:
                tally[item.kind] += 1
        return tally


def detect_drift(
    current: Optional[SECFiling],
    comparable: Optional[SECFiling],
    basis: str,
) -> DriftResult:
    """Diff two filings and return a structured DriftResult.

    Args:
        current: The latest filing.
        comparable: The year-ago (or prior) filing to compare against.
        basis: Human-readable label for the comparison used.

    Returns:
        DriftResult. `available` is False when there is nothing to compare
        (no comparable filing, or a fetch error on either side).
    """
    if current is None or comparable is None:
        return DriftResult(available=False)
    if current.fetch_error or comparable.fetch_error:
        return DriftResult(available=False)

    result = DriftResult(
        comparison_basis=basis,
        current_form=current.form_type,
        current_report_date=current.report_date,
        prior_form=comparable.form_type,
        prior_report_date=comparable.report_date,
    )

    user_prompt = DRIFT_USER_PROMPT.format(
        company_name=current.company_name,
        current_label=f"{current.form_type} — period ending {current.report_date or current.filed_date}",
        prior_label=f"{comparable.form_type} — period ending {comparable.report_date or comparable.filed_date}",
        current_text=format_sections_for_prompt(current),
        prior_text=format_sections_for_prompt(comparable),
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS_SYNTHESIS,
            temperature=CLAUDE_TEMPERATURE,
            system=DRIFT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = response.content[0].text
        return _parse_drift(raw_text, result)
    except Exception as exc:
        logger.error("Drift detection Claude call failed: %s", exc)
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


def _parse_drift(raw_text: str, result: DriftResult) -> DriftResult:
    """Parse the JSON drift response into the given DriftResult."""
    for candidate in (raw_text, _extract_json(raw_text)):
        try:
            # strict=False tolerates literal newlines/tabs inside verbatim
            # filing quotes, which the model sometimes leaves unescaped.
            data = json.loads(candidate, strict=False)
        except (json.JSONDecodeError, AttributeError):
            continue
        result.headline = data.get("headline", "")
        items: list[DriftItem] = []
        for it in data.get("changes", []):
            kind = str(it.get("kind", "")).lower().strip()
            if kind not in _KINDS or not it.get("summary"):
                continue
            items.append(
                DriftItem(
                    kind=kind,
                    label=it.get("label", ""),
                    summary=it.get("summary", ""),
                    quote=it.get("quote", ""),
                    section=it.get("section", ""),
                )
            )
        result.items = items
        result.raw_response = raw_text
        result.available = True
        return result

    logger.warning("Could not parse drift JSON. Preview: %s", raw_text[:200])
    result.error = "Could not parse drift response as JSON."
    return result
