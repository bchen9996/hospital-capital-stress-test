"""Phase 3: headroom, stress scenarios, and conversion of headroom to principal.

"Headroom" is the extra annual debt or rent payment a hospital could take on while
still keeping EBIDA at the target multiple of its total payments.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Scenario:
    """One stress scenario. Each shock is a fraction (0.10 = 10%); zero means not applied."""

    medicaid_cut: float = 0.0
    volume_drop: float = 0.0
    labor_increase: float = 0.0


def headroom(ebida: pd.Series, existing_debt_service: pd.Series, target_dscr: float) -> pd.Series:
    """(EBIDA / target DSCR) - existing debt service. Negative means already over-committed."""
    return ebida / target_dscr - existing_debt_service


def medicaid_revenue(reported: pd.Series, medicaid_share_days: pd.Series, net_patient_revenue: pd.Series) -> pd.Series:
    """Medicaid net revenue: the reported figure (Worksheet S-10) where it is usable,
    otherwise Medicaid's share of inpatient days times net patient revenue.

    "Usable" means positive and no larger than net patient revenue.
    """
    usable = (reported > 0) & (reported <= net_patient_revenue)
    return reported.where(usable, medicaid_share_days * net_patient_revenue)


def stressed_ebida(
    ebida: pd.Series,
    net_patient_revenue: pd.Series,
    medicaid_rev: pd.Series,
    salaries: pd.Series,
    cash_operating_expenses: pd.Series,
    scenario: Scenario,
    variable_cost_share: float,
) -> pd.Series:
    """EBIDA after a scenario's shocks.

    Shocks compound in this order:
      1. Medicaid revenue falls by `medicaid_cut`. No expense falls with it (a rate cut).
      2. What is left of patient revenue falls by `volume_drop`.
      3. Salaries rise by `labor_increase`.
      4. Cash operating expenses (after the salary rise) fall by
         `volume_drop` x `variable_cost_share`; the rest are treated as fixed.
    """
    medicaid_loss = medicaid_rev * scenario.medicaid_cut
    volume_loss = (net_patient_revenue - medicaid_loss) * scenario.volume_drop
    salary_rise = salaries * scenario.labor_increase
    volume_savings = (cash_operating_expenses + salary_rise) * scenario.volume_drop * variable_cost_share
    return ebida - medicaid_loss - volume_loss - salary_rise + volume_savings


def annuity_factor(annual_rate: float, term_years: int) -> float:
    """Principal supported by a payment of 1 a year: (1 - (1 + r)^-n) / r."""
    if annual_rate == 0:
        return float(term_years)
    return (1 - (1 + annual_rate) ** -term_years) / annual_rate


def affordable_principal(annual_payment: pd.Series, annual_rate: float, term_years: int) -> pd.Series:
    """Level-payment loan a given annual payment can carry. Zero when there is no headroom."""
    return annual_payment.clip(lower=0) * annuity_factor(annual_rate, term_years)


def run(
    df: pd.DataFrame,
    scenarios: dict[str, Scenario],
    target_dscr: float,
    variable_cost_share: float,
    capital_types: dict[str, dict],
) -> pd.DataFrame:
    """Add baseline and scenario headroom, stressed headroom, and principal per capital type.

    `df` is the Phase 2 metrics table. Stressed headroom is the lowest of the baseline
    and every scenario; it is missing if any of them could not be computed.
    """
    out = df.copy()
    out["medicaid_revenue_est"] = medicaid_revenue(
        out["medicaid_net_revenue"], out["medicaid_share_days"], out["net_patient_revenue"])
    cash_opex = out["operating_expense"] - out["depreciation"] - out["interest_expense"]

    out["headroom_baseline"] = headroom(out["ebida"], out["existing_debt_service"], target_dscr)
    columns = ["headroom_baseline"]
    for name, scenario in scenarios.items():
        ebida_s = stressed_ebida(
            out["ebida"], out["net_patient_revenue"], out["medicaid_revenue_est"],
            out["salaries"], cash_opex, scenario, variable_cost_share)
        out[f"ebida_{name}"] = ebida_s
        out[f"headroom_{name}"] = headroom(ebida_s, out["existing_debt_service"], target_dscr)
        columns.append(f"headroom_{name}")

    out["headroom_stressed"] = out[columns].min(axis=1, skipna=False)
    complete = out.loc[out["headroom_stressed"].notna(), columns]
    out["binding_scenario"] = complete.idxmin(axis=1).str.removeprefix("headroom_")
    for key, terms in capital_types.items():
        out[f"principal_{key}"] = affordable_principal(
            out["headroom_stressed"], terms["annual_rate"], terms["term_years"])
    return out
