"""Pull fields the CMS public-use file lacks from raw HCRIS (Form CMS-2552-10).

Raw HCRIS is three header-less CSVs per fiscal year:
  *_rpt.csv   one row per cost report (record number, CCN, period, status)
  *_nmrc.csv  one row per numeric cell (record number, worksheet, line, column, value)
  *_alpha.csv one row per text cell
Line and column codes are 5 digits: line "01400" is line 14, "01401" is subline 14.01;
column "00100" is column 1.
"""

import zipfile
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd


@dataclass(frozen=True)
class Cell:
    """A set of worksheet cells that are summed into one field.

    lines: 3-digit line prefixes, so sublines are included ("014" matches 14 and 14.01).
    cols: full 5-digit column codes.
    sign: -1 flips contra-asset lines (reported negative) to a positive number.
    """

    worksheet: str
    lines: tuple[str, ...]
    cols: tuple[str, ...]
    sign: int = 1


_G_FUNDS = ("00100", "00200", "00300", "00400")  # general, specific purpose, endowment, plant

# New fields. Line labels were confirmed against the HCRIS alpha file ("11300INTEREST EXPENSE")
# and the fixed-asset roll-up (gross lines + these contra lines = G line 30).
FIELDS: dict[str, Cell] = {
    # Worksheet G, "accumulated depreciation" line under each depreciable asset class.
    "accumulated_depreciation": Cell(
        "G000000", ("014", "016", "018", "020", "022", "024", "026", "028"), _G_FUNDS, sign=-1),
    # Interest as booked in the trial balance, on the dedicated interest cost centre.
    "interest_ws_a": Cell("A000000", ("113",), ("00200",)),
    # Capital-related interest booked directly in the capital cost centres (A-7 Part II).
    "interest_a7_booked": Cell("A700002", ("003",), ("01100",)),
    # Capital-related interest after reclassifications and Medicare adjustments (A-7 Part III).
    "interest_a7_allowable": Cell("A700003", ("003",), ("01100",)),
}

# Cells that ALSO exist in the public-use file, at the locations its data dictionary gives.
# Two uses: (1) same-version reports must agree exactly, which proves the parsing;
# (2) when HCRIS holds a newer version of a report, these values replace the public file's.
CHECKS: dict[str, Cell] = {
    "cash": Cell("G000000", ("001",), _G_FUNDS),
    "temp_investments": Cell("G000000", ("002",), _G_FUNDS),
    "total_fixed_assets": Cell("G000000", ("030",), _G_FUNDS),
    "total_assets": Cell("G000000", ("036",), _G_FUNDS),
    "notes_loans_short_term": Cell("G000000", ("040",), _G_FUNDS),
    "mortgage_payable": Cell("G000000", ("046",), _G_FUNDS),
    "notes_payable": Cell("G000000", ("047",), _G_FUNDS),
    "unsecured_loans": Cell("G000000", ("048",), _G_FUNDS),
    "other_lt_liabilities": Cell("G000000", ("049",), _G_FUNDS),
    "total_lt_liabilities": Cell("G000000", ("050",), _G_FUNDS),
    "total_fund_balances": Cell("G000000", ("059",), _G_FUNDS),
    "total_patient_revenue": Cell("G300000", ("001",), ("00100",)),
    "net_patient_revenue": Cell("G300000", ("003",), ("00100",)),
    "operating_expense": Cell("G300000", ("004",), ("00100",)),
    "other_income": Cell("G300000", ("025",), ("00100",)),
    "other_expenses": Cell("G300000", ("028",), ("00100",)),
    "net_income": Cell("G300000", ("029",), ("00100",)),
    "depreciation": Cell("A700003", ("003",), ("00900",)),
    "salaries": Cell("A000000", ("200",), ("00100",)),
    "days_medicare": Cell("S300001", ("014",), ("00600",)),
    "days_medicaid": Cell("S300001", ("014",), ("00700",)),
    "days_total": Cell("S300001", ("014",), ("00800",)),
    "medicaid_net_revenue": Cell("S100001", ("002",), ("00100",)),
}

