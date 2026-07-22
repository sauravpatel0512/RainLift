"""Rain vs dry lift formula (Section 8)."""

from __future__ import annotations


def test_lift_formula_matches_spec() -> None:
    rainy_avg = 120.0
    dry_avg = 100.0
    lift = rainy_avg / dry_avg if dry_avg else None
    assert abs(lift - 1.2) < 1e-9

    rainy_avg_empty = None
    dry_avg = 100.0
    lift_null = rainy_avg_empty / dry_avg if rainy_avg_empty is not None and dry_avg else None
    assert lift_null is None
