"""CSS and brand styling for the Cadillaq Streamlit app.

Colors come from the Pemetiq token set, canonically defined in
PemeticPuffin/pemetiq-ops -> design/PEMETIQ_TOKENS.md. The CSS below declares
them once as custom properties on :root and references them everywhere else,
so a palette change is a one-place edit.
"""

# Pemetiq brand colors — anchored on the wordmark SVG.
PRIMARY = "#134256"
SECONDARY = "#1A5C6A"
ACCENT = "#cf5e40"
ACCENT_DARK = "#ae3f1b"
ACCENT_LIGHT = "#f2a892"
BACKGROUND = "#F0EDE8"
TEXT = "#2E2A26"
MUTED = "#6E675E"

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── Pemetiq design tokens ───────────────────────────────────────── */
:root {
    --navy: #134256;
    --navy-lift: #17506a;      /* gradient partner for navy grounds */
    --coral: #cf5e40;          /* fills only — 3.38:1, not for small text */
    --coral-dark: #ae3f1b;     /* ANY coral touching text — fills behind white,
                                  or coral used as text. Covers all three grounds. */
    --coral-light: #f2a892;    /* eyebrow labels on navy grounds */
    --teal: #1A5C6A;

    --cream: #F0EDE8;
    --surface: #FFFFFF;
    --text: #2E2A26;
    --text-2: #4A443C;
    --muted: #6E675E;
    --border: #DDD8D0;
    --border-strong: #C9C2B8;
    --wash: #EDE9E2;           /* subtle warm fill for tiles/pills */
    --wash-2: #F5F2ED;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    background: var(--cream);
}

.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
}

/* ── Multiselect filter chips ────────────────────────────────────
   Streamlit's baseweb tags fill with primaryColor and set white text: white on
   coral is 3.94:1, short of AA at 12px. Deepen the fill to coral-dark (5.95:1). */
span[data-baseweb="tag"] {
    background-color: var(--coral-dark) !important;
}

/* ── Selected segmented-control label ────────────────────────────
   Streamlit tints the selected segment with primaryColor at 10% alpha, so coral
   text lands on a coral wash at only 3.03:1. Deepen the label so the state still
   reads as coral but clears AA at 14px. */
button[aria-checked="true"],
button[aria-checked="true"] * {
    color: var(--coral-dark) !important;
}

/* ── Hide Streamlit chrome ──────────────────────────────────────── */
header[data-testid="stHeader"], #MainMenu, footer,
.stDeployButton { display: none !important; }

/* ── Header ──────────────────────────────────────────────────────── */
.ci-header {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-lift) 100%);
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
    color: var(--coral-light);
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
    border: 2px solid var(--border) !important;
    padding: 0.7rem 1rem !important;
    font-size: 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
    background: var(--surface) !important;
    transition: border-color 0.15s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 2px rgba(19,66,86,0.10) !important;
    outline: none !important;
}

/* ── Primary button ──────────────────────────────────────────────── */
/* Fill is coral-dark, not coral: white on #cf5e40 is 3.94:1, short of AA at 14px.
   White on coral-dark is 5.95:1. */
div[data-testid="stButton"] button[kind="primary"] {
    background: var(--coral-dark) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    height: 44px !important;
    transition: background 0.15s ease !important;
}
/* Hover darkens the same token rather than introducing a fourth coral —
   brightness() keeps the contrast gain monotonic, so hover can never fail. */
div[data-testid="stButton"] button[kind="primary"]:hover {
    filter: brightness(0.88);
}

/* ── Sample brief chips ──────────────────────────────────────────── */
[class*="st-key-sample_"] button {
    height: 42px !important;
    min-height: 42px !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 8px !important;
    background: var(--surface) !important;
    color: var(--navy) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0 0.85rem !important;
    transition: border-color 0.15s ease, color 0.15s ease !important;
}
[class*="st-key-sample_"] button:hover {
    border-color: var(--coral) !important;
    color: var(--coral-dark) !important;
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
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.section-subtitle {
    font-size: 0.84rem;
    color: var(--muted);
    margin-bottom: 1rem;
}

/* ── Company brief card ──────────────────────────────────────────── */
.company-brief-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 4px rgba(19, 66, 86, 0.05);
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
    background: var(--navy);
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
    color: var(--navy);
    margin: 0 0 0.2rem 0;
}
.company-meta {
    font-size: 0.79rem;
    color: var(--muted);
}
.exec-summary-p {
    font-size: 0.95rem;
    line-height: 1.72;
    color: var(--text);
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
    color: var(--text);
}
.signal-section-subtitle {
    font-size: 0.84rem;
    color: var(--muted);
    margin-bottom: 1.2rem;
    padding-left: 1.1rem;
}

