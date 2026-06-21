"""Generate a downloadable PDF brief from Cadillaq analysis results."""

import datetime

from fpdf import FPDF

from src.analysis.per_source import SourceAnalysis
from src.analysis.synthesis import SynthesisResult
from src.entity_resolver import ResolvedEntity

# Brand palette (RGB)
_NAVY  = (0, 23, 49)
_TEAL  = (26, 92, 106)
_CORAL = (232, 100, 59)
_GRAY  = (107, 117, 128)
_LIGHT = (242, 245, 248)

_CONF_COLORS = {
    "High":             (46, 125, 50),
    "Medium":           (245, 124, 0),
    "Low":              (198, 40, 40),
    "Insufficient Data": _GRAY,
}
_CONF_LABELS = {
    "High": "HIGH", "Medium": "MED", "Low": "LOW", "Insufficient Data": "N/A",
}


def _clean(text: str) -> str:
    """Replace Unicode chars that core PDF fonts can't handle."""
    return (
        text
        .replace("–", "-").replace("—", "--")
        .replace("‘", "'").replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("•", "*").replace("…", "...").replace("·", ".")
        .replace(" ", " ")
    )


class _PDF(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*_TEAL)
        self.cell(
            0, 6,
            "PEMETIQ  ·  CADILLAQ  —  COMPETITIVE INTELLIGENCE BRIEF",
            ln=True, align="R",
        )
        self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_GRAY)
        today = datetime.date.today().strftime("%B %d, %Y")
        self.cell(
            0, 6,
            f"Page {self.page_no()}  ·  Generated {today}  ·  cadillaq.pemetiq.com",
            align="C",
        )

    # ── Layout helpers ─────────────────────────────────────────────────────

    def section(self, title: str) -> None:
        self.ln(4)
        self.set_fill_color(*_LIGHT)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*_TEAL)
        self.cell(0, 7, f"  {title.upper()}", fill=True, ln=True)
        self.ln(2)

    def body(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_NAVY)
        self.multi_cell(0, 5, _clean(text))

    def bullet(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_NAVY)
        self.set_x(self.l_margin + 4)
        self.cell(5, 5, "-")
        self.multi_cell(0, 5, _clean(text))

    def numbered(self, n: int, text: str) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_TEAL)
        self.set_x(self.l_margin + 4)
        self.cell(7, 5, f"{n}.")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_NAVY)
        self.multi_cell(0, 5, _clean(text))
        self.ln(0.5)

    def finding(self, confidence: str, category: str, text: str) -> None:
        conf_label = _CONF_LABELS.get(confidence, confidence)
        conf_color = _CONF_COLORS.get(confidence, _GRAY)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*conf_color)
        self.set_x(self.l_margin + 2)
        self.cell(12, 5, f"[{conf_label}]")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_TEAL)
        self.cell(0, 5, _clean(category) + ":", ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_NAVY)
        prev_margin = self.l_margin
        self.set_left_margin(prev_margin + 14)
        self.multi_cell(0, 5, _clean(text))
        self.set_left_margin(prev_margin)
        self.ln(1)


# ── Public API ─────────────────────────────────────────────────────────────

def generate_brief_pdf(
    entity: ResolvedEntity,
    synthesis: SynthesisResult,
    analyses: list[SourceAnalysis],
) -> bytes:
    """Build a PDF brief and return it as bytes for st.download_button."""
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=14, top=12, right=14)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Title block ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_NAVY)
    pdf.cell(0, 10, _clean(entity.legal_name), ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_GRAY)
    today = datetime.date.today().strftime("%B %d, %Y")
    pdf.cell(0, 5, f"{entity.ticker}  ·  CIK {entity.cik}  ·  {today}", ln=True)
    pdf.ln(2)
    pdf.set_draw_color(*_TEAL)
    pdf.set_line_width(0.4)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())

    # ── Executive Summary ────────────────────────────────────────────────
    if synthesis.executive_summary:
        pdf.section("Executive Summary")
        pdf.body(synthesis.executive_summary)

    # ── Key Takeaways ────────────────────────────────────────────────────
    if synthesis.key_takeaways:
        pdf.section("Key Takeaways")
        for i, t in enumerate(synthesis.key_takeaways, 1):
            pdf.numbered(i, t)

    # ── Reinforcing Signals ──────────────────────────────────────────────
    if synthesis.reinforcing_signals:
        pdf.section("Reinforcing Signals")
        for s in synthesis.reinforcing_signals:
            pdf.bullet(s)
            pdf.ln(1)

    # ── Contradictions ───────────────────────────────────────────────────
    pdf.section("Cross-Source Contradictions")
    if synthesis.contradictions:
        for i, c in enumerate(synthesis.contradictions, 1):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*_CORAL)
            pdf.multi_cell(0, 5, f"Contradiction {i}: {_clean(c.claim)}")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*_NAVY)
            pdf.multi_cell(0, 4, _clean(c.source_a))
            pdf.multi_cell(0, 4, _clean(c.source_b))
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*_GRAY)
            pdf.multi_cell(0, 4, f"Why it matters: {_clean(c.significance)}")
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*_GRAY)
        pdf.cell(0, 5, "No contradictions detected across sources.", ln=True)

    # ── Notable Absences ─────────────────────────────────────────────────
    if synthesis.notable_absences:
        pdf.section("Notable Absences")
        for a in synthesis.notable_absences:
            pdf.bullet(a)
            pdf.ln(1)

    # ── Watch Signals ────────────────────────────────────────────────────
    if synthesis.watch_signals:
        pdf.section("Watch Signals")
        for w in synthesis.watch_signals:
            pdf.bullet(w)
            pdf.ln(1)

    # ── Per-Source Findings ──────────────────────────────────────────────
    pdf.section("Per-Source Findings")
    from src.analysis.confidence import CONFIDENCE_ORDER
    for analysis in analyses:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 6, _clean(analysis.source_name).upper(), ln=True)
        if not analysis.is_available:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*_GRAY)
            pdf.cell(0, 5, f"Data unavailable: {_clean(str(analysis.error))}", ln=True)
        else:
            sorted_findings = sorted(
                analysis.findings,
                key=lambda f: CONFIDENCE_ORDER.get(f.confidence, 0),
                reverse=True,
            )
            for f in sorted_findings:
                pdf.finding(f.confidence, f.category, f.text)
        pdf.ln(2)

    return bytes(pdf.output())
