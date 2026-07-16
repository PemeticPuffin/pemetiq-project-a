"""Daily API spend ledger and per-visitor rate limiting.

Cadillaq is public and unauthenticated, and every run costs real money. Two
independent guards sit in front of a live run:

  * Daily spend cap — each Claude call records its actual token + web-search
    cost; once the day's total passes DAILY_SPEND_LIMIT_USD, live runs are
    refused and visitors are pointed at the cached sample briefs.
  * Per-visitor cap — FREE_RUNS_PER_DAY live runs per IP per rolling 24h, so
    one visitor can't drain the day's budget alone.

Both guards fail OPEN: any error in this module lets the run proceed. A
bookkeeping bug must never take the app down.

Ledger: data/spend_ledger.json. Railway's filesystem is ephemeral, so a
redeploy resets the day's total — acceptable for a safety valve. The Anthropic
Console monthly cap remains the real backstop.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Pricing ────────────────────────────────────────────────────────────────
# USD per million tokens (input, output), per platform.claude.com — checked
# 2026-07-16. Matched by prefix so dated model IDs resolve too.
_PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
_CACHE_READ_MULTIPLIER = 0.10    # cached input bills at ~0.1x
_CACHE_WRITE_MULTIPLIER = 1.25   # 5-minute TTL cache writes bill at 1.25x
_WEB_SEARCH_USD = 0.01           # $10 per 1,000 searches; errors aren't billed

# Pre-run estimate only — the ledger records actual cost after the fact.
ESTIMATED_RUN_USD = 0.20

DAILY_SPEND_LIMIT_USD = float(os.getenv("DAILY_SPEND_LIMIT_USD", "5.00"))
FREE_RUNS_PER_DAY = int(os.getenv("FREE_RUNS_PER_DAY", "5"))

_LEDGER_PATH = Path(__file__).parent.parent / "data" / "spend_ledger.json"

_lock = threading.Lock()
_ip_hits: dict[str, list[float]] = {}


def _rates(model: str) -> tuple[float, float]:
    """Return (input, output) USD per million tokens for a model ID."""
    for prefix, rates in _PRICES.items():
        if model.startswith(prefix):
            return rates
    # Unknown model: bill at the highest known rate so we never under-count.
    logger.warning("No pricing for model %r; using highest known rate.", model)
    return max(_PRICES.values())


def cost_of(model: str, usage) -> float:
    """Compute the USD cost of one Claude API call from its usage object."""
    in_rate, out_rate = _rates(model)

    def _n(attr: str) -> int:
        return getattr(usage, attr, 0) or 0

    tokens = (
        _n("input_tokens") * in_rate
        + _n("cache_creation_input_tokens") * in_rate * _CACHE_WRITE_MULTIPLIER
        + _n("cache_read_input_tokens") * in_rate * _CACHE_READ_MULTIPLIER
        + _n("output_tokens") * out_rate
    ) / 1_000_000

    server_tools = getattr(usage, "server_tool_use", None)
    searches = getattr(server_tools, "web_search_requests", 0) or 0
    return tokens + searches * _WEB_SEARCH_USD


def record_usage(model: str, usage) -> float:
    """Append one call's actual cost to today's ledger. Returns the cost."""
    try:
        cost = cost_of(model, usage)
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "date": _today(),
            "model": model,
            "cost_usd": round(cost, 6),
        }
        with _lock:
            ledger = _load()
            ledger.append(entry)
            _save(ledger)
        return cost
    except Exception:  # never let accounting break a run
        logger.exception("Failed to record spend for %s", model)
        return 0.0


def daily_total() -> float:
    """Total recorded spend for today (UTC)."""
    try:
        today = _today()
        with _lock:
            ledger = _load()
        return round(sum(e.get("cost_usd", 0) for e in ledger if e.get("date") == today), 6)
    except Exception:
        logger.exception("Failed to read spend ledger")
        return 0.0


def status() -> dict:
    """Today's spend summary (for ops/debugging, not shown to visitors)."""
    spent = daily_total()
    return {
        "date": _today(),
        "spent_usd": round(spent, 4),
        "limit_usd": DAILY_SPEND_LIMIT_USD,
        "remaining_usd": round(max(0.0, DAILY_SPEND_LIMIT_USD - spent), 4),
        "pct_used": round(min(spent / DAILY_SPEND_LIMIT_USD * 100, 100), 1)
        if DAILY_SPEND_LIMIT_USD else 0.0,
    }


def budget_exhausted() -> bool:
    """True if another run would likely push today past the spend limit."""
    return (daily_total() + ESTIMATED_RUN_USD) > DAILY_SPEND_LIMIT_USD


# ── Per-visitor rate limiting ──────────────────────────────────────────────
def client_ip() -> str:
    """Best-effort visitor IP. Returns "" when unavailable (fails open)."""
    try:
        import streamlit as st

        headers = st.context.headers or {}
        # Cloudflare proxies every pemetiq.com hostname, so this is the real IP.
        ip = headers.get("Cf-Connecting-Ip") or headers.get("CF-Connecting-IP")
        if not ip:
            fwd = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for") or ""
            ip = fwd.split(",")[0].strip()
        return ip or ""
    except Exception:
        return ""


def _prune(hits: list[float], now: float) -> list[float]:
    return [t for t in hits if now - t < 86400]


def runs_remaining(ip: str) -> int:
    if not ip:
        return FREE_RUNS_PER_DAY
    now = time.time()
    with _lock:
        hits = _prune(_ip_hits.get(ip, []), now)
        _ip_hits[ip] = hits
    return max(0, FREE_RUNS_PER_DAY - len(hits))


def _record_run(ip: str) -> None:
    if not ip:
        return
    now = time.time()
    with _lock:
        _ip_hits[ip] = _prune(_ip_hits.get(ip, []), now) + [now]


def gate() -> tuple[bool, str]:
    """Check both guards before a live run. Records the visitor's run if allowed.

    Returns (allowed, message). The message is visitor-facing when refused.
    """
    try:
        if budget_exhausted():
            return False, (
                "Cadillaq has reached its daily analysis budget — live runs are "
                "paused until tomorrow so the tool stays free. The sample briefs "
                "below are full real runs and are still available."
            )
        ip = client_ip()
        if runs_remaining(ip) <= 0:
            return False, (
                f"You've used your {FREE_RUNS_PER_DAY} live briefs for today. "
                "The sample briefs below are still available, or come back "
                "tomorrow for more."
            )
        _record_run(ip)
        return True, ""
    except Exception:  # fail open — never block a run on a guard bug
        logger.exception("Spend/rate gate failed; allowing run")
        return True, ""


# ── Ledger I/O ─────────────────────────────────────────────────────────────
def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _load() -> list[dict]:
    if not _LEDGER_PATH.exists():
        return []
    try:
        return json.loads(_LEDGER_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save(ledger: list[dict]) -> None:
    # Keep the file small — only the last 30 days matter.
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=30)
    ).isoformat()
    ledger = [e for e in ledger if e.get("date", "") >= cutoff]
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_PATH.write_text(json.dumps(ledger, indent=1))
