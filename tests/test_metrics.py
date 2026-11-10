"""Each formula checked against a small example worked out by hand (see comments)."""

import pandas as pd
import pytest

from hcap import metrics


def s(*values: float | None) -> pd.Series:
    return pd.Series(values, dtype="float64")


def test_operating_margin() -> None:
    # (100 - 90) / 100 = 0.10 ; (200 - 250) / 200 = -0.25
    out = metrics.operating_margin(s(100, 200), s(90, 250))
    assert out.tolist() == pytest.approx([0.10, -0.25])


def test_operating_margin_missing_when_revenue_is_zero() -> None:
    assert metrics.operating_margin(s(0), s(50)).isna().all()


def test_ebida() -> None:
    # 5 + 2 + 8 = 15 ; a loss of 10 + 3 + 4 = -3
    assert metrics.ebida(s(5, -10), s(2, 3), s(8, 4)).tolist() == [15, -3]


def test_ebida_missing_when_interest_missing() -> None:
    assert metrics.ebida(s(5), s(None), s(8)).isna().all()


def test_days_cash_on_hand() -> None:
    # cash 60 + investments 40 = 100 ; daily cash expenses = (830 - 100) / 365 = 2 ; 100 / 2 = 50 days
    out = metrics.days_cash_on_hand(s(60), s(40), s(830), s(100), 365)
    assert out.tolist() == pytest.approx([50.0])


def test_average_age_of_plant() -> None:
    # 120 accumulated / 10 a year = 12 years
    assert metrics.average_age_of_plant(s(120), s(10)).tolist() == [12.0]


def test_average_age_of_plant_missing_when_no_depreciation() -> None:
    assert metrics.average_age_of_plant(s(120), s(0)).isna().all()


def test_debt_to_capitalization() -> None:
    # 30 / (30 + 70) = 0.30 ; no debt = 0
    assert metrics.debt_to_capitalization(s(30, 0), s(70, 50)).tolist() == pytest.approx([0.30, 0.0])


def test_debt_to_capitalization_missing_when_capitalization_not_positive() -> None:
    # debt 30, net assets -40 -> capitalization -10 -> no meaningful ratio
    assert metrics.debt_to_capitalization(s(30), s(-40)).isna().all()


def test_existing_debt_service() -> None:
    # interest 4 + current portion 6 = 10
    assert metrics.existing_debt_service(s(4), s(6)).tolist() == [10]


def test_payer_share() -> None:
    # 250 Medicaid days of 1,000 = 25%
    assert metrics.payer_share(s(250), s(1000)).tolist() == [0.25]
    assert metrics.payer_share(s(250), s(0)).isna().all()
