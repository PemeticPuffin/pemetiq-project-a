"""Cross-source synthesis and contradiction detection."""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from dotenv import load_dotenv

from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS_SYNTHESIS, CLAUDE_TEMPERATURE
from src.analysis.per_source import SourceAnalysis
from src.analysis.prompts import (
    COMPARISON_SYSTEM_PROMPT,
    COMPARISON_USER_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT,
    SYNTHESIS_USER_PROMPT,
)

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """A contradiction detected between two data sources."""

    claim: str
    source_a: str
    source_b: str
    significance: str


@dataclass
class SynthesisResult:
    """The final cross-source competitive intelligence brief."""

    company_name: str
    ticker: str
    executive_summary: str = ""
    key_takeaways: list[str] = field(default_factory=list)
    reinforcing_signals: list[str] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    notable_absences: list[str] = field(default_factory=list)
    watch_signals: list[str] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None

    @property
    def has_contradictions(self) -> bool:
        """True if the synthesis found any cross-source contradictions."""
        return len(self.contradictions) > 0


@dataclass
class CompetitiveEdge:
    """One company's advantage on a specific dimension."""

    company: str
    dimension: str
    advantage: str
    evidence: str


@dataclass
class DivergingSignal:
    """A topic where the two companies' signals point in different directions."""

    topic: str
    company_a: str
    company_b: str


@dataclass
class ComparisonResult:
    """Head-to-head comparison synthesis for two companies."""

    name_a: str
    ticker_a: str
    name_b: str
    ticker_b: str
    comparison_summary: str = ""
    key_takeaways: list[str] = field(default_factory=list)
    competitive_edges: list[CompetitiveEdge] = field(default_factory=list)
    shared_vulnerabilities: list[str] = field(default_factory=list)
    diverging_signals: list[DivergingSignal] = field(default_factory=list)
    watch_signals: list[str] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None


def compare_synthesize(
    name_a: str,
    ticker_a: str,
    analyses_a: list[SourceAnalysis],
    name_b: str,
    ticker_b: str,
    analyses_b: list[SourceAnalysis],
) -> ComparisonResult:
    """Run head-to-head comparison synthesis via Claude.

    Takes independent per-source analyses for two companies and produces a
    structured comparison: competitive edges, shared vulnerabilities, diverging
    signals, and watch items.

    Args:
        name_a: Legal name of company A.
        ticker_a: Ticker for company A.
        analyses_a: Per-source analyses for company A.
        name_b: Legal name of company B.
        ticker_b: Ticker for company B.
        analyses_b: Per-source analyses for company B.

    Returns:
        ComparisonResult with the full head-to-head brief.
    """
    text_a = "\n\n".join(a.to_brief_text() for a in analyses_a)
    text_b = "\n\n".join(a.to_brief_text() for a in analyses_b)

    user_prompt = COMPARISON_USER_PROMPT.format(
        name_a=name_a,
        ticker_a=ticker_a,
        name_b=name_b,
        ticker_b=ticker_b,
        analyses_a=text_a,
        analyses_b=text_b,
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS_SYNTHESIS,
            temperature=CLAUDE_TEMPERATURE,
            system=COMPARISON_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = response.content[0].text
        return _parse_comparison(raw_text, name_a, ticker_a, name_b, ticker_b)
    except Exception as exc:
        logger.error("Comparison synthesis Claude call failed: %s", exc)
        return ComparisonResult(
            name_a=name_a, ticker_a=ticker_a,
            name_b=name_b, ticker_b=ticker_b,
            error=str(exc),
        )


def _parse_comparison(
    raw_text: str, name_a: str, ticker_a: str, name_b: str, ticker_b: str
) -> ComparisonResult:
    """Parse JSON comparison output from Claude into a ComparisonResult."""
    try:
        data = json.loads(raw_text, strict=False)
        edges = [
            CompetitiveEdge(
                company=e.get("company", ""),
                dimension=e.get("dimension", ""),
                advantage=e.get("advantage", ""),
                evidence=e.get("evidence", ""),
            )
            for e in data.get("competitive_edges", [])
        ]
        diverging = [
            DivergingSignal(
                topic=d.get("topic", ""),
                company_a=d.get("company_a", ""),
                company_b=d.get("company_b", ""),
            )
            for d in data.get("diverging_signals", [])
        ]
        return ComparisonResult(
            name_a=name_a, ticker_a=ticker_a,
            name_b=name_b, ticker_b=ticker_b,
            comparison_summary=data.get("comparison_summary", ""),
            key_takeaways=data.get("key_takeaways", []),
            competitive_edges=edges,
            shared_vulnerabilities=data.get("shared_vulnerabilities", []),
            diverging_signals=diverging,
            watch_signals=data.get("watch_signals", []),
            raw_response=raw_text,
        )
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Could not parse comparison JSON: %s", exc)
        return ComparisonResult(
            name_a=name_a, ticker_a=ticker_a,
            name_b=name_b, ticker_b=ticker_b,
            comparison_summary=raw_text[:500],
            raw_response=raw_text,
            error=f"JSON parse error: {exc}",
        )


def synthesize(
    company_name: str,
    ticker: str,
    source_analyses: list[SourceAnalysis],
) -> SynthesisResult:
    """Run cross-source synthesis via Claude.

    Feeds all per-source analyses into a single Claude call that identifies
    reinforcing signals, contradictions, notable absences, and watch signals.

    Args:
        company_name: Legal company name.
        ticker: Stock ticker symbol.
        source_analyses: List of SourceAnalysis results from per_source.analyze_all_sources.

    Returns:
        SynthesisResult with the full competitive intelligence brief.
    """
    source_analyses_text = "\n\n".join(a.to_brief_text() for a in source_analyses)
    user_prompt = SYNTHESIS_USER_PROMPT.format(
        company_name=company_name,
        ticker=ticker,
        source_analyses_text=source_analyses_text,
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS_SYNTHESIS,
            temperature=CLAUDE_TEMPERATURE,
            system=SYNTHESIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = response.content[0].text
        return _parse_synthesis(raw_text, company_name, ticker)
    except Exception as exc:
        logger.error("Synthesis Claude call failed: %s", exc)
        return SynthesisResult(
            company_name=company_name,
            ticker=ticker,
            error=str(exc),
        )


def _parse_synthesis(raw_text: str, company_name: str, ticker: str) -> SynthesisResult:
    """Parse JSON synthesis output from Claude into a SynthesisResult.

    Args:
        raw_text: Raw text returned by Claude.
        company_name: Company name for the result object.
        ticker: Ticker for the result object.

    Returns:
        SynthesisResult with all fields populated, or error set on parse failure.
    """
    try:
        data = json.loads(raw_text, strict=False)
        contradictions = [
            Contradiction(
                claim=c.get("claim", ""),
                source_a=c.get("source_a", ""),
                source_b=c.get("source_b", ""),
                significance=c.get("significance", ""),
            )
            for c in data.get("contradictions", [])
        ]
        return SynthesisResult(
            company_name=company_name,
            ticker=ticker,
            executive_summary=data.get("executive_summary", ""),
            key_takeaways=data.get("key_takeaways", []),
            reinforcing_signals=data.get("reinforcing_signals", []),
            contradictions=contradictions,
            notable_absences=data.get("notable_absences", []),
            watch_signals=data.get("watch_signals", []),
            raw_response=raw_text,
        )
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Could not parse synthesis JSON: %s", exc)
        return SynthesisResult(
            company_name=company_name,
            ticker=ticker,
            executive_summary=raw_text[:500],
            raw_response=raw_text,
            error=f"JSON parse error: {exc}",
        )
