"""Fetch and parse relevant sections from the latest SEC 10-K or 10-Q filing."""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import requests

from config import SEC_USER_AGENT, REQUEST_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_FILING_URL = "https://www.sec.gov/Archives/edgar/full-index/"
_HEADERS = {"User-Agent": SEC_USER_AGENT}

# Sections we want to extract from the filing.
# Each key maps to a list of patterns tried in order (first match wins).
# 10-K uses Item 1 (Business), Item 1A (Risk Factors), Item 7 (MD&A).
# 10-Q uses Item 1A (Risk Factors), Item 2 (MD&A); no standalone Business section.
_TARGET_SECTIONS: dict[str, list[re.Pattern]] = {
    "business": [
        re.compile(r"item\s*1[\.\s]+business(?!\s+combination)", re.IGNORECASE),
    ],
    "risk_factors": [
        re.compile(r"item\s*1a[\.\s]+risk\s+factors", re.IGNORECASE),
    ],
    "mda": [
        re.compile(r"item\s*7[\.\s]+management.{0,20}discussion", re.IGNORECASE),  # 10-K
        re.compile(r"item\s*2[\.\s]+management.{0,20}discussion", re.IGNORECASE),  # 10-Q
    ],
}

# Max chars per section sent to the LLM (~25K tokens worth is plenty)
_MAX_SECTION_CHARS = 30_000


@dataclass
class SECFiling:
    """Extracted content from an SEC filing."""

    form_type: str
    filed_date: str
    company_name: str
    cik: int
    sections: dict[str, str] = field(default_factory=dict)  # section_name → text
    fetch_error: Optional[str] = None


def fetch_latest_filing(cik: int, company_name: str) -> SECFiling:
    """Fetch the latest 10-K or 10-Q for a company and extract key sections.

    Args:
        cik: SEC CIK number.
        company_name: Human-readable company name (for logging).

    Returns:
        SECFiling with extracted section text, or fetch_error set if failed.
    """
    try:
        form_type, filed_date, doc_url = _get_latest_filing_url(cik)
        logger.info("Fetching %s filed %s for CIK %d", form_type, filed_date, cik)
        raw_text = _fetch_filing_text(doc_url)
        sections = _extract_sections(raw_text)
        return SECFiling(
            form_type=form_type,
            filed_date=filed_date,
            company_name=company_name,
            cik=cik,
            sections=sections,
        )
    except Exception as exc:
        logger.warning("SEC filing fetch failed for CIK %d: %s", cik, exc)
        return SECFiling(
            form_type="unknown",
            filed_date="unknown",
            company_name=company_name,
            cik=cik,
            fetch_error=str(exc),
        )


def _get_latest_filing_url(cik: int) -> tuple[str, str, str]:
    """Return (form_type, filed_date, primary_doc_url) for the latest 10-K or 10-Q.

    Args:
        cik: SEC CIK number.

    Returns:
        Tuple of form type string, ISO date string, and full URL to primary document.

    Raises:
        RuntimeError: If no 10-K or 10-Q is found or the request fails.
    """
    url = _SUBMISSIONS_URL.format(cik=cik)
    data = _get_json(url)

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accessions = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])

    for i, form in enumerate(forms):
        if form in ("10-K", "10-Q"):
            accession = accessions[i].replace("-", "")
            doc = primary_docs[i]
            url = (
                f"https://www.sec.gov/Archives/edgar/full-index/"
                f"{dates[i][:4]}/QTR{_quarter(dates[i])}/{accession}/{doc}"
            )
            # Use the index page URL pattern that always works
            index_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik}"
                f"/{accession}/{doc}"
            )
            return form, dates[i], index_url

    raise RuntimeError(f"No 10-K or 10-Q found for CIK {cik}")


def _fetch_filing_text(url: str) -> str:
    """Download and lightly clean filing text (strips HTML tags).

    Args:
        url: URL to the primary filing document.

    Returns:
        Plain-text content of the filing.
    """
    resp = _get_raw(url)
    text = resp.text

    # Strip HTML if present
    if "<html" in text.lower() or "<!doctype" in text.lower():
        text = re.sub(r"<[^>]+>", " ", text)
        # Named entities
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&#160;", " ", text)   # non-breaking space (common in XBRL filings)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&rsquo;|&#8217;", "'", text)
        text = re.sub(r"&ldquo;|&#8220;", '"', text)
        text = re.sub(r"&rdquo;|&#8221;", '"', text)
        text = re.sub(r"&#\d+;", " ", text)   # any remaining numeric entities

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _extract_sections(text: str) -> dict[str, str]:
    """Extract Business, Risk Factors, and MD&A sections from filing text.

    Args:
        text: Full plain-text content of the filing.

    Returns:
        Dict mapping section key to extracted text (may be empty if not found).
    """
    results: dict[str, str] = {}

    # Find all section header positions.
    # Use the LAST match for each section: table-of-contents entries appear early
    # in the document, while actual section headers appear later.
    positions: list[tuple[str, int]] = []
    for name, patterns in _TARGET_SECTIONS.items():
        best: Optional[int] = None
        for pattern in patterns:
            matches = list(pattern.finditer(text))
            if matches:
                # Last match is the real section, not a TOC reference
                best = matches[-1].start()
                break  # first pattern family that has any match wins
        if best is not None:
            positions.append((name, best))

    if not positions:
        logger.warning("No target sections found in filing text")
        return results

    # Sort by position
    positions.sort(key=lambda x: x[1])

    for idx, (name, start) in enumerate(positions):
        end = positions[idx + 1][1] if idx + 1 < len(positions) else len(text)
        section_text = text[start:end].strip()
        # Cap length before sending to LLM
        if len(section_text) > _MAX_SECTION_CHARS:
            section_text = section_text[:_MAX_SECTION_CHARS] + "\n\n[truncated]"
        results[name] = section_text

    return results


def format_sections_for_prompt(filing: SECFiling) -> str:
    """Format an SECFiling into a compact string suitable for an LLM prompt.

    Args:
        filing: Populated SECFiling instance.

    Returns:
        Multi-section string, or an unavailability note if fetch failed.
    """
    if filing.fetch_error:
        return f"[SEC data unavailable: {filing.fetch_error}]"
    parts = [f"SEC {filing.form_type} filed {filing.filed_date} — {filing.company_name}\n"]
    for name, text in filing.sections.items():
        parts.append(f"=== {name.upper().replace('_', ' ')} ===\n{text}\n")
    return "\n".join(parts)


def _quarter(date_str: str) -> int:
    """Return the fiscal quarter (1–4) for an ISO date string."""
    month = int(date_str[5:7])
    return (month - 1) // 3 + 1


def _get_json(url: str) -> dict:
    """GET a URL and parse JSON with retry logic."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                logger.warning("Retry %d/%d for %s: %s", attempt + 1, MAX_RETRIES, url, exc)
                time.sleep(1)
            else:
                raise RuntimeError(f"Request failed after retries: {exc}") from exc


def _get_raw(url: str) -> requests.Response:
    """GET a URL and return the raw response with retry logic."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                logger.warning("Retry %d/%d for %s: %s", attempt + 1, MAX_RETRIES, url, exc)
                time.sleep(1)
            else:
                raise RuntimeError(f"Request failed after retries: {exc}") from exc
