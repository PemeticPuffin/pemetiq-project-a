"""CSS and brand styling for the Cadillaq Streamlit app."""

# Pemetiq brand colors
PRIMARY = "#001731"
SECONDARY = "#1A5C6A"
ACCENT = "#E8643B"
BACKGROUND = "#FAFBFC"
TEXT = "#333333"
MUTED = "#6B7580"

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #333333;
    background: #FAFBFC;
}

.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
}

/* ── Hide Streamlit chrome ──────────────────────────────────────── */
header[data-testid="stHeader"], #MainMenu, footer,
.stDeployButton { display: none !important; }

/* ── Header ──────────────────────────────────────────────────────── */
.ci-header {
    background: linear-gradient(135deg, #001731 0%, #0d2c4d 100%);
    padding: 2.5rem 3rem 2.2rem;
    border-radius: 14px;
    margin-bottom: 1.8rem;
    color: white;
}
.ci-header .brand-label {
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #E8643B;
    margin-bottom: 0.7rem;
}
.ci-header h1 {
    font-size: 2.1rem;
    font-weight: 700;
    margin: 0 0 0.6rem 0;
    color: white;
    line-height: 1.2;
}
.ci-header .tagline {
    font-size: 0.92rem;
    margin: 0;
    color: rgba(255,255,255,0.8);
    max-width: 540px;
    line-height: 1.65;
}

/* ── Search input ────────────────────────────────────────────────── */
div[data-testid="stTextInput"] input {
    border-radius: 0.5rem !important;
    border: 2px solid #e2e4e8 !important;
    padding: 0.7rem 1rem !important;
    font-size: 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
    background: white !important;
    transition: border-color 0.15s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #001731 !important;
    box-shadow: 0 0 0 2px rgba(0,23,49,0.08) !important;
    outline: none !important;
}

/* ── Primary button ──────────────────────────────────────────────── */
div[data-testid="stButton"] button[kind="primary"] {
    background: #E8643B !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    height: 44px !important;
    transition: background 0.15s ease !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #d4572f !important;
}

/* ── Sample brief chips ──────────────────────────────────────────── */
[class*="st-key-sample_"] button {
    height: 42px !important;
    min-height: 42px !important;
    border: 1px solid #D3DAE0 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    color: #0E3B54 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0 0.85rem !important;
    transition: border-color 0.15s ease, color 0.15s ease !important;
}
[class*="st-key-sample_"] button:hover {
    border-color: #E8643B !important;
    color: #E8643B !important;
}
/* keep labels on one line; truncate gracefully rather than wrap */
[class*="st-key-sample_"] button p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
}

/* ── Section labels ──────────────────────────────────────────────── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #6B7580;
    margin-bottom: 0.25rem;
}
.section-subtitle {
    font-size: 0.84rem;
    color: #6B7580;
    margin-bottom: 1rem;
}

/* ── Company brief card ──────────────────────────────────────────── */
.company-brief-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 4px rgba(14, 59, 84, 0.05);
}
.company-brief-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.2rem;
    padding-bottom: 1.2rem;
}
.company-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: #001731;
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.92rem;
    font-weight: 700;
    flex-shrink: 0;
    letter-spacing: 0.03em;
}
.company-name {
    font-size: 1.22rem;
    font-weight: 700;
    color: #001731;
    margin: 0 0 0.2rem 0;
}
.company-meta {
    font-size: 0.79rem;
    color: #6B7580;
}
.exec-summary-p {
    font-size: 0.95rem;
    line-height: 1.72;
    color: #333333;
    margin: 0 0 0.9rem 0;
}
.exec-summary-p.lead {
    font-weight: 500;
}
.exec-summary-p:last-child {
    margin-bottom: 0;
}

/* ── Reinforcing signal section ──────────────────────────────────── */
.signal-section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
}
.signal-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #2E7D32;
    flex-shrink: 0;
    display: inline-block;
}
.signal-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #1A1A1A;
}
.signal-section-subtitle {
    font-size: 0.84rem;
    color: #6B7580;
    margin-bottom: 1.2rem;
    padding-left: 1.1rem;
}

