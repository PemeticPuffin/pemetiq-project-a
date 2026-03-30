# RENAME: CI Autopilot → Cadillaq

## What's Changing
The tool formerly called "CI Autopilot" is now branded **Cadillaq** (subtitle: "Competitive Intelligence Autopilot"). Named after Cadillac Mountain in Acadia National Park, Maine — subtle letter swap, same pronunciation.

## Where to Apply the Rename

### Must Change (user-facing)
1. **`app.py`** — `st.set_page_config(page_title=...)`: Change from `"CI Autopilot | Pemetiq"` to `"Cadillaq | Pemetiq"`
2. **`app.py`** — Any hero/header text that says "CI Autopilot" or "Competitive Intelligence Autopilot" → replace with:
   - Primary name: **Cadillaq**
   - Subtitle (where it appears): **Competitive intelligence autopilot**
3. **`src/ui/styling.py`** and **`src/ui/components.py`** — Any hardcoded strings referencing the old name in headers, banners, or UI copy
4. **`.streamlit/config.toml`** — If there's a page title or app name configured here
5. **`README.md`** — Update project title and description

### Should Change (branding consistency)
6. **`src/analysis/prompts.py`** — If any system prompts reference "CI Autopilot" by name (e.g., "You are the CI Autopilot analysis engine..."), update to "Cadillaq"
7. **SEC EDGAR User-Agent** in `config.py` — Currently `"Pemetiq CI-Autopilot hello@pemetiq.com"`. Update to `"Pemetiq Cadillaq hello@pemetiq.com"`

### Do NOT Change
- Internal variable names, function names, module names, or folder structure — no need to rename `ci-autopilot/` to `cadillaq/` or refactor code identifiers. This is a branding change, not a refactor.
- The `page_icon` emoji can stay as-is

## Subtitle Pattern
Wherever the name appears in the UI, use this format:
- **Large/hero context:** "Cadillaq" (mountain name alone, bold, prominent)
- **With context:** "Cadillaq — Competitive intelligence autopilot"
- Never: "Cadillaq CI Autopilot" or "The Cadillaq" — the mountain name IS the product name

## Brand Note
Cadillaq is one of two Pemetiq tools. The other is Manseil (Narrative Stress Test). They are complementary:
- Cadillaq synthesizes **upward** from data → "What should I know?"
- Manseil tests **downward** from claims → "Should I believe this?"
