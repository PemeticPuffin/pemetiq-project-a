"""Tests for entity_resolver — run from ci-autopilot/ directory."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.entity_resolver import resolve_company


def test_resolve_by_name():
    result = resolve_company("Apple")
    assert result.cik == 320193
    assert "Apple" in result.legal_name
    assert result.ticker == "AAPL"
    print(f"  name match: {result}")


def test_resolve_by_ticker():
    result = resolve_company("MSFT")
    assert result.ticker == "MSFT"
    assert "MICROSOFT" in result.legal_name.upper()
    print(f"  ticker match: {result}")


def test_resolve_unknown():
    try:
        resolve_company("XYZZY_DOES_NOT_EXIST_12345")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  correctly raised ValueError: {e}")


if __name__ == "__main__":
    for fn in [test_resolve_by_name, test_resolve_by_ticker, test_resolve_unknown]:
        print(f"Running {fn.__name__}...")
        fn()
    print("All tests passed.")
