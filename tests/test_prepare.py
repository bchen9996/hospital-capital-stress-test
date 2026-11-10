"""Tests for the data-preparation rules that feed the metric formulas."""

import pandas as pd
import pytest

from hcap import prepare


def s(*values: float | None) -> pd.Series:
    return pd.Series(values, dtype="float64")


def test_select_reports_scope_latest_and_minimum_length() -> None:
    df = pd.DataFrame({
        "ccn": ["1", "2", "3", "3", "4"],
        "ccn_facility_type": ["STH", "PH", "CAH", "CAH", "STH"],
        "is_latest_for_ccn": [True, True, False, True, True],
        "period_days": [365, 365, 274, 365, 43],
    })
    out = prepare.select_reports(df, ["STH", "CAH"], 180)
    # 2 is psychiatric, first row of 3 is superseded, 4 is only 43 days
    assert out[["ccn", "period_days"]].values.tolist() == [["1", 365], ["3", 365]]


def test_interest_adds_the_two_booked_sources() -> None:
    out = prepare.interest_expense(s(100, None, None), s(None, 40, None))
    assert out.iloc[:2].tolist() == [100, 40]
    assert pd.isna(out.iloc[2])  # nothing reported stays missing, not zero


def test_interest_negative_is_unusable() -> None:
    assert prepare.interest_expense(s(None), s(-500)).isna().all()


def test_long_term_debt_sums_three_lines() -> None:
    assert prepare.long_term_debt(s(10), s(20), s(5)).tolist() == [35]


def test_long_term_debt_missing_if_any_component_negative_or_blank() -> None:
    out = prepare.long_term_debt(s(10, 10), s(20, None), s(-500, 5))
    assert out.isna().all()


def test_annualize_scales_only_partial_years() -> None:
    row = {c: [100.0, 100.0] for c in prepare.FLOW_FIELDS}
    df = pd.DataFrame({**row, "period_days": [365, 73], "is_full_year": [True, False], "cash": [7.0, 7.0]})
    out = prepare.annualize(df, 365)
    # 73 days is one fifth of a year, so 100 becomes 500; the full-year row and cash are untouched
    assert out["net_income"].tolist() == pytest.approx([100, 500])
    assert out["cash"].tolist() == [7, 7]
    assert out["annualized"].tolist() == [False, True]


def test_fill_blank_lines_only_when_statement_was_filed() -> None:
    blank = {c: [None, None] for c in [*prepare.BALANCE_SHEET_LINES, *prepare.INCOME_LINES]}
    df = pd.DataFrame({**blank, "total_assets": [500.0, None], "net_income": [None, 9.0]}).astype("float64")
    out = prepare.fill_blank_lines(df)
    assert out.loc[0, "cash"] == 0 and pd.isna(out.loc[1, "cash"])
    assert pd.isna(out.loc[0, "other_expenses"]) and out.loc[1, "other_expenses"] == 0
