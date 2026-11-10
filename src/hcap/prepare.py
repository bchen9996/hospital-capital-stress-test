"""Turn the Phase 1 table into clean, annual inputs for the metric formulas.

Every judgement call (scope, blanks, partial years, what counts as debt and interest)
lives here, so metrics.py stays pure arithmetic.
"""

import pandas as pd

from hcap import metrics

BALANCE_SHEET_LINES = [
    "cash", "temp_investments", "notes_loans_short_term",
    "mortgage_payable", "notes_payable", "unsecured_loans", "other_lt_liabilities",
]
INCOME_LINES = ["other_income", "other_expenses"]

# Amounts that accumulate over the reporting period, so a short period needs scaling up.
FLOW_FIELDS = [
    "net_patient_revenue", "total_patient_revenue", "operating_expense", "other_income",
    "other_expenses", "net_income", "depreciation", "salaries", "medicaid_net_revenue",
    "interest_ws_a", "interest_a7_booked",
]


def select_reports(df: pd.DataFrame, facility_types: list[str], min_period_days: int) -> pd.DataFrame:
    """One report per hospital: in-scope types, latest period, long enough to annualize."""
    keep = df["ccn_facility_type"].isin(facility_types) & df["is_latest_for_ccn"]
    return df[keep & (df["period_days"] >= min_period_days)].reset_index(drop=True)


def fill_blank_lines(df: pd.DataFrame) -> pd.DataFrame:
    """Read a blank line as zero, but only where the hospital filed that statement."""
    out = df.copy()
    has_balance_sheet = out["total_assets"].notna()
    has_income_statement = out["net_income"].notna()
    for col in BALANCE_SHEET_LINES:
        out.loc[has_balance_sheet, col] = out.loc[has_balance_sheet, col].fillna(0)
    for col in INCOME_LINES:
        out.loc[has_income_statement, col] = out.loc[has_income_statement, col].fillna(0)
    return out


def annualize(df: pd.DataFrame, days_in_year: int) -> pd.DataFrame:
    """Scale flow amounts of partial-year reports to a full year. Full-year rows are untouched."""
    out = df.copy()
    partial = ~out["is_full_year"]
    factor = days_in_year / out.loc[partial, "period_days"]
    for col in FLOW_FIELDS:
        out.loc[partial, col] = out.loc[partial, col] * factor
    out["annualized"] = partial
    return out


def interest_expense(interest_ws_a: pd.Series, interest_a7_booked: pd.Series) -> pd.Series:
    """Interest as booked: Worksheet A line 113 plus A-7 Part II capital interest.

    Missing when neither cell is reported, and missing when the total is negative.
    It is never assumed to be zero.
    """
    total = pd.concat([interest_ws_a, interest_a7_booked], axis=1).sum(axis=1, min_count=1)
    return total.where(total >= 0)


def long_term_debt(mortgage: pd.Series, notes: pd.Series, unsecured: pd.Series) -> pd.Series:
    """Mortgages + notes + unsecured loans. Missing if any component is negative.

    Negative components are health-system intercompany balances, not debt.
    """
    parts = pd.concat([mortgage, notes, unsecured], axis=1)
    return parts.sum(axis=1, skipna=False).where((parts >= 0).all(axis=1))


def current_portion_proxy(notes_loans_short_term: pd.Series) -> pd.Series:
    """Short-term notes and loans, standing in for current portion of long-term debt."""
    return notes_loans_short_term.where(notes_loans_short_term >= 0)


def build_flags(df: pd.DataFrame) -> pd.Series:
    """Plain-English caveats for each hospital, joined with '; '."""
    has_debt = (df["long_term_debt"] > 0) | (df["notes_loans_short_term"] > 0)
    no_interest = df["interest_ws_a"].isna() & df["interest_a7_booked"].isna()
    tests = {
        "partial year scaled to 12 months": df["annualized"],
        "values taken from newer HCRIS version": df["values_from_hcris"],
        "no balance sheet": df["total_assets"].isna(),
        "interest not reported, but debt on balance sheet": no_interest & has_debt,
        "interest not reported, no debt on balance sheet": no_interest & ~has_debt,
        "interest negative, unusable": ~no_interest & df["interest_expense"].isna(),
        "long-term debt unusable (negative component)":
            df["total_assets"].notna() & df["long_term_debt"].isna(),
        "short-term notes negative, unusable": df["notes_loans_short_term"] < 0,
        "negative cash": df["cash"] < 0,
        "negative net assets": df["total_fund_balances"] < 0,
        "no patient days reported": df["days_total"].fillna(0) == 0,
    }
    labels = pd.DataFrame(tests).fillna(False)
    return labels.apply(lambda row: "; ".join(labels.columns[row.to_numpy(dtype=bool)]), axis=1)


def compute_metrics(df: pd.DataFrame, includes_other_income: bool, days_in_year: int) -> pd.DataFrame:
    """Add derived inputs, the Phase 2 metrics, and the flags column."""
    out = df.copy()
    out["interest_expense"] = interest_expense(out["interest_ws_a"], out["interest_a7_booked"])
    out["long_term_debt"] = long_term_debt(out["mortgage_payable"], out["notes_payable"], out["unsecured_loans"])
    out["current_portion_ltd"] = current_portion_proxy(out["notes_loans_short_term"])
    out["operating_revenue"] = out["net_patient_revenue"] + (out["other_income"] if includes_other_income else 0)
    out["total_expenses"] = out["operating_expense"] + out["other_expenses"]

    out["operating_margin"] = metrics.operating_margin(out["operating_revenue"], out["operating_expense"])
    out["ebida"] = metrics.ebida(out["net_income"], out["interest_expense"], out["depreciation"])
    out["days_cash_on_hand"] = metrics.days_cash_on_hand(
        out["cash"], out["temp_investments"], out["total_expenses"], out["depreciation"], days_in_year)
    out["avg_age_of_plant"] = metrics.average_age_of_plant(out["accumulated_depreciation"], out["depreciation"])
    out["debt_to_capitalization"] = metrics.debt_to_capitalization(out["long_term_debt"], out["total_fund_balances"])
    out["existing_debt_service"] = metrics.existing_debt_service(out["interest_expense"], out["current_portion_ltd"])
    out["medicaid_share_days"] = metrics.payer_share(out["days_medicaid"], out["days_total"])
    out["medicare_share_days"] = metrics.payer_share(out["days_medicare"], out["days_total"])
    out["flags"] = build_flags(out)
    return out