/* ── Signal cards ────────────────────────────────────────────────── */
.signal-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 3px rgba(19, 66, 86, 0.04);
    display: flex;
    flex-direction: column;
}
.signal-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--navy);
    margin-bottom: 0.45rem;
    line-height: 1.35;
}
.signal-card-body {
    font-size: 0.86rem;
    line-height: 1.6;
    color: var(--text-2);
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
.source-tag-default { background: var(--wash); color: var(--text-2); }

/* ── Contradictions banner ───────────────────────────────────────── */
.contradictions-banner {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-lift) 100%);
    border-radius: 12px 12px 0 0;
    padding: 1.5rem 1.8rem 1.4rem;
    margin-top: 1.8rem;
}
.contradictions-banner .contrad-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--coral-light);
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
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
}

/* ── Contradiction cards ─────────────────────────────────────────── */
.contradiction-v2 {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    background: var(--surface);
}
.contradiction-number {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--coral-dark);
    margin-bottom: 0.5rem;
}
.contradiction-title {
    font-size: 0.97rem;
    font-weight: 700;
    color: var(--navy);
    margin-bottom: 0.6rem;
    line-height: 1.35;
}
.contradiction-desc {
    font-size: 0.85rem;
    line-height: 1.6;
    color: var(--text-2);
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
    color: var(--text-2);
    font-style: italic;
}

/* ── Notable absences ────────────────────────────────────────────── */
.absence-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.absence-section-subtitle {
    font-size: 0.84rem;
    color: var(--muted);
    margin-bottom: 1.1rem;
}
.absence-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.72rem 0;
    font-size: 0.87rem;
    color: var(--text);
    line-height: 1.45;
}
.absence-dash {
    color: var(--border-strong);
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
    color: var(--text);
    margin-bottom: 0.25rem;
}
.watch-section-subtitle {
    font-size: 0.84rem;
    color: var(--muted);
    margin-bottom: 1.1rem;
}
.watch-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 1px 3px rgba(19, 66, 86, 0.04);
}
.watch-card-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--navy);
    margin-bottom: 0.4rem;
    line-height: 1.35;
}
.watch-card-body {
    font-size: 0.84rem;
    line-height: 1.55;
    color: var(--text-2);
}

/* ── Per-source findings ─────────────────────────────────────────── */
.findings-section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.findings-section-subtitle {
    font-size: 0.83rem;
    color: var(--muted);
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
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}
.finding-text-v2 {
    font-size: 0.9rem;
    line-height: 1.58;
    color: var(--text);
    margin-bottom: 0.4rem;
}
.finding-source-link {
    font-size: 0.78rem;
    color: var(--teal);
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
    color: var(--muted);
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
}

/* ── Tabs ────────────────────────────────────────────────────────── */
div[data-testid="stTabs"] button[data-testid="stTab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
/* Streamlit colours the selected tab with primaryColor; coral on cream is only
   3.38:1. Deepen it — the selected state still reads coral but clears AA.
   Selector is attribute-light because Streamlit's stTab testids shift between
   releases; [aria-selected] is the stable hook. */
[role="tab"][aria-selected="true"],
[role="tab"][aria-selected="true"] * {
    color: var(--coral-dark) !important;
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
    color: var(--navy);
    letter-spacing: -0.01em;
}
.drift-basis {
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--muted);
    background: var(--wash);
    border-radius: 999px;
    padding: 0.28rem 0.75rem;
}
.drift-headline {
    font-size: 1.02rem;
    font-weight: 500;
    line-height: 1.55;
    color: var(--text);
    margin: 0.35rem 0 1.1rem;
}
.drift-tiles {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.1rem;
}
.drift-tile {
    background: var(--wash-2);
    border-radius: 12px;
    padding: 0.7rem 0.85rem;
}
.drift-tile-label {
    font-size: 0.76rem;
    color: var(--muted);
    margin-bottom: 0.15rem;
}
.drift-tile-value {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.1;
}
.drift-cards { display: flex; flex-direction: column; gap: 0.65rem; }
.drift-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    box-shadow: 0 1px 3px rgba(19, 66, 86, 0.04);
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
.drift-badge-dropped     { background: var(--wash); color: var(--text-2); }
.drift-badge-tone        { background: #DFF0EC; color: #16534A; }
.drift-badge-emerged     { background: #DFF0EC; color: #16534A; }
.drift-badge-faded       { background: var(--wash); color: var(--text-2); }
.drift-badge-sentiment   { background: #E6F1FB; color: #1C5A86; }
.drift-card-label {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--navy);
}
.drift-card-summary {
    font-size: 0.88rem;
    line-height: 1.55;
    color: var(--text-2);
    margin: 0;
}
.drift-quote {
    font-size: 0.82rem;
    font-style: italic;
    line-height: 1.5;
    color: var(--muted);
    border-left: 2px solid var(--border-strong);
    padding: 0.1rem 0 0.1rem 0.7rem;
    margin: 0.5rem 0 0;
}
.drift-value-added       { color: #B3261E; }
.drift-value-intensified { color: #B4650A; }
.drift-value-dropped     { color: var(--muted); }
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
        f'width:1.4rem;height:1.4rem;border-radius:50%;background:var(--wash);'
        f'color:var(--navy);font-size:0.7rem;font-weight:700;margin-right:0.5rem;'
        f'flex-shrink:0;">{n}</span>'
    )
