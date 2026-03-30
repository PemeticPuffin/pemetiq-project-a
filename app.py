"""Cadillaq — Competitive intelligence autopilot. Streamlit entry point."""

import base64
import logging
import os
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

from src.analysis.per_source import analyze_all_sources
from src.analysis.synthesis import synthesize
from src.data.news_api import fetch_news
from src.data.sec_edgar import fetch_latest_filing
from src.data.trends import fetch_trends
from src.entity_resolver import resolve_company
from src.ui.components import (
    render_company_brief,
    render_footer,
    render_source_findings,
    render_synthesis_sections,
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

# ── Search input ───────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1], gap="small")

with col_input:
    query = st.text_input(
        label="Company",
        placeholder="Enter a company name or ticker — e.g. Palantir, MSFT, Nvidia",
        label_visibility="collapsed",
    )

with col_btn:
    run_clicked = st.button("Analyze", type="primary", use_container_width=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None


def _render_brief(entity, analyses, synthesis) -> None:
    """Render the full CI brief."""
    st.markdown(
        '<div class="section-label">Executive Summary</div>'
        '<div class="section-subtitle">Synthesized from SEC filings, recent news, and search trend data.</div>',
        unsafe_allow_html=True,
    )
    render_company_brief(entity, synthesis)
    render_synthesis_sections(synthesis)
    render_source_findings(analyses)


# ── Pipeline ───────────────────────────────────────────────────────────────
if run_clicked:
    if not query.strip():
        st.warning("Please enter a company name or ticker.")
    else:
        progress = st.progress(0, text="Resolving company identity...")

        # Step 1: Entity resolution
        try:
            entity = resolve_company(query.strip())
        except ValueError as exc:
            progress.empty()
            st.error(str(exc))
            st.stop()

        progress.progress(20, text=f"Found **{entity.legal_name}** ({entity.ticker}) — fetching data...")

        # Step 2: Parallel data fetch
        filing = fetch_latest_filing(entity.cik, entity.legal_name)
        news_data = fetch_news(entity.legal_name, entity.ticker)
        trends_data = fetch_trends(entity.legal_name, entity.ticker)

        progress.progress(50, text="Analyzing each source with Claude...")

        # Step 3: Per-source analysis
        analyses = analyze_all_sources(
            company_name=entity.legal_name,
            ticker=entity.ticker,
            filing=filing,
            news_data=news_data,
            trends_data=trends_data,
        )

        progress.progress(80, text="Synthesizing cross-source brief...")

        # Step 4: Synthesis
        synthesis = synthesize(
            company_name=entity.legal_name,
            ticker=entity.ticker,
            source_analyses=analyses,
        )

        progress.progress(100, text="Complete.")
        progress.empty()

        st.session_state.result = {
            "entity": entity,
            "analyses": analyses,
            "synthesis": synthesis,
        }

# ── Render stored result ───────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    _render_brief(r["entity"], r["analyses"], r["synthesis"])
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
