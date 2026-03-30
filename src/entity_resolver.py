"""Resolve a company name or ticker to CIK, legal name, and ticker via SEC EDGAR."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

from config import SEC_USER_AGENT, REQUEST_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search and company search endpoints
_COMPANY_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{query}%22&forms=10-K"
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

_HEADERS = {"User-Agent": SEC_USER_AGENT}


@dataclass
class ResolvedEntity:
    """Fully resolved company identity from SEC EDGAR."""

    cik: int
    legal_name: str
    ticker: str


def resolve_company(query: str) -> ResolvedEntity:
    """Resolve a company name or ticker to its SEC identity.

    Tries ticker match first (exact, case-insensitive), then falls back to
    name fuzzy match against the SEC company tickers bulk file.

    Args:
        query: Company name (e.g. "Apple") or ticker (e.g. "AAPL").

    Returns:
        ResolvedEntity with cik, legal_name, and ticker.

    Raises:
        ValueError: If the company cannot be resolved.
    """
    tickers_data = _fetch_company_tickers()

    # --- 1. Exact ticker match ---
    normalized = query.strip().upper()
    for entry in tickers_data.values():
        if entry["ticker"].upper() == normalized:
            cik = int(entry["cik_str"])
            return ResolvedEntity(
                cik=cik,
                legal_name=entry["title"],
                ticker=entry["ticker"].upper(),
            )

    # --- 2. Name substring match (case-insensitive, prefer shorter names) ---
    query_lower = query.strip().lower()
    candidates: list[tuple[int, dict]] = []
    for entry in tickers_data.values():
        if query_lower in entry["title"].lower():
            candidates.append((len(entry["title"]), entry))

    if candidates:
        # Pick the shortest matching name to prefer "Apple Inc." over
        # "Apple Hospitality REIT" when the user types "Apple"
        candidates.sort(key=lambda x: x[0])
        best = candidates[0][1]
        cik = int(best["cik_str"])
        ticker = best["ticker"].upper()
        # Validate/enrich via submissions endpoint (gets confirmed ticker)
        try:
            ticker = _get_ticker_from_submissions(cik) or ticker
        except Exception:
            pass
        return ResolvedEntity(cik=cik, legal_name=best["title"], ticker=ticker)

    raise ValueError(
        f"Could not resolve '{query}' to a known SEC registrant. "
        "Try using the full legal name or ticker symbol."
    )


def _fetch_company_tickers() -> dict:
    """Fetch the SEC bulk company tickers file (cached by caller if needed).

    Returns:
        Dict keyed by ordinal, each value has keys: cik_str, title, ticker.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(
                _COMPANY_TICKERS_URL,
                headers=_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                logger.warning("Retrying company tickers fetch (%d/%d): %s", attempt + 1, MAX_RETRIES, exc)
                time.sleep(1)
            else:
                raise RuntimeError(f"Failed to fetch SEC company tickers: {exc}") from exc


def _get_ticker_from_submissions(cik: int) -> Optional[str]:
    """Fetch the primary ticker from the SEC submissions endpoint.

    Args:
        cik: Numeric CIK.

    Returns:
        Ticker string, or None if not found.
    """
    url = _SUBMISSIONS_URL.format(cik=cik)
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            tickers = data.get("tickers", [])
            return tickers[0].upper() if tickers else None
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                logger.warning("Retrying submissions fetch (%d/%d): %s", attempt + 1, MAX_RETRIES, exc)
                time.sleep(1)
            else:
                logger.warning("Could not fetch submissions for CIK %d: %s", cik, exc)
                return None
