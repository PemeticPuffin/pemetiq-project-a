"""Cadillaq — Competitive intelligence autopilot. Streamlit entry point."""

import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image as _Image

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

_ASSETS = Path(__file__).parent / "assets"

def _b64_img(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"

# ── Page config — must be the first Streamlit call ────────────────────────
st.set_page_config(
    page_title="Cadillaq | Pemetiq",
    page_icon=_Image.open(_ASSETS / "favicon.png"),
    layout="wide",
)

from src.analysis.drift import detect_drift
from src.analysis.per_source import analyze_all_sources
from src.analysis.synthesis import compare_synthesize, synthesize
from src.data.sec_edgar import fetch_comparison_filings, fetch_latest_filing
from src.data.trends import fetch_trends
from src.ui.pdf_export import generate_brief_pdf
from src.entity_resolver import ResolvedEntity, resolve_company
from src.ui.components import (
    render_company_brief,
    render_comparison_view,
    render_drift_section,
    render_footer,
    render_source_findings,
    render_synthesis_sections,
    render_takeaways_anchor,
    render_takeaways_section,
)
from src.ui.styling import CUSTOM_CSS

# ── Inject brand CSS ───────────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
_icon_uri = _b64_img(_ASSETS / "app-icon.png")
st.markdown(
    f"""
    <div class="ci-header">
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem">
            <img src="{_icon_uri}" style="height:44px;width:44px;border-radius:10px;flex-shrink:0;box-shadow:0 0 0 1.5px rgba(255,255,255,0.3),0 2px 8px rgba(0,0,0,0.25)">
            <div class="brand-label" style="margin-bottom:0">PEMETIQ</div>
        </div>
        <h1>Cadillaq — Competitive Intelligence Autopilot</h1>
        <p class="tagline">
            Pulls SEC filings, recent news, and search trends for any public US company —
            then surfaces contradictions, gaps, and signals that no single report will show you.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Mode toggle ────────────────────────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["Single company", "Compare two companies"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# ── Search inputs ──────────────────────────────────────────────────────────
if mode == "Single company":
    col_input, col_btn = st.columns([5, 1], gap="small")
    with col_input:
        query = st.text_input(
            label="Company",
            placeholder="Enter a company name or ticker — e.g. Palantir, MSFT, Nvidia",
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.button("Analyze", type="primary", use_container_width=True)
    query_b = ""
else:
    col_a, col_b, col_btn = st.columns([3, 3, 1], gap="small")
    with col_a:
        query = st.text_input(
            label="Company A",
            placeholder="Company A — e.g. Palantir",
            label_visibility="collapsed",
        )
    with col_b:
        query_b = st.text_input(
            label="Company B",
            placeholder="Company B — e.g. Snowflake",
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.button("Compare", type="primary", use_container_width=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "mode" not in st.session_state:
    st.session_state.mode = "single"


def _render_brief_header(entity, synthesis, analyses, drift) -> None:
    """Render the Executive Summary label and the Export PDF button."""
    col_hdr, col_btn = st.columns([5, 1])
    with col_hdr:
        st.markdown(
            '<div class="section-label">Executive Summary</div>'
            '<div class="section-subtitle">Synthesized from SEC filings, recent news, and search trend data.</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        pdf_bytes = generate_brief_pdf(entity, synthesis, analyses, drift)
        st.download_button(
            label="Export PDF",
            data=pdf_bytes,
            file_name=f"cadillaq_{entity.legal_name.lower().replace(' ', '_').replace(',', '')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _render_brief(entity, analyses, synthesis, drift=None) -> None:
    """Render the full CI brief (used when replaying a stored result)."""
    _render_brief_header(entity, synthesis, analyses, drift)
    render_company_brief(entity, synthesis)
    render_takeaways_anchor(synthesis.key_takeaways)
    render_drift_section(drift)
    render_synthesis_sections(synthesis)
    render_source_findings(analyses)
    render_takeaways_section(synthesis.key_takeaways)


def _resolve(query: str) -> tuple[ResolvedEntity, bool]:
    """Resolve a company query; return (entity, sec_fallback)."""
    try:
        return resolve_company(query.strip()), False
    except ValueError:
        return ResolvedEntity(cik=0, legal_name=query.strip().title(), ticker="N/A"), True


def _run_pipeline(entity: ResolvedEntity) -> dict:
    """Fetch data (parallel) and run per-source analysis for one company."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_filing = pool.submit(fetch_latest_filing, entity.cik, entity.legal_name)
        f_trends = pool.submit(fetch_trends, entity.legal_name, entity.ticker)
        filing = f_filing.result()
        trends_data = f_trends.result()
    analyses = analyze_all_sources(
        company_name=entity.legal_name,
        ticker=entity.ticker,
        filing=filing,
        trends_data=trends_data,
    )
    return {"entity": entity, "analyses": analyses}


# ── Pipeline ───────────────────────────────────────────────────────────────
if run_clicked:
    if mode == "Single company":
        if not query.strip():
            st.warning("Please enter a company name or ticker.")
        else:
            entity, fallback = _resolve(query)
            if fallback:
                st.warning(
                    f"**{entity.legal_name}** doesn't appear to be a publicly registered US company — "
                    "SEC filing data will be unavailable. Showing news and search trend analysis only."
                )

            status = st.status(f"Analyzing {entity.legal_name}…", expanded=True)

            # Placeholders in final display order — filled as each stage completes.
            slot_header = st.empty()
            slot_brief = st.empty()
            slot_anchor = st.empty()
            slot_drift = st.empty()
            slot_synth = st.empty()
            slot_find = st.empty()
            slot_take = st.empty()

            status.write("Fetching SEC filings, recent news, and search trends…")
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_cmp = pool.submit(fetch_comparison_filings, entity.cik, entity.legal_name)
                f_trends = pool.submit(fetch_trends, entity.legal_name, entity.ticker)
                current, comparable, basis = f_cmp.result()
                trends_data = f_trends.result()

            status.write("Analyzing sources and detecting narrative drift…")
            with ThreadPoolExecutor(max_workers=3) as pool:
                f_analyses = pool.submit(
                    analyze_all_sources,
                    company_name=entity.legal_name,
                    ticker=entity.ticker,
                    filing=current,
                    trends_data=trends_data,
                )
                f_drift = pool.submit(detect_drift, current, comparable, basis)
                analyses = f_analyses.result()

                status.write("Synthesizing cross-source brief…")
                f_synth = pool.submit(
                    synthesize,
                    company_name=entity.legal_name,
                    ticker=entity.ticker,
                    source_analyses=analyses,
                )

                # Reveal the drift beat as soon as it lands, before synthesis finishes.
                drift = f_drift.result()
                with slot_drift.container():
                    render_drift_section(drift)

                synthesis = f_synth.result()

            with slot_header.container():
                _render_brief_header(entity, synthesis, analyses, drift)
            with slot_brief.container():
                render_company_brief(entity, synthesis)
            with slot_anchor.container():
                render_takeaways_anchor(synthesis.key_takeaways)
            with slot_synth.container():
                render_synthesis_sections(synthesis)
            with slot_find.container():
                render_source_findings(analyses)
            with slot_take.container():
                render_takeaways_section(synthesis.key_takeaways)

            status.update(
                label=f"Brief ready — {entity.legal_name}", state="complete", expanded=False
            )

            st.session_state.mode = "single"
            st.session_state.result = {
                "entity": entity,
                "analyses": analyses,
                "synthesis": synthesis,
                "drift": drift,
            }
            render_footer()
            st.stop()

    else:  # Compare two companies
        if not query.strip() or not query_b.strip():
            st.warning("Please enter both company names or tickers.")
        else:
            progress = st.progress(0, text="Resolving company identities...")
            entity_a, fallback_a = _resolve(query)
            entity_b, fallback_b = _resolve(query_b)
            for entity, fallback in ((entity_a, fallback_a), (entity_b, fallback_b)):
                if fallback:
                    st.warning(
                        f"**{entity.legal_name}** doesn't appear to be a publicly registered US company — "
                        "SEC filing data will be unavailable for this company."
                    )

            progress.progress(15, text=f"Fetching and analyzing {entity_a.legal_name} and {entity_b.legal_name} in parallel...")
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_a = pool.submit(_run_pipeline, entity_a)
                f_b = pool.submit(_run_pipeline, entity_b)
                r_a = f_a.result()
                r_b = f_b.result()

            progress.progress(75, text="Running head-to-head comparison synthesis...")
            comparison = compare_synthesize(
                name_a=entity_a.legal_name,
                ticker_a=entity_a.ticker,
                analyses_a=r_a["analyses"],
                name_b=entity_b.legal_name,
                ticker_b=entity_b.ticker,
                analyses_b=r_b["analyses"],
            )
            progress.progress(100, text="Complete.")
            progress.empty()
            st.session_state.mode = "compare"
            st.session_state.result = {
                "entity_a": entity_a,
                "analyses_a": r_a["analyses"],
                "entity_b": entity_b,
                "analyses_b": r_b["analyses"],
                "comparison": comparison,
            }

# ── Render stored result ───────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    if st.session_state.mode == "single":
        _render_brief(r["entity"], r["analyses"], r["synthesis"], r.get("drift"))
    else:
        render_comparison_view(
            entity_a=r["entity_a"],
            analyses_a=r["analyses_a"],
            entity_b=r["entity_b"],
            analyses_b=r["analyses_b"],
            comparison=r["comparison"],
        )
else:
    st.markdown(
        """
        <div style="text-align:center; padding: 4rem 0; color: #6B7580;">
            <div style="font-size: 0.95rem; font-weight: 500; color: #6B7580;">
                Enter a company name or ticker above to generate your brief.
            </div>
            <div style="font-size: 0.82rem; margin-top: 0.5rem; color: #9EA6B0;">
                Works with any public US company — try AAPL, Palantir, or Nvidia.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_footer()
