"""Autonomous sample-lineup curator for Cadillaq.

Monthly (via GitHub Actions) this:
  1. Asks Claude — grounded with web search — which public US companies have the
     most demo-worthy competitive-intelligence narratives right now, given the
     currently featured set (with hysteresis, so the lineup evolves, not thrashes).
  2. Validates each pick resolves to a US public company on SEC EDGAR.
  3. Runs the real pipeline for newly chosen companies and QUALITY-GATES each
     one — a sample is only published if it has an executive summary, at least
     two working sources, and available narrative drift. Incumbents that survive
     are kept as-is (no needless regeneration).
  4. Updates src/ui/samples/manifest.json + fixtures and writes
     curation_summary.md (used as the pull-request body).

Nothing here publishes to the live site: the GitHub Actions workflow opens a
pull request with the changes for Aaron to approve.

Usage:
    python curate_samples.py            # full run (selection + generation)
    python curate_samples.py --dry-run  # selection only, no pipeline/API cost beyond the picker
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

from config import CLAUDE_MODEL
from generate_samples import generate
from src.entity_resolver import resolve_company
from src.ui.samples import SAMPLES_DIR, list_samples, load_sample, write_manifest

TARGET_SIZE = 3          # how many samples to feature
MAX_SWAPS = 1            # hysteresis: at most this many changes per run

SELECTOR_SYSTEM = """You curate the sample companies featured on Cadillaq, a competitive-intelligence \
tool for investors, corporate strategy teams, and business operators. Each sample is a full CI brief \
(SEC filings + recent news + search trends, with cross-source contradiction detection and year-over-year \
narrative-drift analysis).

Your job: choose the public US companies whose narratives are the most compelling to SHOWCASE right now to \
that audience — names with active investor attention, recent earnings, notable news, or contested \
narratives that make the tool look sharp.

Hard constraints on every pick:
- US-listed company that files with the SEC (10-K / 10-Q). No foreign private issuers, funds, or SPACs.
- At least ~1 year of filing history — the tool compares against the year-ago quarter, so avoid very \
recent IPOs.
- Favor variety across sectors; avoid two companies with near-identical stories.

Use web search to ground your choices in what is actually happening in the market as of today.

Apply hysteresis: KEEP currently featured companies that are still highly relevant. Change at most the \
number of slots you are told is allowed, swapping out only those that have gone stale for clearly more \
timely names. If the current lineup is still great, change nothing.

