"""Reusable Streamlit UI components for the Cadillaq brief."""

import base64
import datetime
import html
from pathlib import Path

import streamlit as st

_ASSETS = Path(__file__).parent.parent.parent / "assets"

def _b64_img(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"

from src.analysis.confidence import CONFIDENCE_ORDER
from src.analysis.per_source import SourceAnalysis
from src.analysis.synthesis import ComparisonResult, SynthesisResult
from src.entity_resolver import ResolvedEntity
from src.ui.styling import badge_html, priority_badge_html

_SECTION_DESCRIPTIONS = {
    "reinforcing": "Where SEC filings, news, and search trends all point in the same direction — high-conviction signals.",
    "contradictions": "These gaps between official narrative and external signals are the core intelligence value of this brief.",
    "absences": "What you'd expect to find given the company's profile, but can't — silence is sometimes the most telling signal.",
    "watch": "Early indicators and emerging patterns that don't yet rise to a conclusion — but warrant active monitoring.",
}


def _get_initials(name: str) -> str:
    """Extract up to two initials from a company name."""
    words = [w for w in name.split() if w and w[0].isalpha()]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return name[:2].upper()


def _detect_source_tags(text: str) -> list[tuple[str, str]]:
    """Infer which data sources are referenced in a text snippet.

    Returns:
        List of (label, css_class) tuples.
    """
    tags: list[tuple[str, str]] = []
    t = text.lower()
    if any(kw in t for kw in ["sec", "10-k", "10-q", "filing", "edgar", "annual report", "quarterly report"]):
        tags.append(("SEC Filing", "sec"))
    if any(kw in t for kw in ["news", "article", "media", "analyst", "seeking alpha", "reuters", "bloomberg", "reported", "report"]):
        tags.append(("Recent News", "news"))
    if any(kw in t for kw in ["trend", "search interest", "google trends", "search volume", "query"]):
        tags.append(("Google Trends", "trends"))
    return tags


def _source_tags_html(text: str) -> str:
    """Return HTML for source tag pills detected from text."""
    tags = _detect_source_tags(text)
    if not tags:
        return ""
    return "".join(
        f'<span class="source-tag source-tag-{cls}">{label}</span>'
        for label, cls in tags
    )


def _split_titled(text: str) -> tuple[str, str]:
    """Split a 'Title: body' string into (title, body). Returns ('', text) if no colon."""
    parts = text.split(":", 1)
    if len(parts) == 2 and len(parts[0]) < 80:
        return parts[0].strip(), parts[1].strip()
    return "", text


def render_company_brief(entity: ResolvedEntity, synthesis: SynthesisResult) -> None:
    """Render the company identity card with executive summary text inline.

    Args:
        entity: Resolved company entity.
        synthesis: Completed synthesis result containing the executive summary.
    """
    today = datetime.date.today().strftime("%b %d, %Y")
    initials = _get_initials(entity.legal_name)

    summary = synthesis.executive_summary or ""
    paragraphs = [p.strip() for p in summary.split("\n\n") if p.strip()]
    if not paragraphs and summary:
        paragraphs = [summary]

    para_html = ""
    for i, p in enumerate(paragraphs):
        cls = "exec-summary-p lead" if i == 0 else "exec-summary-p"
        para_html += f'<p class="{cls}">{p}</p>'

    st.markdown(
        f'<div class="company-brief-card">'
        f'<div class="company-brief-header">'
        f'<div class="company-avatar">{initials}</div>'
        f'<div><div class="company-name">{entity.legal_name}</div>'
        f'<div class="company-meta">{entity.ticker} &nbsp;·&nbsp; CIK: {entity.cik} &nbsp;·&nbsp; Report generated {today}</div>'
        f'</div></div>'
        f'{para_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_company_card(entity: ResolvedEntity) -> None:
    """Render a standalone company identity card without summary text.

    Args:
        entity: Resolved company entity with name, ticker, and CIK.
    """
    initials = _get_initials(entity.legal_name)
    st.markdown(
        f'<div class="company-brief-card">'
        f'<div class="company-brief-header" style="margin-bottom:0;padding-bottom:0;border-bottom:none;">'
        f'<div class="company-avatar">{initials}</div>'
        f'<div><div class="company-name">{entity.legal_name}</div>'
        f'<div class="company-meta">{entity.ticker} &nbsp;·&nbsp; CIK: {entity.cik}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )


def render_executive_summary(synthesis: SynthesisResult) -> None:
    """Render the executive summary text block (standalone).

    Args:
        synthesis: Completed synthesis result.
    """
    if synthesis.error and not synthesis.executive_summary:
        st.error(f"Synthesis error: {synthesis.error}")
        return

    summary = synthesis.executive_summary or ""
    paragraphs = [p.strip() for p in summary.split("\n\n") if p.strip()]
    if not paragraphs and summary:
        paragraphs = [summary]

    para_html = ""
    for i, p in enumerate(paragraphs):
        cls = "exec-summary-p lead" if i == 0 else "exec-summary-p"
        para_html += f'<p class="{cls}">{p}</p>'

    st.markdown(
        f'<div class="company-brief-card">{para_html}</div>',
        unsafe_allow_html=True,
    )


def render_synthesis_sections(synthesis: SynthesisResult) -> None:
    """Render all four synthesis sections in the redesigned layout.

    Args:
        synthesis: Completed synthesis result.
    """
    _render_reinforcing(synthesis)
    _render_contradictions(synthesis)
    _render_absences_and_watch(synthesis)


def _render_reinforcing(synthesis: SynthesisResult) -> None:
    st.markdown(
        f'<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
        f'<div class="signal-section-header"><div class="signal-dot"></div>'
        f'<div class="signal-section-title">Reinforcing Signals</div></div>'
        f'<div class="signal-section-subtitle">{_SECTION_DESCRIPTIONS["reinforcing"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    signals = synthesis.reinforcing_signals
    if not signals:
        st.caption("No reinforcing signals identified across sources.")
        return

    cards_html = ""
    for signal in signals:
        title, body = _split_titled(signal)
        display_title = title if title else signal[:80]
        display_body = body if title else ""
        tags_html = _source_tags_html(signal)
        cards_html += (
            f'<div class="signal-card">'
            f'<div class="signal-card-title">{display_title}</div>'
            f'<div class="signal-card-body">{display_body}</div>'
            f'<div class="source-tags">{tags_html}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:0.5rem;">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def _render_contradictions(synthesis: SynthesisResult) -> None:
    contradictions = synthesis.contradictions

    st.markdown(
        f'<div class="contradictions-banner">'
        f'<div class="contrad-eyebrow">Cross-Source Contradictions</div>'
        f'<div class="contrad-title">Where sources actively disagree</div>'
        f'<div class="contrad-desc">{_SECTION_DESCRIPTIONS["contradictions"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not contradictions:
        st.markdown(
            '<div class="contradictions-body">'
            '<p style="color:#6B7580;font-size:0.9rem;margin:0;">No contradictions detected across sources.</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        return

    cards_html = ""
    for i, c in enumerate(contradictions, 1):
        tags_a_html = _source_tags_html(c.source_a)
        tags_b_html = _source_tags_html(c.source_b)
        all_tags = tags_a_html + tags_b_html
        cards_html += (
            f'<div class="contradiction-v2">'
            f'<div class="contradiction-number">Contradiction {i}</div>'
            f'<div class="contradiction-title">{c.claim}</div>'
            f'<div class="source-tags" style="margin-bottom:0.75rem;">{all_tags}</div>'
            f'<div class="contradiction-desc">{c.source_a}</div>'
            f'<div class="contradiction-desc" style="margin-top:-0.3rem;">{c.source_b}</div>'
            f'<div class="why-matters-label">Why it matters</div>'
            f'<div class="why-matters-text">{c.significance}</div>'
            f'</div>'
        )

    grid_cols = "1fr 1fr" if len(contradictions) > 1 else "1fr"
    st.markdown(
        f'<div class="contradictions-body"><div style="display:grid;grid-template-columns:{grid_cols};gap:1rem;">{cards_html}</div></div>',
        unsafe_allow_html=True,
    )


def _render_absences_and_watch(synthesis: SynthesisResult) -> None:
    """Render Notable Absences and Watch Signals in a two-column layout."""
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        _render_absences(synthesis)
    with col2:
        _render_watch(synthesis)


def _render_absences(synthesis: SynthesisResult) -> None:
    absences = synthesis.notable_absences
    st.markdown(
        f'<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
        f'<div class="absence-section-title">Notable Absences</div>'
        f'<div class="absence-section-subtitle">{_SECTION_DESCRIPTIONS["absences"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if not absences:
        st.caption("No notable absences identified.")
        return

    items_html = "".join(
        f'<div class="absence-item"><span class="absence-dash">—</span><span>{a}</span></div>'
        for a in absences
    )
    st.markdown(f"<div>{items_html}</div>", unsafe_allow_html=True)


def _render_watch(synthesis: SynthesisResult) -> None:
    watch = synthesis.watch_signals
    st.markdown(
        f'<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
        f'<div class="watch-section-title">Watch Signals</div>'
        f'<div class="watch-section-subtitle">{_SECTION_DESCRIPTIONS["watch"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if not watch:
        st.caption("No watch signals identified.")
        return

    for signal in watch:
        title, body = _split_titled(signal)
        display_title = title if title else signal[:80]
        display_body = body if title else ""
        st.markdown(
            f'<div class="watch-card">'
            f'<div class="watch-card-title">{display_title}</div>'
            f'<div class="watch-card-body">{display_body}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_source_findings(analyses: list[SourceAnalysis]) -> None:
    """Render per-source findings in a tabbed layout with finding counts.

    Args:
        analyses: List of SourceAnalysis objects (one per data source).
    """
    st.markdown(
        '<div style="margin-top:2.2rem;margin-bottom:0.25rem;">'
        '<div class="findings-section-label">Per-Source Findings</div>'
        '<div class="findings-section-subtitle">Raw findings from each source, analyzed independently. '
        'Sorted by confidence — High findings are explicitly supported by the source material.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_labels = [
        f"{a.source_name}  {len(a.findings) if a.is_available else 0}"
        for a in analyses
    ]
    tabs = st.tabs(tab_labels)

    for tab, analysis in zip(tabs, analyses):
        with tab:
            if not analysis.is_available:
                st.markdown(
                    f'<div class="source-error">Data unavailable: {analysis.error}</div>',
                    unsafe_allow_html=True,
                )
                continue

            if not analysis.findings:
                st.caption("No findings returned for this source.")
                continue

            sorted_findings = sorted(
                analysis.findings,
                key=lambda f: CONFIDENCE_ORDER.get(f.confidence, 0),
                reverse=True,
            )

            cards_html = ""
            for finding in sorted_findings:
                bdg = badge_html(finding.confidence)
                cards_html += (
                    f'<div class="finding-card-v2">'
                    f'<div class="finding-badge-col">{bdg}</div>'
                    f'<div class="finding-content-col">'
                    f'<div class="finding-category-v2">{finding.category}</div>'
                    f'<div class="finding-text-v2">{finding.text}</div>'
                    f'<span class="finding-source-link">View {analysis.source_name} \u2192</span>'
                    f'</div>'
                    f'</div>'
                )

            st.markdown(
                f'<div style="padding-top:0.5rem;">{cards_html}</div>',
                unsafe_allow_html=True,
            )


def render_takeaways_anchor(takeaways: list[str], compare: bool = False) -> None:
    """Render the compact top anchor card linking down to the full takeaways section.

    Args:
        takeaways: List of takeaway strings from the synthesis.
        compare: True when rendering in comparison mode (adjusts label).
    """
    if not takeaways:
        return
    label = "Head-to-Head Verdict" if compare else "Key Takeaways"
    items_html = "".join(
        f'<div style="display:flex;gap:0.6rem;margin-bottom:0.45rem;align-items:flex-start;">'
        f'<span style="font-size:0.72rem;font-weight:700;color:var(--teal);min-width:1.1rem;padding-top:0.05rem;">{i}.</span>'
        f'<span style="font-size:0.82rem;color:var(--navy);line-height:1.55;">{t}</span>'
        f'</div>'
        for i, t in enumerate(takeaways, 1)
    )
    st.markdown(
        f'<div style="background:rgba(26,92,106,0.06);border:1px solid rgba(26,92,106,0.18);'
        f'border-radius:8px;padding:1.1rem 1.25rem 0.9rem;margin-bottom:1.5rem;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.7rem;">'
        f'<span style="font-size:0.65rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;'
        f'color:var(--teal);">{label}</span>'
        f'<a href="#takeaways" style="font-size:0.72rem;color:var(--teal);text-decoration:none;'
        f'opacity:0.7;">full analysis ↓</a>'
        f'</div>'
        f'{items_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_takeaways_section(takeaways: list[str], compare: bool = False) -> None:
    """Render the full takeaways section at the bottom of the brief.

    Args:
        takeaways: List of takeaway strings from the synthesis.
        compare: True when rendering in comparison mode (adjusts label).
    """
    if not takeaways:
        return
    label = "Head-to-Head Verdict" if compare else "Key Takeaways"
    subtitle = (
        "Directional verdicts based on the evidence above — where each company stands relative to the other."
        if compare else
        "What an investor or operator should do, watch, or weigh based on the full evidence set."
    )
    items_html = "".join(
        f'<div style="display:flex;gap:0.75rem;padding:0.85rem 0;'
        f'border-bottom:1px solid rgba(14,59,84,0.07);align-items:flex-start;">'
        f'<span style="font-size:1rem;font-weight:700;color:var(--teal);min-width:1.5rem;'
        f'line-height:1.4;padding-top:0.05rem;">{i}.</span>'
        f'<span style="font-size:0.88rem;color:var(--navy);line-height:1.6;">{t}</span>'
        f'</div>'
        for i, t in enumerate(takeaways, 1)
    )
    st.markdown(
        f'<div id="takeaways" style="margin-top:2.5rem;">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.2rem;">'
        f'<div style="width:3px;height:1.1rem;background:var(--teal);border-radius:2px;"></div>'
        f'<span style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:var(--teal);">{label}</span>'
        f'</div>'
        f'<div style="font-size:0.78rem;color:#6B7580;margin-bottom:0.75rem;">{subtitle}</div>'
        f'<div style="border-top:1px solid rgba(14,59,84,0.1);">{items_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_comparison_view(
    entity_a: ResolvedEntity,
    analyses_a: list[SourceAnalysis],
    entity_b: ResolvedEntity,
    analyses_b: list[SourceAnalysis],
    comparison: ComparisonResult,
    drift_a=None,
    drift_b=None,
) -> None:
    """Render the full head-to-head comparison view.

    Args:
        entity_a: Resolved entity for company A.
        analyses_a: Per-source analyses for company A.
        entity_b: Resolved entity for company B.
        analyses_b: Per-source analyses for company B.
        comparison: Completed comparison synthesis result.
        drift_a: Narrative-drift result for company A (optional).
        drift_b: Narrative-drift result for company B (optional).
    """
    # ── Company cards ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-label">Head-to-Head Comparison</div>'
        '<div class="section-subtitle">Independent analysis of each company, synthesized into a structured competitive brief.</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        render_company_card(entity_a)
    with col_b:
        render_company_card(entity_b)

    # ── Comparison summary ─────────────────────────────────────────────────
    if comparison.error and not comparison.comparison_summary:
        st.error(f"Comparison synthesis error: {comparison.error}")
    elif comparison.comparison_summary:
        st.markdown(
            f'<div class="company-brief-card" style="margin-top:1rem;">'
            f'<p class="exec-summary-p lead">{comparison.comparison_summary}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    render_takeaways_anchor(comparison.key_takeaways, compare=True)

    # ── Competitive edges ──────────────────────────────────────────────────
    if comparison.competitive_edges:
        st.markdown(
            '<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
            '<div class="signal-section-header"><div class="signal-dot"></div>'
            '<div class="signal-section-title">Competitive Edges</div></div>'
            '<div class="signal-section-subtitle">Where each company has a clear, evidence-backed advantage.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        cards_html = ""
        for edge in comparison.competitive_edges:
            company_label = (
                f'<span style="font-size:0.65rem;font-weight:600;letter-spacing:0.06em;'
                f'color:var(--teal);text-transform:uppercase;">{edge.company}</span>'
            )
            cards_html += (
                f'<div class="signal-card">'
                f'{company_label}'
                f'<div class="signal-card-title" style="margin-top:0.3rem;">{edge.dimension}</div>'
                f'<div class="signal-card-body">{edge.advantage}</div>'
                f'<div style="font-size:0.75rem;color:#6B7580;margin-top:0.5rem;">{edge.evidence}</div>'
                f'</div>'
            )
        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:0.5rem;">{cards_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Diverging signals ──────────────────────────────────────────────────
    if comparison.diverging_signals:
        st.markdown(
            '<div class="contradictions-banner">'
            '<div class="contrad-eyebrow">Diverging Signals</div>'
            '<div class="contrad-title">Where the companies are moving in opposite directions</div>'
            '<div class="contrad-desc">Topics where evidence for one company points clearly away from the other — the most actionable intelligence in a head-to-head.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        cards_html = ""
        for i, d in enumerate(comparison.diverging_signals, 1):
            cards_html += (
                f'<div class="contradiction-v2">'
                f'<div class="contradiction-number">Signal {i}</div>'
                f'<div class="contradiction-title">{d.topic}</div>'
                f'<div class="contradiction-desc"><strong>{comparison.name_a}:</strong> {d.company_a}</div>'
                f'<div class="contradiction-desc" style="margin-top:-0.3rem;"><strong>{comparison.name_b}:</strong> {d.company_b}</div>'
                f'</div>'
            )
        grid_cols = "1fr 1fr" if len(comparison.diverging_signals) > 1 else "1fr"
        st.markdown(
            f'<div class="contradictions-body"><div style="display:grid;grid-template-columns:{grid_cols};gap:1rem;">{cards_html}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Shared vulnerabilities + Watch signals ─────────────────────────────
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(
            '<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
            '<div class="absence-section-title">Shared Vulnerabilities</div>'
            '<div class="absence-section-subtitle">Risks and weaknesses both companies face — neutralise these before leaning on any edge.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if comparison.shared_vulnerabilities:
            items_html = "".join(
                f'<div class="absence-item"><span class="absence-dash">—</span><span>{v}</span></div>'
                for v in comparison.shared_vulnerabilities
            )
            st.markdown(f"<div>{items_html}</div>", unsafe_allow_html=True)
        else:
            st.caption("No shared vulnerabilities identified.")

    with col2:
        st.markdown(
            '<div style="margin-top:1.8rem;margin-bottom:0.25rem;">'
            '<div class="watch-section-title">Watch Signals</div>'
            '<div class="watch-section-subtitle">Asymmetric risks or early indicators that could shift this comparison.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if comparison.watch_signals:
            for signal in comparison.watch_signals:
                title, body = _split_titled(signal)
                display_title = title if title else signal[:80]
                display_body = body if title else ""
                st.markdown(
                    f'<div class="watch-card">'
                    f'<div class="watch-card-title">{display_title}</div>'
                    f'<div class="watch-card-body">{display_body}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No watch signals identified.")

    # ── Per-company Narrative Drift ────────────────────────────────────────
    if (drift_a is not None and getattr(drift_a, "available", False)) or \
       (drift_b is not None and getattr(drift_b, "available", False)):
        st.markdown(
            '<div style="margin-top:2rem;margin-bottom:0.5rem;">'
            '<div class="signal-section-header"><div class="signal-dot"></div>'
            '<div class="signal-section-title">Narrative Drift</div></div>'
            '<div class="signal-section-subtitle">How each company\'s own filing narrative has shifted since the comparable prior period.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_drift_section(drift_a, heading=f"Narrative Drift — {entity_a.legal_name}")
        render_drift_section(drift_b, heading=f"Narrative Drift — {entity_b.legal_name}")

    render_takeaways_section(comparison.key_takeaways, compare=True)

    # ── Per-source findings — side by side tabs ────────────────────────────
    st.markdown(
        '<div style="margin-top:2.2rem;margin-bottom:0.25rem;">'
        '<div class="findings-section-label">Per-Source Findings</div>'
        '<div class="findings-section-subtitle">Independent source analysis for each company. Expand to compare raw findings.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_a2, col_b2 = st.columns(2, gap="medium")
    for col, entity, analyses in (
        (col_a2, entity_a, analyses_a),
        (col_b2, entity_b, analyses_b),
    ):
        with col:
            st.markdown(
                f'<div style="font-size:0.8rem;font-weight:600;color:var(--navy);margin-bottom:0.5rem;">'
                f'{entity.legal_name}</div>',
                unsafe_allow_html=True,
            )
            tab_labels = [
                f"{a.source_name}  {len(a.findings) if a.is_available else 0}"
                for a in analyses
            ]
            tabs = st.tabs(tab_labels)
            for tab, analysis in zip(tabs, analyses):
                with tab:
                    if not analysis.is_available:
                        st.markdown(
                            f'<div class="source-error">Data unavailable: {analysis.error}</div>',
                            unsafe_allow_html=True,
                        )
                        continue
                    if not analysis.findings:
                        st.caption("No findings returned for this source.")
                        continue
                    sorted_findings = sorted(
                        analysis.findings,
                        key=lambda f: CONFIDENCE_ORDER.get(f.confidence, 0),
                        reverse=True,
                    )
                    cards_html = ""
                    for finding in sorted_findings:
                        bdg = badge_html(finding.confidence)
                        cards_html += (
                            f'<div class="finding-card-v2">'
                            f'<div class="finding-badge-col">{bdg}</div>'
                            f'<div class="finding-content-col">'
                            f'<div class="finding-category-v2">{finding.category}</div>'
                            f'<div class="finding-text-v2">{finding.text}</div>'
                            f'</div>'
                            f'</div>'
                        )
                    st.markdown(
                        f'<div style="padding-top:0.5rem;">{cards_html}</div>',
                        unsafe_allow_html=True,
                    )


_DRIFT_BADGES = {
    "added": "New risk",
    "intensified": "Intensified",
    "dropped": "Dropped",
    "tone": "Tone",
}
_DRIFT_TILES = [
    ("added", "New risks", "+{n}"),
    ("intensified", "Intensified", "▲ {n}"),
    ("dropped", "Metrics dropped", "−{n}"),
    ("tone", "Tone shifts", "~ {n}"),
]


def _period_end_label(report_date: str, filed_date: str = "") -> str:
    """Unambiguous period-end label from an ISO date, e.g. 'Mar 2026'.

    Uses the actual period-end month/year rather than a calendar-quarter number,
    which would be misleading for companies with non-December fiscal years.
    """
    src = report_date or filed_date
    try:
        return datetime.date.fromisoformat(src).strftime("%b %Y")
    except (ValueError, TypeError):
        return src[:7] if src else "prior period"


def render_drift_section(drift, heading: str = "Narrative Drift") -> None:
    """Render the Narrative Drift section — what changed vs the prior filing."""
    if drift is None or not getattr(drift, "available", False):
        return

    esc = html.escape
    cur = _period_end_label(drift.current_report_date)
    prior = _period_end_label(drift.prior_report_date)
    qualifier = "quarter" if drift.current_form == "10-Q" else "year"
    basis = f"{drift.current_form} · {qualifier} ending {cur} vs {prior}"
    if drift.comparison_basis:
        basis += f" · {drift.comparison_basis}"

    header = (
        f'<div class="drift-header">'
        f'<span class="drift-title">{esc(heading)}</span>'
        f'<span class="drift-basis">{esc(basis)}</span>'
        f'</div>'
    )
    headline = (
        f'<div class="drift-headline">{esc(drift.headline)}</div>'
        if drift.headline else ""
    )

    if not drift.items:
        st.markdown(
            header + headline
            + '<div style="color:#6B7580;font-size:0.88rem;">'
            f'No material narrative changes since the {esc(prior)} filing.</div>',
            unsafe_allow_html=True,
        )
        return

    counts = drift.counts
    tiles = ""
    for kind, label, fmt in _DRIFT_TILES:
        tiles += (
            f'<div class="drift-tile">'
            f'<div class="drift-tile-label">{label}</div>'
            f'<div class="drift-tile-value drift-value-{kind}">{fmt.format(n=counts[kind])}</div>'
            f'</div>'
        )

    cards = ""
    for item in drift.items:
        kind = item.kind
        badge = _DRIFT_BADGES.get(kind, kind.title())
        quote_html = (
            f'<p class="drift-quote">“{esc(item.quote)}”</p>' if item.quote else ""
        )
        label_html = (
            f'<span class="drift-card-label">{esc(item.label)}</span>'
            if item.label else ""
        )
        cards += (
            f'<div class="drift-card">'
            f'<div class="drift-card-head">'
            f'<span class="drift-badge drift-badge-{kind}">{badge}</span>'
            f'{label_html}</div>'
            f'<p class="drift-card-summary">{esc(item.summary)}</p>'
            f'{quote_html}'
            f'</div>'
        )

    st.markdown(
        header + headline
        + f'<div class="drift-tiles">{tiles}</div>'
        + f'<div class="drift-cards">{cards}</div>',
        unsafe_allow_html=True,
    )


_NEWS_DRIFT_BADGES = {
    "emerged": "Emerged",
    "faded": "Faded",
    "sentiment": "Sentiment",
}


def render_news_drift_section(news_drift) -> None:
    """Render the News Narrative Shift section — how the media story changed."""
    if news_drift is None or not getattr(news_drift, "available", False):
        return
    if not news_drift.items:
        return

    esc = html.escape
    basis = "Media coverage"
    if news_drift.prior_period:
        basis += f" · since {esc(news_drift.prior_period)}"

    header = (
        f'<div class="drift-header">'
        f'<span class="drift-title">News Narrative Shift</span>'
        f'<span class="drift-basis">{basis}</span>'
        f'</div>'
    )
    headline = (
        f'<div class="drift-headline">{esc(news_drift.headline)}</div>'
        if news_drift.headline else ""
    )

    cards = ""
    for item in news_drift.items:
        badge = _NEWS_DRIFT_BADGES.get(item.kind, item.kind.title())
        label_html = (
            f'<span class="drift-card-label">{esc(item.label)}</span>'
            if item.label else ""
        )
        cards += (
            f'<div class="drift-card">'
            f'<div class="drift-card-head">'
            f'<span class="drift-badge drift-badge-{item.kind}">{badge}</span>'
            f'{label_html}</div>'
            f'<p class="drift-card-summary">{esc(item.summary)}</p>'
            f'</div>'
        )

    st.markdown(
        header + headline + f'<div class="drift-cards">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the Pemetiq footer with Primary-Logo."""
    logo_uri = _b64_img(_ASSETS / "primary-logo.png")
    st.markdown(
        f'<div class="ci-footer">'
        f'<img src="{logo_uri}" style="height:28px;opacity:0.85;margin-bottom:0.5rem"><br>'
        f'<span>© 2026 Pemetiq &nbsp;·&nbsp; All signals sourced from public data</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
