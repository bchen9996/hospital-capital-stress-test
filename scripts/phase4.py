"""Run Phase 4: locate each hospital and match it to the capital ladder.

Usage:  python scripts/phase4.py      (run phase1.py, phase2.py and phase3.py first)

Sends hospital street addresses to the U.S. Census Bureau geocoder the first time it
runs; results are cached in data/geo_cache.csv.
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hcap import geo, ingest, matcher  # noqa: E402
from hcap.config import load_config  # noqa: E402


def summary(matches: pd.DataFrame) -> str:
    """Markdown summary: how many hospitals land on each rung, and location coverage."""
    order = [*matcher.LADDER.values(), matcher.CANNOT_ASSESS_LABEL]
    primary = matches["primary_label"].value_counts().reindex(order, fill_value=0)
    alternates = matches["alternates"].str.split(" | ", regex=False).explode()
    alt = alternates[alternates != ""].value_counts().reindex(order, fill_value=0)
    table = pd.DataFrame({"primary match": primary, "listed as alternate": alt}).rename_axis("rung").reset_index()
    location = pd.DataFrame([
        {"fact": "address geocoded (coordinates and census tract known)", "hospitals": int(matches["geocoded"].sum())},
        {"fact": "in an NMTC low-income tract", "hospitals": int((matches["nmtc_eligible"] == True).sum())},  # noqa: E712
        {"fact": "town population from the geocoded address", "hospitals": int((matches["town_source"] == "geocoded address").sum())},
        {"fact": "town population from the mailing city name", "hospitals": int((matches["town_source"] == "mailing city name").sum())},
        {"fact": "town population unknown", "hospitals": int((matches["town_source"] == "unknown").sum())},
    ])
    return "\n\n".join([
        f"# Phase 4 capital match summary\n\n{len(matches)} hospitals. Thresholds are screening PLACEHOLDERS "
        "from config.yaml, not official program requirements.",
        "## Matches by rung\n\n" + table.to_markdown(index=False),
        "## Location data coverage\n\n" + location.to_markdown(index=False),
    ])


def main() -> None:
    cfg = load_config()
    data, loc = cfg["data"], cfg["location"]
    geo_dir = ROOT / data["raw_dir"] / "geo"
    with duckdb.connect(str(ROOT / data["db_path"]), read_only=True) as con:
        stress = con.execute("SELECT * FROM stress").df()
        address = con.execute(
            "SELECT h.ccn, h.hgi_address, h.hgi_city, h.hgi_zip, h.street, h.city, h.zip "
            "FROM hospitals h JOIN stress s ON s.ccn = h.ccn AND s.fy_end = h.fy_end").df()

    geocoded = geo.geocode_hospitals(address, ROOT / loc["geocode_cache"])
    towns = geo.load_town_population(
        ingest.download(loc["town_population_url"], geo_dir / "town_population.csv"), loc["town_population_column"])
    nmtc = geo.load_nmtc_tracts(ingest.download(loc["nmtc_tracts_url"], geo_dir / "nmtc_tracts.xlsx"))
    located = geo.attach_location(address, geocoded, towns, nmtc)
    keep = ["ccn", "latitude", "longitude", "geocoded", "tract_geoid", "nmtc_eligible",
            "town_name", "town_population", "town_source"]

    matches, details = matcher.run(stress.merge(located[keep], on="ccn"), cfg["capital_ladder"])

    ingest.write_duckdb(ROOT / data["db_path"], {"matches": matches, "match_details": details})
    report_dir = ROOT / data["report_dir"]
    matches.to_csv(report_dir / "phase4_matches.csv", index=False)
    details.to_csv(report_dir / "phase4_match_details.csv", index=False)
    (report_dir / "phase4_summary.md").write_text(summary(matches), encoding="utf-8")
    print("Wrote tables 'matches' and 'match_details', reports/phase4_matches.csv, "
          "phase4_match_details.csv and phase4_summary.md")


if __name__ == "__main__":
    main()