/* ── Signal cards ────────────────────────────────────────────────── */
.signal-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 3px rgba(14, 59, 84, 0.04);
    display: flex;
    flex-direction: column;
}
.signal-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #001731;
    margin-bottom: 0.45rem;
    line-height: 1.35;
}
.signal-card-body {
    font-size: 0.86rem;
    line-height: 1.6;
    color: #444444;
    flex: 1;
    margin-bottom: 0.75rem;
}

/* ── Source tags / pills ─────────────────────────────────────────── */
.source-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: auto;
}
.source-tag {
    display: inline-block;
    padding: 0.17rem 0.65rem;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.source-tag-sec    { background: #FDE8DF; color: #B8421F; }
.source-tag-news   { background: #FDE8DF; color: #B8421F; }
.source-tag-trends { background: #DFF0EC; color: #16534A; }
.source-tag-default { background: #EEF0F3; color: #555555; }

/* ── Contradictions banner ───────────────────────────────────────── */
.contradictions-banner {
    background: linear-gradient(135deg, #001731 0%, #0d2c4d 100%);
    border-radius: 12px 12px 0 0;
    padding: 1.5rem 1.8rem 1.4rem;
    margin-top: 1.8rem;
}
.contradictions-banner .contrad-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #E8643B;
    margin-bottom: 0.4rem;
}
.contradictions-banner .contrad-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.3rem;
}
.contradictions-banner .contrad-desc {
    font-size: 0.83rem;
    color: rgba(255,255,255,0.58);
}
.contradictions-body {
    background: white;
    border: 1px solid #E2E8F0;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
}

/* ── Contradiction cards ─────────────────────────────────────────── */
.contradiction-v2 {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    background: white;
}
.contradiction-number {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #E8643B;
    margin-bottom: 0.5rem;
}
.contradiction-title {
    font-size: 0.97rem;
    font-weight: 700;
    color: #001731;
    margin-bottom: 0.6rem;
    line-height: 1.35;
}
.contradiction-desc {
    font-size: 0.85rem;
    line-height: 1.6;
    color: #444444;
    margin-bottom: 0.55rem;
}
.why-matters-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #C62828;
    margin-bottom: 0.3rem;
    margin-top: 0.75rem;
}
.why-matters-text {
    font-size: 0.84rem;
    line-height: 1.55;
    color: #555555;
    font-style: italic;
}

/* ── Notable absences ────────────────────────────────────────────── */
.absence-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #1A1A1A;
    margin-bottom: 0.25rem;
}
.absence-section-subtitle {
    font-size: 0.84rem;
    color: #6B7580;
    margin-bottom: 1.1rem;
}
.absence-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.72rem 0;
    font-size: 0.87rem;
    color: #333333;
    line-height: 1.45;
}
.absence-dash {
    color: #CBD2D9;
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 0.05rem;
}

/* ── Watch signals ───────────────────────────────────────────────── */
.watch-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #1A1A1A;
    margin-bottom: 0.25rem;
}
.watch-section-subtitle {
    font-size: 0.84rem;
    color: #6B7580;
    margin-bottom: 1.1rem;
}
.watch-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 1px 3px rgba(14, 59, 84, 0.04);
}
.watch-card-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: #001731;
    margin-bottom: 0.4rem;
    line-height: 1.35;
}
.watch-card-body {
    font-size: 0.84rem;
    line-height: 1.55;
    color: #555555;
}

/* ── Per-source findings ─────────────────────────────────────────── */
.findings-section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #6B7580;
    margin-bottom: 0.25rem;
}
.findings-section-subtitle {
    font-size: 0.83rem;
    color: #6B7580;
    margin-bottom: 0.8rem;
}
.finding-card-v2 {
    display: flex;
    gap: 1rem;
    padding: 1rem 0;
}
.finding-card-v2 + .finding-card-v2 {
    margin-top: 0.25rem;
}
.finding-badge-col {
    flex-shrink: 0;
    padding-top: 0.1rem;
    width: 52px;
}
.finding-content-col { flex: 1; }
.finding-category-v2 {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6B7580;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}
.finding-text-v2 {
    font-size: 0.9rem;
    line-height: 1.58;
    color: #333333;
    margin-bottom: 0.4rem;
}
.finding-source-link {
    font-size: 0.78rem;
    color: #1A5C6A;
    font-weight: 500;
}

