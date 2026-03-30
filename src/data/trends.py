"""Fetch Google Trends search interest data via pytrends."""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrendsData:
    """Google Trends data for a company."""

    company_name: str
    ticker: str
    # Weekly interest over time: list of {"date": "YYYY-MM-DD", "value": int}
    interest_over_time: list[dict] = field(default_factory=list)
    # Related queries: {"top": [...], "rising": [...]}
    related_queries: dict = field(default_factory=dict)
    fetch_error: Optional[str] = None


def fetch_trends(company_name: str, ticker: str) -> TrendsData:
    """Fetch 90-day Google Trends data for a company.

    Falls back gracefully if pytrends is unavailable or Google rate-limits.

    Args:
        company_name: Company name to use as the search keyword.
        ticker: Stock ticker (used as fallback keyword if name yields no data).

    Returns:
        TrendsData with interest_over_time and related_queries, or fetch_error set.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return TrendsData(
            company_name=company_name,
            ticker=ticker,
            fetch_error="pytrends not installed",
        )

    short_name = _shorten_name(company_name)

    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        keyword = short_name

        pytrends.build_payload([keyword], timeframe="today 3-m", geo="US")
        iot_df = pytrends.interest_over_time()

        interest_over_time: list[dict] = []
        if iot_df is not None and not iot_df.empty and keyword in iot_df.columns:
            for date, row in iot_df.iterrows():
                interest_over_time.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": int(row[keyword]),
                })

        related_queries: dict = {"top": [], "rising": []}
        try:
            rq = pytrends.related_queries()
            if rq and keyword in rq:
                top_df = rq[keyword].get("top")
                rising_df = rq[keyword].get("rising")
                if top_df is not None and not top_df.empty:
                    related_queries["top"] = top_df.head(10).to_dict("records")
                if rising_df is not None and not rising_df.empty:
                    related_queries["rising"] = rising_df.head(10).to_dict("records")
        except Exception as exc:
            logger.warning("Could not fetch related queries: %s", exc)

        logger.info(
            "Fetched %d trend data points for %s", len(interest_over_time), company_name
        )
        return TrendsData(
            company_name=company_name,
            ticker=ticker,
            interest_over_time=interest_over_time,
            related_queries=related_queries,
        )

    except Exception as exc:
        # Google rate-limits aggressively — this is expected and non-fatal
        logger.warning("Google Trends fetch failed for %s: %s", company_name, exc)
        return TrendsData(
            company_name=company_name,
            ticker=ticker,
            fetch_error=str(exc),
        )


def format_trends_for_prompt(trends_data: TrendsData) -> str:
    """Format TrendsData into a compact string suitable for an LLM prompt.

    Args:
        trends_data: Populated TrendsData instance.

    Returns:
        Multi-line string summarizing search interest trends.
    """
    if trends_data.fetch_error:
        return f"[Google Trends data unavailable: {trends_data.fetch_error}]"

    lines = [f"Google Trends (US, last 90 days) for '{trends_data.company_name}':\n"]

    if trends_data.interest_over_time:
        values = [p["value"] for p in trends_data.interest_over_time]
        avg = sum(values) / len(values)
        peak = max(values)
        recent = values[-4:] if len(values) >= 4 else values
        recent_avg = sum(recent) / len(recent)
        trend_dir = "up" if recent_avg > avg else "down"

        lines.append(f"Average interest (0–100 scale): {avg:.1f}")
        lines.append(f"Peak interest: {peak}")
        lines.append(f"Recent 4-week trend: {trend_dir} (recent avg {recent_avg:.1f} vs overall {avg:.1f})")

        # Include last 12 weeks of data points
        lines.append("\nWeekly interest (last 12 weeks):")
        for point in trends_data.interest_over_time[-12:]:
            lines.append(f"  {point['date']}: {point['value']}")
    else:
        lines.append("No interest-over-time data returned.")

    if trends_data.related_queries.get("top"):
        lines.append("\nTop related queries:")
        for q in trends_data.related_queries["top"][:5]:
            lines.append(f"  - {q.get('query', '')} (value: {q.get('value', '')})")

    if trends_data.related_queries.get("rising"):
        lines.append("\nRising related queries:")
        for q in trends_data.related_queries["rising"][:5]:
            lines.append(f"  - {q.get('query', '')} (value: {q.get('value', '')})")

    return "\n".join(lines)


def _shorten_name(legal_name: str) -> str:
    """Strip common legal suffixes for cleaner Trends keyword."""
    import re
    suffixes = [
        r",?\s+Inc\.?$", r",?\s+Corp\.?$", r",?\s+Corporation$",
        r",?\s+Ltd\.?$", r",?\s+LLC\.?$", r",?\s+Limited$",
        r",?\s+PLC\.?$", r",?\s+Co\.?$",
    ]
    name = legal_name.strip()
    for suffix in suffixes:
        name = re.sub(suffix, "", name, flags=re.IGNORECASE).strip()
    return name
