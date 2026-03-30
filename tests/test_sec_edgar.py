"""Tests for sec_edgar — fetches live data from SEC EDGAR."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.data.sec_edgar import fetch_latest_filing, format_sections_for_prompt


def test_apple_filing():
    filing = fetch_latest_filing(cik=320193, company_name="Apple Inc.")
    assert filing.fetch_error is None, f"Unexpected error: {filing.fetch_error}"
    assert filing.form_type in ("10-K", "10-Q"), f"Unexpected form: {filing.form_type}"
    assert len(filing.sections) > 0, "No sections extracted"
    print(f"  Form: {filing.form_type}, filed: {filing.filed_date}")
    print(f"  Sections: {list(filing.sections.keys())}")
    for name, text in filing.sections.items():
        print(f"  [{name}] {len(text):,} chars")


def test_format_prompt():
    filing = fetch_latest_filing(cik=320193, company_name="Apple Inc.")
    text = format_sections_for_prompt(filing)
    assert "SEC" in text
    assert len(text) > 100
    print(f"  Formatted prompt text: {len(text):,} chars")


def test_bad_cik():
    filing = fetch_latest_filing(cik=999999999, company_name="Fake Co")
    assert filing.fetch_error is not None
    print(f"  Correctly got error: {filing.fetch_error[:80]}")


if __name__ == "__main__":
    for fn in [test_apple_filing, test_format_prompt, test_bad_cik]:
        print(f"Running {fn.__name__}...")
        fn()
    print("All SEC tests passed.")
