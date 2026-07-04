"""Tests for coverage analysis."""

from __future__ import annotations

from sumsmaster.coverage import addition_domain, analyze, division_domain, multiplication_domain, subtraction_domain


def test_multiplication_grid_coverage_high() -> None:
    """The 12x12 grid should be near-fully covered by the trick library."""
    report = analyze("mul", multiplication_domain(0, 12))
    assert report.total_facts == 169
    assert report.coverage_pct >= 99.0


def test_addition_grid_coverage_high() -> None:
    report = analyze("add", addition_domain(0, 12))
    assert report.total_facts == 169
    assert report.coverage_pct >= 99.0


def test_subtraction_coverage_reasonable() -> None:
    report = analyze("sub", subtraction_domain(0, 20))
    # Subtraction is the hardest domain; we expect >=95% with the inverse
    # fallback included.
    assert report.coverage_pct >= 95.0


def test_division_coverage_total() -> None:
    report = analyze("div", division_domain(1, 12))
    # Inverse-of-mul covers everything by construction.
    assert report.coverage_pct == 100.0


def test_per_trick_hits_nonempty_for_covered_facts() -> None:
    report = analyze("mul", multiplication_domain(0, 12))
    assert sum(report.per_trick_hits.values()) > 0
    # Every covered fact contributed to at least one trick's hit count.
    assert report.covered_facts <= sum(report.per_trick_hits.values())


def test_uncovered_list_matches_count() -> None:
    report = analyze("sub", subtraction_domain(0, 20))
    assert len(report.uncovered) == report.total_facts - report.covered_facts
