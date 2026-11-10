"""Phase 1: download CMS files, filter to one state, join hospital info, store in DuckDB."""

from pathlib import Path

import duckdb
import pandas as pd
import requests

from hcap import columns


def download(url: str, dest: Path, force: bool = False) -> Path:
    """Download `url` to `dest` unless it already exists. Returns `dest`."""
    if dest.exists() and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=120, stream=True) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    return dest


def read_raw_csv(path: Path) -> pd.DataFrame:
    """Read a CMS CSV with every column as text, so CCNs and ZIPs keep leading zeros."""
    return pd.read_csv(path, dtype=str, encoding_errors="replace")


def check_columns(df: pd.DataFrame, expected: list[str], source: str) -> None:
    """Raise if any expected column name is absent from the file."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise KeyError(f"{source}: expected columns not found: {missing}")


def normalize_ccn(ccn: pd.Series) -> pd.Series:
    """CMS Certification Number as a 6-character, zero-padded string."""
    return ccn.astype(str).str.strip().str.zfill(6)


def tidy_cost_report(raw: pd.DataFrame) -> pd.DataFrame:
    """Select the verified columns, rename to internal names, and set types.

    Blank cells stay missing (NaN). Nothing is filled or imputed here.
    """
    text, num = columns.COST_REPORT_TEXT, columns.COST_REPORT_NUMERIC
    check_columns(raw, [*text.values(), *num.values()], "cost report")
    out = raw[list(text.values())].rename(columns={v: k for k, v in text.items()})
    for name, source in num.items():
        out[name] = pd.to_numeric(raw[source], errors="coerce")
    out["ccn"] = normalize_ccn(out["ccn"])
    for col in ("fy_begin", "fy_end"):
        out[col] = pd.to_datetime(out[col], format="%m/%d/%Y", errors="coerce")
    return out


def add_period_fields(df: pd.DataFrame, min_days: int, max_days: int) -> pd.DataFrame:
    """Add reporting-period length, a partial-year flag, and duplicate-CCN markers."""
    out = df.copy()
    out["period_days"] = (out["fy_end"] - out["fy_begin"]).dt.days + 1
    out["is_full_year"] = out["period_days"].between(min_days, max_days)
    out["reports_for_ccn"] = out.groupby("ccn")["ccn"].transform("size")
    out["is_latest_for_ccn"] = out["fy_end"] == out.groupby("ccn")["fy_end"].transform("max")
    return out


def tidy_hgi(raw: pd.DataFrame) -> pd.DataFrame:
    """Select and rename Hospital General Information columns; star rating becomes numeric."""
    check_columns(raw, list(columns.HGI.values()), "hospital general information")
    out = raw[list(columns.HGI.values())].rename(columns={v: k for k, v in columns.HGI.items()})
    out["ccn"] = normalize_ccn(out["ccn"])
    # "Not Available" becomes missing rather than a number.
    out["star_rating"] = pd.to_numeric(out["star_rating"], errors="coerce")
    return out


def join_hgi(cost: pd.DataFrame, hgi: pd.DataFrame) -> pd.DataFrame:
    """Left-join hospital info onto cost reports by CCN; `hgi_matched` marks hits."""
    out = cost.merge(hgi, on="ccn", how="left", validate="many_to_one", indicator=True)
    out["hgi_matched"] = out.pop("_merge") == "both"
    return out


def write_duckdb(db_path: Path, tables: dict[str, pd.DataFrame]) -> None:
    """Replace each named table in the DuckDB file with the given frame."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        for name, frame in tables.items():
            con.register("_frame", frame)
            con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _frame')
            con.unregister("_frame")