# Gross fixed-asset lines on Worksheet G (land through non-depreciable minor equipment).
GROSS_FIXED = Cell(
    "G000000", ("012", "013", "015", "017", "019", "021", "023", "025", "027", "029"), _G_FUNDS)

RPT_COLUMNS = {0: "hcris_rpt_rec_num", 2: "ccn", 4: "hcris_status", 5: "fy_begin", 6: "fy_end"}


def unzip(zip_path: Path) -> Path:
    """Extract a HCRIS zip next to itself (skipped if already done). Returns the folder."""
    with zipfile.ZipFile(zip_path) as zf:
        if not all((zip_path.parent / n).exists() for n in zf.namelist()):
            zf.extractall(zip_path.parent)
    return zip_path.parent


def read_rpt(path: Path) -> pd.DataFrame:
    """Read the report index: record number, CCN, status code and reporting period."""
    raw = pd.read_csv(path, header=None, dtype=str)
    out = raw[list(RPT_COLUMNS)].rename(columns=RPT_COLUMNS)
    for col in ("fy_begin", "fy_end"):
        out[col] = pd.to_datetime(out[col], format="%m/%d/%Y")
    return out


def match_reports(hospitals: pd.DataFrame, rpt: pd.DataFrame) -> pd.DataFrame:
    """Attach the HCRIS record for the same CCN and reporting period.

    The public-use file and HCRIS are different snapshots, so the record number can
    differ when a report was amended or settled in between. `hcris_same_version`
    says whether the record numbers agree.
    """
    out = hospitals.merge(rpt, on=["ccn", "fy_begin", "fy_end"], how="left", validate="one_to_one")
    out["hcris_matched"] = out["hcris_rpt_rec_num"].notna()
    out["hcris_same_version"] = out["hcris_rpt_rec_num"] == out["rpt_rec_num"]
    return out


def read_cells(nmrc_path: Path, rpt_nums: list[str], worksheets: list[str]) -> pd.DataFrame:
    """Return every numeric cell on the given worksheets for the given reports (long format)."""
    con = duckdb.connect()
    con.register("wanted", pd.DataFrame({"rpt": rpt_nums}))
    con.register("sheets", pd.DataFrame({"ws": worksheets}))
    schema = "{'rpt':'VARCHAR','ws':'VARCHAR','line':'VARCHAR','col':'VARCHAR','val':'DOUBLE'}"
    return con.execute(
        f"SELECT n.* FROM read_csv(?, header=false, columns={schema}) n "
        "JOIN wanted USING (rpt) JOIN sheets USING (ws)",
        [str(nmrc_path)],
    ).df()


def sum_cell(cells: pd.DataFrame, spec: Cell) -> pd.Series:
    """Sum the cells a spec describes, per report. Reports with no such cells are absent."""
    mask = (
        (cells["ws"] == spec.worksheet)
        & cells["line"].str[:3].isin(spec.lines)
        & cells["col"].isin(spec.cols)
    )
    return spec.sign * cells[mask].groupby("rpt")["val"].sum()


def build_fields(cells: pd.DataFrame, specs: dict[str, Cell], prefix: str = "") -> pd.DataFrame:
    """One row per report, one column per spec. Missing stays missing (never zero-filled)."""
    wide = pd.DataFrame({prefix + name: sum_cell(cells, spec) for name, spec in specs.items()})
    return wide.rename_axis("hcris_rpt_rec_num").reset_index()


def apply_newer_version(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Where HCRIS holds a different version of a report, take shared fields from HCRIS.

    Keeps every input consistent with the version that interest and accumulated
    depreciation were read from. The public-file value is kept in `<field>_public`.
    """
    out = df.copy()
    newer = out["hcris_matched"] & ~out["hcris_same_version"]
    for field in fields:
        out[f"{field}_public"] = out[field]
        out.loc[newer, field] = out.loc[newer, f"hcris_{field}"]
    out["values_from_hcris"] = newer
    return out


def worksheets_needed() -> list[str]:
    """Distinct worksheet codes used by any spec."""
    return sorted({c.worksheet for c in [*FIELDS.values(), *CHECKS.values(), GROSS_FIXED]})