/* ── Confidence badges ───────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 0.18rem 0.5rem;
    border-radius: 4px;
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: white;
}
.badge-high        { background: #2E7D32; }
.badge-medium      { background: #F57C00; }
.badge-low         { background: #C62828; }
.badge-insufficient { background: #9E9E9E; }

/* ── Source error ────────────────────────────────────────────────── */
.source-error {
    background: #FFF3F3;
    border: 1px solid #FCCBCB;
    border-radius: 6px;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    color: #C62828;
}

/* ── Footer ──────────────────────────────────────────────────────── */
.ci-footer {
    text-align: center;
    font-size: 0.78rem;
    color: #9EA6B0;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #E8EDF2;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
div[data-testid="stTabs"] button[data-testid="stTab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
div[data-testid="stTabs"] button[data-testid="stTab"][aria-selected="true"] {
    color: #001731 !important;
    font-weight: 700 !important;
}

/* ── Narrative Drift ─────────────────────────────────────────────────────── */
.drift-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}
.drift-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #001731;
    letter-spacing: -0.01em;
}
.drift-basis {
    font-size: 0.78rem;
    font-weight: 500;
    color: #6B7580;
    background: #F0F4F8;
    border-radius: 999px;
    padding: 0.28rem 0.75rem;
}
.drift-headline {
    font-size: 1.02rem;
    font-weight: 500;
    line-height: 1.55;
    color: #1A2C3E;
    margin: 0.35rem 0 1.1rem;
}
.drift-tiles {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.1rem;
}
.drift-tile {
    background: #F6F8FA;
    border-radius: 12px;
    padding: 0.7rem 0.85rem;
}
.drift-tile-label {
    font-size: 0.76rem;
    color: #6B7580;
    margin-bottom: 0.15rem;
}
.drift-tile-value {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.1;
}
.drift-cards { display: flex; flex-direction: column; gap: 0.65rem; }
.drift-card {
    background: #FFFFFF;
    border: 1px solid #E6EAEF;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    box-shadow: 0 1px 3px rgba(14, 59, 84, 0.04);
}
.drift-card-head {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
}
.drift-badge {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 0.18rem 0.55rem;
    border-radius: 6px;
}
.drift-badge-added       { background: #FCEBEA; color: #B3261E; }
.drift-badge-intensified { background: #FDF0DD; color: #B4650A; }
.drift-badge-dropped     { background: #EEF0F3; color: #55606B; }
.drift-badge-tone        { background: #DFF0EC; color: #16534A; }
.drift-badge-emerged     { background: #DFF0EC; color: #16534A; }
.drift-badge-faded       { background: #EEF0F3; color: #55606B; }
.drift-badge-sentiment   { background: #E6F1FB; color: #1C5A86; }
.drift-card-label {
    font-size: 0.92rem;
    font-weight: 600;
    color: #001731;
}
.drift-card-summary {
    font-size: 0.88rem;
    line-height: 1.55;
    color: #46525E;
    margin: 0;
}
.drift-quote {
    font-size: 0.82rem;
    font-style: italic;
    line-height: 1.5;
    color: #6B7580;
    border-left: 2px solid #D5DCE3;
    padding: 0.1rem 0 0.1rem 0.7rem;
    margin: 0.5rem 0 0;
}
.drift-value-added       { color: #B3261E; }
.drift-value-intensified { color: #B4650A; }
.drift-value-dropped     { color: #6B7580; }
.drift-value-tone        { color: #16534A; }
</style>
"""


def badge_html(confidence: str) -> str:
    """Return an HTML confidence badge for a given confidence level.

    Args:
        confidence: One of High, Medium, Low, Insufficient Data.

    Returns:
        HTML string for the inline badge.
    """
    cls_map = {
        "High": "badge-high",
        "Medium": "badge-medium",
        "Low": "badge-low",
        "Insufficient Data": "badge-insufficient",
    }
    cls = cls_map.get(confidence, "badge-insufficient")
    label = confidence if confidence != "Insufficient Data" else "Insuff."
    return f'<span class="badge {cls}">{label}</span>'


def priority_badge_html(n: int) -> str:
    """Return an HTML priority number badge.

    Args:
        n: Priority number (1-based).

    Returns:
        HTML string for the badge.
    """
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:1.4rem;height:1.4rem;border-radius:50%;background:#F0F4F8;color:#001731;'
        f'font-size:0.7rem;font-weight:700;margin-right:0.5rem;flex-shrink:0;">{n}</span>'
    )
