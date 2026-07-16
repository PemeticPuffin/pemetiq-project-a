"""Cached sample briefs — real pipeline runs stored as JSON fixtures.

Samples are generated offline with generate_samples.py (repo root) and loaded
instantly in the app, so first-time visitors see a complete brief without
waiting on (or paying for) a live run. `raw_response` fields are stripped on
save: they are debug-only and never rendered.
"""
from __future__ import annotations

import dataclasses
import json
from datetime import date
from pathlib import Path

from src.analysis.drift import DriftItem, DriftResult
from src.analysis.news_drift import NewsDriftItem, NewsDriftResult
from src.analysis.per_source import Finding, SourceAnalysis
from src.analysis.synthesis import Contradiction, SynthesisResult
from src.entity_resolver import ResolvedEntity

SAMPLES_DIR = Path(__file__).parent / "samples"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"


def list_samples() -> list[dict]:
    """Ordered sample metadata from the manifest, filtered to fixtures present.

    Each entry: {"slug", "label", "ticker", "generated_on"}. The curator owns
    the manifest; the app only reads it, so add/remove is a data operation.
    """
    if MANIFEST_PATH.exists():
        data = json.loads(MANIFEST_PATH.read_text())
        return [s for s in data.get("samples", []) if sample_available(s["slug"])]
    # Fallback: derive from whatever fixtures exist (manifest missing).
    return [
        {"slug": p.stem, "label": p.stem.title(), "ticker": "", "generated_on": ""}
        for p in sorted(SAMPLES_DIR.glob("*.json"))
        if p.name != "manifest.json"
    ]


def write_manifest(samples: list[dict]) -> None:
    """Persist the featured-sample lineup (used by the curator)."""
    MANIFEST_PATH.write_text(
        json.dumps({"updated": date.today().isoformat(), "samples": samples}, indent=1)
    )


def _strip_raw(d: dict) -> dict:
    d.pop("raw_response", None)
    return d


def save_sample(slug: str, result: dict) -> Path:
    """Serialize a completed single-company pipeline result to JSON."""
    drift = result.get("drift")
    news_drift = result.get("news_drift")
    payload = {
        "generated_on": date.today().isoformat(),
        "entity": dataclasses.asdict(result["entity"]),
        "analyses": [_strip_raw(dataclasses.asdict(a)) for a in result["analyses"]],
        "synthesis": _strip_raw(dataclasses.asdict(result["synthesis"])),
        "drift": _strip_raw(dataclasses.asdict(drift)) if drift else None,
        "news_drift": _strip_raw(dataclasses.asdict(news_drift)) if news_drift else None,
    }
    SAMPLES_DIR.mkdir(exist_ok=True)
    path = SAMPLES_DIR / f"{slug}.json"
    path.write_text(json.dumps(payload, indent=1))
    return path


def sample_available(slug: str) -> bool:
    return (SAMPLES_DIR / f"{slug}.json").exists()


def load_sample(slug: str) -> dict:
    """Load a fixture back into the exact objects app.py stores in session state."""
    d = json.loads((SAMPLES_DIR / f"{slug}.json").read_text())

    synthesis_d = dict(d["synthesis"])
    synthesis_d["contradictions"] = [
        Contradiction(**c) for c in synthesis_d.get("contradictions", [])
    ]

    drift = None
    if d.get("drift"):
        drift_d = dict(d["drift"])
        drift_d["items"] = [DriftItem(**i) for i in drift_d.get("items", [])]
        drift = DriftResult(**drift_d)

    news_drift = None
    if d.get("news_drift"):
        nd = dict(d["news_drift"])
        nd["items"] = [NewsDriftItem(**i) for i in nd.get("items", [])]
        news_drift = NewsDriftResult(**nd)

    return {
        "entity": ResolvedEntity(**d["entity"]),
        "analyses": [
            SourceAnalysis(
                source_name=a["source_name"],
                findings=[Finding(**f) for f in a.get("findings", [])],
                error=a.get("error"),
            )
            for a in d["analyses"]
        ],
        "synthesis": SynthesisResult(**synthesis_d),
        "drift": drift,
        "news_drift": news_drift,
        "sample_generated_on": d["generated_on"],
    }
