"""Stress-test formulas checked against one hospital worked out by hand.

The example hospital:
  EBIDA 100, existing debt service 30, net patient revenue 1,000,
  Medicaid revenue 200, salaries 400, cash operating expenses 900.
"""

import pandas as pd
import pytest

from hcap import prepare, stress
from hcap.stress import Scenario


def s(*values: float | None) -> pd.Series:
    return pd.Series(values, dtype="float64")


def _stressed(scenario: Scenario) -> float:
    return stress.stressed_ebida(s(100), s(1000), s(200), s(400), s(900), scenario, 0.40).iloc[0]


def test_headroom() -> None:
    # 100 / 1.25 = 80 of payments supportable ; 80 - 30 already committed = 50
    assert stress.headroom(s(100), s(30), 1.25).tolist() == pytest.approx([50.0])


def test_headroom_negative_when_over_committed() -> None:
    # 100 / 1.25 = 80 ; 80 - 95 = -15
    assert stress.headroom(s(100), s(95), 1.25).tolist() == pytest.approx([-15.0])


def test_medicaid_cut() -> None:
    # 10% of 200 = 20 lost, no expense offset -> 80
    assert _stressed(Scenario(medicaid_cut=0.10)) == pytest.approx(80.0)


def test_volume_drop() -> None:
    # revenue -10% of 1,000 = -100 ; expenses fall 10% x 40% x 900 = 36 ; 100 - 100 + 36 = 36
    assert _stressed(Scenario(volume_drop=0.10)) == pytest.approx(36.0)


def test_labor_shock() -> None:
    # 5% of 400 = 20 more salaries -> 80
    assert _stressed(Scenario(labor_increase=0.05)) == pytest.approx(80.0)


def test_combined_compounds_the_three_shocks() -> None:
    # Medicaid: -20 -> patient revenue 980
    # volume:   -10% of 980 = -98
    # labor:    +20 salaries -> cash expenses 920
    # savings:  10% x 40% x 920 = 36.8
    # 100 - 20 - 98 - 20 + 36.8 = -1.2
    assert _stressed(Scenario(medicaid_cut=0.10, volume_drop=0.10, labor_increase=0.05)) == pytest.approx(-1.2)


def test_no_shock_leaves_ebida_unchanged() -> None:
    assert _stressed(Scenario()) == pytest.approx(100.0)


def test_medicaid_revenue_prefers_reported_then_falls_back_to_days() -> None:
    # reported 150 is used ; blank -> 20% of days x 1,000 = 200 ; negative and too-large are rejected
    out = stress.medicaid_revenue(s(150, None, -50, 5000), s(0.2, 0.2, 0.2, 0.2), s(1000, 1000, 1000, 1000))
    assert out.tolist() == pytest.approx([150, 200, 200, 200])


def test_annuity_factor() -> None:
    # 2 years at 10%: 1/1.1 + 1/1.21 = 0.909091 + 0.826446 = 1.735537
    assert stress.annuity_factor(0.10, 2) == pytest.approx(1.735537, abs=1e-6)
    assert stress.annuity_factor(0.0, 5) == 5.0


def test_affordable_principal() -> None:
    # payment of 100 a year for 2 years at 10% supports 173.55 ; no headroom supports nothing
    out = stress.affordable_principal(s(100, -40), 0.10, 2)
    assert out.tolist() == pytest.approx([173.5537, 0.0], abs=1e-3)


def test_run_takes_the_lowest_headroom_and_names_the_scenario() -> None:
    df = pd.DataFrame({
        "ebida": [100.0], "existing_debt_service": [30.0], "net_patient_revenue": [1000.0],
        "medicaid_net_revenue": [200.0], "medicaid_share_days": [0.2], "salaries": [400.0],
        "operating_expense": [960.0], "depreciation": [50.0], "interest_expense": [10.0],
    })
    scenarios = {"medicaid_cut": Scenario(medicaid_cut=0.10), "volume_drop": Scenario(volume_drop=0.10)}
    out = stress.run(df, scenarios, 1.25, 0.40, {"loan": {"annual_rate": 0.10, "term_years": 2}}).iloc[0]
    assert out["headroom_baseline"] == pytest.approx(50.0)
    assert out["headroom_medicaid_cut"] == pytest.approx(80 / 1.25 - 30)  # 34
    assert out["headroom_volume_drop"] == pytest.approx(36 / 1.25 - 30)  # -1.2
    assert out["headroom_stressed"] == pytest.approx(-1.2)
    assert out["binding_scenario"] == "volume_drop"
    assert out["principal_loan"] == 0.0


def test_assume_zero_interest_only_without_debt() -> None:
    interest = s(None, None, None, 50)
    reported = pd.Series([False, False, False, True])
    out = prepare.assume_zero_interest(interest, reported, s(0, 100, None, 0), s(0, 0, 0, 0))
    # no debt -> 0 ; has debt -> stays blank ; debt unknown -> stays blank ; reported value untouched
    assert out.iloc[0] == 0 and pd.isna(out.iloc[1]) and pd.isna(out.iloc[2]) and out.iloc[3] == 50
