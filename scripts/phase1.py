"""Run Phase 1: ingest, filter, join, store, and write the data quality report.

Usage:  python scripts/phase1.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hcap import hcris, ingest, quality  # noqa: E402
from hcap.config import load_config  # noqa: E402


def add_hcris(hospitals: pd.DataFrame, url: str, year: int, raw_dir: Path) -> pd.DataFrame:
    """Download raw HCRIS, match each report by CCN + period, and attach the extra fields."""
    folder = hcris.unzip(ingest.download(url, raw_dir / "hcris" / f"HOSP10FY{year}.ZIP"))
    out = hcris.match_reports(hospitals, hcris.read_rpt(folder / f"HOSP10_{year}_rpt.csv"))
    cells = hcris.read_cells(
        folder / f"HOSP10_{year}_nmrc.csv",
        out["hcris_rpt_rec_num"].dropna().tolist(),
        hcris.worksheets_needed(),
    )
    checks = {**hcris.CHECKS, "gross_fixed_assets": hcris.GROSS_FIXED}
    out = out.merge(hcris.build_fields(cells, hcris.FIELDS), on="hcris_rpt_rec_num", how="left")
    return out.merge(hcris.build_fields(cells, checks, prefix="hcris_"), on="hcris_rpt_rec_num", how="left")


def section(title: str, frame: pd.DataFrame, note: str = "") -> str:
    """Render one report section as markdown."""
    body = frame.to_markdown(index=False) if len(frame) else "_None found._"
    return f"## {title} ({len(frame)})\n\n{note}\n\n{body}\n"


def main() -> None:
    cfg = load_config()
    data, q, state = cfg["data"], cfg["quality"], cfg["state"]
    raw_dir = ROOT / data["raw_dir"]
    year = data["cost_report_year"]

    cost_raw = ingest.read_raw_csv(ingest.download(data["cost_report_url"], raw_dir / f"CostReport_{year}_Final.csv"))
    hgi_raw = ingest.read_raw_csv(ingest.download(data["hgi_url"], raw_dir / "Hospital_General_Information.csv"))

    print(f"Cost report {year}: {cost_raw.shape[0]} rows x {cost_raw.shape[1]} columns. Actual column names:")
    for i, name in enumerate(cost_raw.columns, 1):
        print(f"  {i:>3}. {name}")

    cost = ingest.tidy_cost_report(cost_raw)
    cost = cost[cost["state"] == state]
    cost = ingest.add_period_fields(cost, q["full_year_min_days"], q["full_year_max_days"])
    hospitals = ingest.join_hgi(cost, ingest.tidy_hgi(hgi_raw))
    hospitals = add_hcris(hospitals, data["hcris_url"], year, raw_dir)

    ingest.write_duckdb(ROOT / data["db_path"], {
        "cost_report_raw": cost_raw,
        "hgi_raw": hgi_raw,
        "hospitals": hospitals,
    })

    report = "\n".join([
        f"# Phase 1 data quality report: {state}, cost report file {year}\n",
        f"{len(hospitals)} cost reports for {hospitals['ccn'].nunique()} hospitals (CCNs). "
        f"{int(hospitals['hgi_matched'].sum())} matched to Hospital General Information; "
        f"{int(hospitals['hcris_matched'].sum())} matched to raw HCRIS, of which "
        f"{int(hospitals['hcris_same_version'].sum())} are the same version of the report.\n",
        section("Raw HCRIS: fields added", quality.missing_summary(hospitals, quality.HCRIS_FIELDS),
                "Three candidate interest measures are pulled; none has been chosen yet. "
                "A blank means the hospital reported nothing in that cell."),
        section("Raw HCRIS: agreement with the public file on shared cells",
                quality.hcris_agreement(hospitals, list(hcris.CHECKS)),
                "Same-version rows prove the parsing. Different-version rows show how much a report "
                "changed between the two CMS snapshots."),
        section("Raw HCRIS: fixed-asset roll-up failures", quality.fixed_asset_rollup(hospitals),
                "Gross fixed assets minus accumulated depreciation should equal Worksheet G line 30."),
        section("Raw HCRIS: no matching record", quality.unmatched_hcris(hospitals)),
        section("Missing values in Phase 2 fields", quality.missing_summary(hospitals, quality.PHASE2_FIELDS),
                "Blank cells are left blank. A blank may mean zero or may mean not reported; the file does not say which."),
        section("Negative values where none should exist",
                quality.negative_values(hospitals, [*quality.NON_NEGATIVE_FIELDS, *quality.HCRIS_FIELDS])),
        section("Failed consistency checks", quality.impossible_values(hospitals, q["balance_tolerance_dollars"])),
        section("Partial-year or odd-length reports", quality.partial_year(hospitals),
                f"Outside {q['full_year_min_days']}-{q['full_year_max_days']} days."),
        section("Hospitals with more than one report", quality.duplicate_ccn(hospitals)),
        section("No match in Hospital General Information", quality.unmatched_hgi(hospitals),
                "These have no hospital type, star rating, or Care Compare address."),
    ])
    out = ROOT / data["report_dir"] / "phase1_data_quality.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"\nWrote {out.relative_to(ROOT)} and {data['db_path']}")


if __name__ == "__main__":
    main()
