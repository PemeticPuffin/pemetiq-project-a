"""Regenerate the cached sample briefs (src/ui/samples/*.json).

Runs the real single-company pipeline for each sample company and stores the
result as a JSON fixture. Costs a few live API calls per company — run
occasionally (e.g. after a prompt change or when samples feel stale), then
commit the updated JSON.

Usage:  venv/bin/python generate_samples.py [slug ...]
        (no args = regenerate all samples)
"""
import datetime
import sys
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

from src.analysis.drift import detect_drift
from src.analysis.news_drift import detect_news_drift
from src.analysis.per_source import analyze_all_sources
from src.analysis.synthesis import synthesize
from src.data.sec_edgar import fetch_comparison_filings
from src.data.trends import fetch_trends
from src.entity_resolver import resolve_company
from src.ui.samples import SAMPLES, save_sample


def generate(slug: str, query: str) -> None:
    print(f"── {slug}: resolving {query!r}…")
    entity = resolve_company(query)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_cmp = pool.submit(fetch_comparison_filings, entity.cik, entity.legal_name, "yoy")
        f_trends = pool.submit(fetch_trends, entity.legal_name, entity.ticker)
        current, comparable, basis = f_cmp.result()
        trends_data = f_trends.result()

    prior_period = ""
    if comparable is not None and comparable.report_date:
        try:
            prior_period = datetime.date.fromisoformat(
                comparable.report_date
            ).strftime("%b %Y")
        except ValueError:
            pass

    print(f"   analyzing sources + drift…")
    with ThreadPoolExecutor(max_workers=4) as pool:
        f_analyses = pool.submit(
            analyze_all_sources,
            company_name=entity.legal_name,
            ticker=entity.ticker,
            filing=current,
            trends_data=trends_data,
        )
        f_drift = pool.submit(detect_drift, current, comparable, basis)
        f_news_drift = pool.submit(
            detect_news_drift, entity.legal_name, entity.ticker, prior_period
        )
        analyses = f_analyses.result()
        drift = f_drift.result()
        news_drift = f_news_drift.result()

    print(f"   synthesizing…")
    synthesis = synthesize(
        company_name=entity.legal_name,
        ticker=entity.ticker,
        source_analyses=analyses,
    )

    path = save_sample(slug, {
        "entity": entity,
        "analyses": analyses,
        "synthesis": synthesis,
        "drift": drift,
        "news_drift": news_drift,
    })
    n_findings = sum(len(a.findings) for a in analyses)
    print(f"   saved {path.name}: {n_findings} findings, "
          f"{len(synthesis.contradictions)} contradictions, "
          f"drift={'yes' if drift and drift.available else 'no'}, "
          f"news_drift={'yes' if news_drift and news_drift.available else 'no'}")


if __name__ == "__main__":
    slugs = sys.argv[1:] or list(SAMPLES)
    for slug in slugs:
        generate(slug, SAMPLES[slug])
