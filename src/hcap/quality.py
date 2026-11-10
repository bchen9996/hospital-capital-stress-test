"""Phase 1 data quality checks. Each check returns a small frame; nothing is corrected."""

import pandas as pd

ID_COLS = ["ccn", "hospital_name", "ccn_facility_type"]

# Fields Phase 2 formulas read directly.
PHASE2_FIELDS = [
    "net_patient_revenue", "operating_expense", "other_income", "other_expenses", "net_income",
    "depreciation", "cash", "temp_investments", "salaries",
    "mortgage_payable", "notes_payable", "unsecured_loans", "other_lt_liabilities",
    "total_lt_liabilities", "notes_loans_short_term", "total_fund_balances",
    "days_medicare", "days_medicaid", "days_total", "medicaid_net_revenue",
    "star_rating", "hospital_type",
]

# A negative value in any of these is an accounting impossibility or a data-entry sign error.
NON_NEGATIVE_FIELDS = [
    "beds", "fte", "days_medicare", "days_medicaid", "days_total", "salaries", "depreciation",
    "total_costs", "cash", "temp_investments", "total_assets", "total_fixed_assets",
    "mortgage_payable", "notes_payable", "unsecured_loans", "notes_loans_short_term",
    "total_lt_liabilities", "total_patient_revenue", "net_patient_revenue", "operating_expense",
    "medicaid_net_revenue",
]


def missing_summary(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Count and share of missing values per field."""
    n = df[fields].isna().sum()
    return pd.DataFrame({"missing": n, "pct_missing": (100 * n / len(df)).round(1)}).reset_index(names="field")


def negative_values(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """One row per (hospital, field) where a should-be-non-negative field is below zero."""
    long = df.melt(id_vars=ID_COLS, value_vars=fields, var_name="field")
    return long[long["value"] < 0].sort_values(["field", "ccn"]).reset_index(drop=True)


def impossible_values(df: pd.DataFrame, balance_tolerance: float) -> pd.DataFrame:
    """Rows that fail internal-consistency checks, with the name of the failed check."""
    checks = {
        "payer days exceed total days":
            df["days_medicare"].fillna(0) + df["days_medicaid"].fillna(0) > df["days_total"],
        "balance sheet does not balance":
            (df["total_assets"] - df["total_liab_and_fund"]).abs() > balance_tolerance,
        "no balance sheet reported": df["total_assets"].isna(),
        "net patient revenue missing or zero": df["net_patient_revenue"].fillna(0) == 0,
        "net patient revenue exceeds gross charges":
            df["net_patient_revenue"] > df["total_patient_revenue"],
        "negative net assets (fund balance)": df["total_fund_balances"] < 0,
        "zero or missing total patient days": df["days_total"].fillna(0) == 0,
    }
    frames = [df.loc[mask, ID_COLS].assign(check=name) for name, mask in checks.items()]
    return pd.concat(frames, ignore_index=True)


def partial_year(df: pd.DataFrame) -> pd.DataFrame:
    """Cost reports whose period is shorter or longer than a normal fiscal year."""
    cols = [*ID_COLS, "fy_begin", "fy_end", "period_days", "reports_for_ccn"]
    return df.loc[~df["is_full_year"], cols].sort_values("period_days").reset_index(drop=True)


def duplicate_ccn(df: pd.DataFrame) -> pd.DataFrame:
    """Hospitals with more than one cost report in the file."""
    cols = [*ID_COLS, "fy_begin", "fy_end", "period_days", "is_latest_for_ccn"]
    return df.loc[df["reports_for_ccn"] > 1, cols].sort_values(["ccn", "fy_begin"]).reset_index(drop=True)


HCRIS_FIELDS = ["accumulated_depreciation", "interest_ws_a", "interest_a7_booked", "interest_a7_allowable"]


def hcris_agreement(df: pd.DataFrame, fields: list[str], tolerance: float = 1.0) -> pd.DataFrame:
    """Compare public-file values with the same cells re-read from raw HCRIS.

    Split by whether the two sources hold the same version of the report. Same-version
    rows should agree exactly; that is the proof the worksheet parsing is right.
    """
    rows = []
    for same, group in df[df["hcris_matched"]].groupby("hcris_same_version"):
        for field in fields:
            both = group[[field, f"hcris_{field}"]].dropna()
            agree = ((both[field] - both[f"hcris_{field}"]).abs() <= tolerance).sum()
            rows.append({
                "version": "same record number" if same else "different record number",
                "field": field, "compared": len(both), "agree": int(agree), "differ": int(len(both) - agree),
            })
    return pd.DataFrame(rows)


def fixed_asset_rollup(df: pd.DataFrame, tolerance: float = 1.0) -> pd.DataFrame:
    """Reports where gross fixed assets minus accumulated depreciation is not G line 30."""
    out = df[[*ID_COLS, "hcris_gross_fixed_assets", "accumulated_depreciation", "hcris_total_fixed_assets"]].copy()
    out["gap"] = (
        out["hcris_gross_fixed_assets"].fillna(0) - out["accumulated_depreciation"].fillna(0)
        - out["hcris_total_fixed_assets"]
    )
    return out[out["gap"].abs() > tolerance].reset_index(drop=True)


def unmatched_hcris(df: pd.DataFrame) -> pd.DataFrame:
    """Cost reports with no raw HCRIS record for the same CCN and period."""
    return df.loc[~df["hcris_matched"], [*ID_COLS, "fy_begin", "fy_end"]].reset_index(drop=True)


def unmatched_hgi(df: pd.DataFrame) -> pd.DataFrame:
    """Cost reports with no row in Hospital General Information."""
    return df.loc[~df["hgi_matched"], ID_COLS].sort_values("ccn").reset_index(drop=True)
