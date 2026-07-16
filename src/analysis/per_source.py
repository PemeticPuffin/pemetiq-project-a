"""Per-source analysis orchestration — calls Claude once per data source, concurrently."""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from dotenv import load_dotenv

from config import CLAUDE_MODEL_FAST, CLAUDE_MAX_TOKENS_PER_SOURCE, CLAUDE_TEMPERATURE
from src import spend
from src.analysis.confidence import normalize_confidence
from src.analysis.prompts import (
    NEWS_SYSTEM_PROMPT,
    NEWS_WEB_SEARCH_USER_PROMPT,
    SEC_SYSTEM_PROMPT,
    SEC_USER_PROMPT,
    TRENDS_SYSTEM_PROMPT,
    TRENDS_USER_PROMPT,
)
from src.data.sec_edgar import SECFiling, format_sections_for_prompt
from src.data.trends import TrendsData, format_trends_for_prompt

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """A single analytical finding with a confidence rating."""

    category: str
    text: str
    confidence: str  # "High", "Medium", "Low", or "Insufficient Data"


@dataclass
class SourceAnalysis:
    """Analyzed output from one data source."""

    source_name: str
    findings: list[Finding] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """True if analysis completed without error."""
        return self.error is None

    def to_brief_text(self) -> str:
        """Format this analysis for inclusion in the synthesis prompt.

        Returns:
            Multi-line string with source header and confidence-tagged findings.
        """
        if self.error:
            return f"=== {self.source_name} ===\n[Data unavailable: {self.error}]\n"
        lines = [f"=== {self.source_name} ==="]
        for f in self.findings:
            lines.append(f"[{f.confidence}] {f.category}: {f.text}")
        return "\n".join(lines) + "\n"


def analyze_all_sources(
    company_name: str,
    ticker: str,
    filing: SECFiling,
    trends_data: TrendsData,
) -> list[SourceAnalysis]:
    """Run per-source Claude analysis for all three sources concurrently.

    Args:
        company_name: Legal company name.
        ticker: Stock ticker symbol.
        filing: Fetched SEC filing data.
        trends_data: Fetched Google Trends data.

    Returns:
        List of three SourceAnalysis results (SEC, News, Trends).
    """
    return asyncio.run(
        _analyze_all_async(company_name, ticker, filing, trends_data)
    )


async def _analyze_all_async(
    company_name: str,
    ticker: str,
    filing: SECFiling,
    trends_data: TrendsData,
) -> list[SourceAnalysis]:
    """Fire all three Claude analysis calls concurrently via asyncio.gather."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    tasks = [
        _analyze_sec(client, company_name, ticker, filing),
        _analyze_news_web(client, company_name, ticker),
        _analyze_trends(client, company_name, ticker, trends_data),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    source_names = ["SEC Filing", "Recent News", "Google Trends"]
    analyses: list[SourceAnalysis] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Analysis task failed for %s: %s", source_names[i], result)
            analyses.append(SourceAnalysis(source_name=source_names[i], error=str(result)))
        else:
            analyses.append(result)

    return analyses


async def _analyze_sec(
    client: anthropic.AsyncAnthropic,
    company_name: str,
    ticker: str,
    filing: SECFiling,
) -> SourceAnalysis:
    """Analyze SEC filing data with Claude."""
    if filing.fetch_error:
        return SourceAnalysis(source_name="SEC Filing", error=filing.fetch_error)

    user_prompt = SEC_USER_PROMPT.format(
        company_name=company_name,
        ticker=ticker,
        filing_text=format_sections_for_prompt(filing),
    )
    return await _call_claude(client, "SEC Filing", SEC_SYSTEM_PROMPT, user_prompt)


async def _analyze_news_web(
    client: anthropic.AsyncAnthropic,
    company_name: str,
    ticker: str,
) -> SourceAnalysis:
    """Search the web for recent news and analyze it via Claude's built-in web search."""
    user_prompt = NEWS_WEB_SEARCH_USER_PROMPT.format(
        company_name=company_name,
        ticker=ticker if ticker and ticker.upper() != "N/A" else company_name,
    )
    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=CLAUDE_MAX_TOKENS_PER_SOURCE,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=NEWS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        spend.record_usage(CLAUDE_MODEL_FAST, response.usage)
        # Web search responses have multiple content blocks; take the last text block
        raw_text = next(
            (b.text for b in reversed(response.content) if b.type == "text"),
            "",
        )
        findings = _parse_findings(raw_text, "Recent News")
        return SourceAnalysis(
            source_name="Recent News",
            findings=findings,
            raw_response=raw_text,
        )
    except Exception as exc:
        logger.error("Web search news analysis failed: %s", exc)
        return SourceAnalysis(source_name="Recent News", error=str(exc))


