"""Run Phase 2: compute financial metrics for in-scope hospitals.

Usage:  python scripts/phase2.py      (run scripts/phase1.py first)
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hcap import ingest, prepare  # noqa: E402
from hcap.config import load_config  # noqa: E402

METRICS = [
    "operating_margin", "ebida", "days_cash_on_hand", "avg_age_of_plant",
    "debt_to_capitalization", "existing_debt_service", "medicaid_share_days", "medicare_share_days",
]
OUTPUT = [
    "ccn", "hospital_name", "city", "county", "ccn_facility_type", "hospital_type", "ownership",
    "star_rating", "rural_urban", "beds", "fy_begin", "fy_end", "period_days",
    "operating_revenue", "operating_expense", "net_income", "depreciation", "interest_expense",
    "cash", "temp_investments", "long_term_debt", "current_portion_ltd", "total_fund_balances",
    "accumulated_depreciation", "salaries", "medicaid_net_revenue", "total_patient_revenue",
    "net_patient_revenue", "other_income", "other_expenses", "total_expenses",
    *METRICS, "flags",
]


def summary(result: pd.DataFrame) -> str:
    """Markdown summary: coverage and spread of each metric, and how often each flag fires."""
    stats = result[METRICS].describe(percentiles=[0.25, 0.5, 0.75]).T
    stats = stats[["count", "min", "25%", "50%", "75%", "max"]].rename(columns={"count": "hospitals with a value"})
    flags = result["flags"].str.split("; ").explode()
    flag_counts = flags[flags != ""].value_counts().rename_axis("flag").reset_index(name="hospitals")
    return "\n\n".join([
        f"# Phase 2 metrics summary\n\n{len(result)} hospitals in scope.",
        "## Coverage and spread\n\n" + stats.round(3).to_markdown(),
        "## Flags\n\n" + flag_counts.to_markdown(index=False),
    ])


def main() -> None:
    cfg = load_config()
    data, scope, m = cfg["data"], cfg["scope"], cfg["metrics"]
    with duckdb.connect(str(ROOT / data["db_path"]), read_only=True) as con:
        hospitals = con.execute("SELECT * FROM hospitals").df()

    selected = prepare.select_reports(hospitals, scope["facility_types"], scope["min_period_days"])
    if m["blank_lines_are_zero_when_statement_filed"]:
        selected = prepare.fill_blank_lines(selected)
    selected = prepare.annualize(selected, m["days_in_year"])
    result = prepare.compute_metrics(selected, m["operating_revenue_includes_other_income"], m["days_in_year"])[OUTPUT]

    ingest.write_duckdb(ROOT / data["db_path"], {"metrics": result})
    report_dir = ROOT / data["report_dir"]
    result.to_csv(report_dir / "phase2_metrics.csv", index=False)
    (report_dir / "phase2_summary.md").write_text(summary(result), encoding="utf-8")
    print(f"{len(hospitals)} reports -> {len(result)} hospitals in scope. Wrote table 'metrics', "
          "reports/phase2_metrics.csv and reports/phase2_summary.md")


if __name__ == "__main__":
    main()