Respond with ONLY a JSON object, no prose:
{"lineup": [{"ticker": "TICK", "label": "Short Name", "reason": "one sentence on why it's timely"}],
 "summary": "2-3 sentences explaining what changed vs the current lineup and why"}"""


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _extract_json(text: str) -> str:
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


def select_lineup(current: list[dict]) -> dict:
    """Ask Claude (web-search grounded) for the ideal lineup."""
    current_desc = ", ".join(f"{s['label']} ({s.get('ticker','?')})" for s in current) or "(none)"
    user = (
        f"Today is {datetime.date.today():%B %d, %Y}.\n"
        f"Currently featured ({len(current)}): {current_desc}.\n"
        f"Choose the ideal {TARGET_SIZE}-company lineup. You may change at most {MAX_SWAPS} "
        f"of the current picks."
    )
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SELECTOR_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    text = next((b.text for b in reversed(resp.content) if b.type == "text"), "")
    data = json.loads(_extract_json(text))
    data["lineup"] = data["lineup"][:TARGET_SIZE]
    return data


def _reconcile(lineup: list[dict], current: list[dict]) -> None:
    """Match picks to incumbents by ticker; reuse their slug + label so fixture
    filenames stay stable and a re-picked company is recognized as a keep."""
    by_ticker = {s.get("ticker", "").upper(): s for s in current if s.get("ticker")}
    for item in lineup:
        inc = by_ticker.get(item.get("ticker", "").upper())
        if inc:
            item["slug"] = inc["slug"]
            item["label"] = inc["label"]
            item["generated_on"] = inc.get("generated_on", "")
            item["is_incumbent"] = True
        else:
            item["slug"] = _slug(item["label"])
            item["is_incumbent"] = False


def quality_ok(slug: str) -> bool:
    """A sample is publishable only if the brief is complete."""
    try:
        r = load_sample(slug)
    except Exception:
        return False
    synth = r["synthesis"]
    live_sources = sum(1 for a in r["analyses"] if not a.error and a.findings)
    drift_ok = bool(r["drift"] and r["drift"].available)
    return bool(synth.executive_summary) and live_sources >= 2 and drift_ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Select only; do not run the pipeline or change files.")
    args = ap.parse_args()

    current = list_samples()
    print(f"Current lineup: {[s['label'] for s in current]}")

    picked = select_lineup(current)
    _reconcile(picked["lineup"], current)
    print(f"\nProposed lineup:")
    for item in picked["lineup"]:
        flag = "keep" if item["is_incumbent"] else "NEW"
        print(f"  [{flag}] {item['label']} ({item['ticker']}) — {item['reason']}")
    print(f"\nRationale: {picked['summary']}")

    if args.dry_run:
        print("\n(dry run — no files changed)")
        return

    # Generate only the new picks; keep surviving incumbents as-is.
    final: list[dict] = []
    for item in picked["lineup"]:
        slug = item["slug"]
        if item["is_incumbent"] and quality_ok(slug):
            final.append(_manifest_entry(item, keep=True))
            continue
        if not _validate(item):
            print(f"  ✗ {item['label']}: failed EDGAR validation — skipped")
            continue
        if _generate_gated(slug, item["ticker"]):
            item["generated_on"] = datetime.date.today().isoformat()
            final.append(_manifest_entry(item, keep=False))
        else:
            print(f"  ✗ {item['label']}: failed quality gate after retry — skipped")

    # Backfill from surviving incumbents if we lost picks, to keep the lineup full.
    if len(final) < TARGET_SIZE:
        for s in current:
            if len(final) >= TARGET_SIZE:
                break
            if s["slug"] not in {f["slug"] for f in final} and quality_ok(s["slug"]):
                final.append(s)

    if [f["slug"] for f in final] == [s["slug"] for s in current]:
        print("\nNo change — current lineup is still the most relevant. Nothing to propose.")
        return

    _prune_dropped({f["slug"] for f in final})
    write_manifest(final)
    _write_summary(current, final, picked["summary"])
    print(f"\nFinal lineup: {[f['label'] for f in final]}")


def _validate(item: dict) -> bool:
    try:
        resolve_company(item["ticker"])
        return True
    except Exception:
        return False


def _generate_gated(slug: str, ticker: str) -> bool:
    for attempt in (1, 2):
        try:
            generate(slug, ticker)
        except Exception as exc:
            print(f"    generation attempt {attempt} errored: {exc}")
            continue
        if quality_ok(slug):
            return True
        print(f"    attempt {attempt}: incomplete, retrying…")
    (SAMPLES_DIR / f"{slug}.json").unlink(missing_ok=True)
    return False


def _manifest_entry(item: dict, keep: bool) -> dict:
    return {
        "slug": item["slug"],
        "label": item["label"],
        "ticker": item["ticker"],
        "generated_on": item.get("generated_on") or datetime.date.today().isoformat(),
    }


def _prune_dropped(keep_slugs: set[str]) -> None:
    for p in SAMPLES_DIR.glob("*.json"):
        if p.name != "manifest.json" and p.stem not in keep_slugs:
            print(f"  removing dropped sample: {p.name}")
            p.unlink()


def _write_summary(before: list[dict], after: list[dict], rationale: str) -> None:
    before_s = {s["slug"] for s in before}
    after_s = {s["slug"] for s in after}
    added = [s for s in after if s["slug"] not in before_s]
    removed = [s for s in before if s["slug"] not in after_s]
    lines = ["## Monthly sample-lineup update", "", rationale, ""]
    if added:
        lines.append("**Added:** " + ", ".join(f"{s['label']} ({s['ticker']})" for s in added))
    if removed:
        lines.append("**Removed:** " + ", ".join(s["label"] for s in removed))
    if not added and not removed:
        lines.append("_No changes — current lineup is still the most relevant._")
    lines += ["", "**Featured after this update:** "
              + ", ".join(f"{s['label']} ({s['ticker']})" for s in after)]
    (SAMPLES_DIR.parent.parent.parent / "curation_summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