async def _analyze_trends(
    client: anthropic.AsyncAnthropic,
    company_name: str,
    ticker: str,
    trends_data: TrendsData,
) -> SourceAnalysis:
    """Analyze Google Trends data with Claude."""
    if trends_data.fetch_error:
        return SourceAnalysis(source_name="Google Trends", error=trends_data.fetch_error)

    user_prompt = TRENDS_USER_PROMPT.format(
        company_name=company_name,
        ticker=ticker,
        trends_text=format_trends_for_prompt(trends_data),
    )
    return await _call_claude(client, "Google Trends", TRENDS_SYSTEM_PROMPT, user_prompt)


async def _call_claude(
    client: anthropic.AsyncAnthropic,
    source_name: str,
    system_prompt: str,
    user_prompt: str,
) -> SourceAnalysis:
    """Make one Claude API call and parse the JSON response into a SourceAnalysis.

    Args:
        client: Async Anthropic client.
        source_name: Display name for this data source.
        system_prompt: System prompt defining the analytical framework.
        user_prompt: User prompt containing the source data.

    Returns:
        SourceAnalysis with parsed findings, or error set if the call fails.
    """
    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=CLAUDE_MAX_TOKENS_PER_SOURCE,
            temperature=CLAUDE_TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        spend.record_usage(CLAUDE_MODEL_FAST, response.usage)
        raw_text = response.content[0].text
        findings = _parse_findings(raw_text, source_name)
        return SourceAnalysis(
            source_name=source_name,
            findings=findings,
            raw_response=raw_text,
        )
    except Exception as exc:
        logger.error("Claude API call failed for %s: %s", source_name, exc)
        return SourceAnalysis(source_name=source_name, error=str(exc))


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


def _parse_findings(raw_text: str, source_name: str) -> list[Finding]:
    """Parse JSON findings from a Claude response.

    Handles both pure-JSON responses and responses where JSON follows preamble
    text (as can happen with web search tool use).

    Args:
        raw_text: Raw text returned by Claude (expected to be a JSON object).
        source_name: Used only for warning logs.

    Returns:
        List of Finding objects. Returns a single low-confidence finding on parse failure.
    """
    for candidate in (raw_text, _extract_json(raw_text)):
        try:
            # strict=False tolerates literal newlines/tabs the model may leave
            # unescaped inside finding text, avoiding silent parse failures.
            data = json.loads(candidate, strict=False)
            return [
                Finding(
                    category=item.get("category", "General"),
                    text=item.get("text", ""),
                    confidence=normalize_confidence(item.get("confidence", "Insufficient Data")),
                )
                for item in data.get("findings", [])
                if item.get("text")
            ]
        except (json.JSONDecodeError, AttributeError):
            continue

    logger.warning("Could not parse findings JSON for %s. Preview: %s", source_name, raw_text[:200])
    return [
        Finding(
            category="Parse Error",
            text=f"Response could not be parsed as JSON. Preview: {raw_text[:300]}",
            confidence="Low",
        )
    ]
