"""Run Phase 3: headroom, stress scenarios, affordable principal.

Usage:  python scripts/phase3.py      (run phase1.py and phase2.py first)
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hcap import ingest, stress  # noqa: E402
from hcap.config import load_config  # noqa: E402


def summary(result: pd.DataFrame, scenario_names: list[str], capital_types: dict[str, dict]) -> str:
    """Markdown summary of headroom by scenario and principal by capital type."""
    cols = ["headroom_baseline", *[f"headroom_{n}" for n in scenario_names], "headroom_stressed"]
    rows = [{
        "measure": c.removeprefix("headroom_"),
        "hospitals with a value": int(result[c].notna().sum()),
        "negative": int((result[c] < 0).sum()),
        "median ($M)": round(result[c].median() / 1e6, 2),
        "25th pct ($M)": round(result[c].quantile(0.25) / 1e6, 2),
        "75th pct ($M)": round(result[c].quantile(0.75) / 1e6, 2),
    } for c in cols]
    binding = result["binding_scenario"].value_counts().rename_axis("lowest-headroom case").reset_index(name="hospitals")
    positive = result[result["headroom_stressed"] > 0]
    principal = pd.DataFrame([{
        "capital type": t["label"], "rate": t["annual_rate"], "term (years)": t["term_years"],
        "median principal, hospitals with positive stressed headroom ($M)":
            round(positive[f"principal_{k}"].median() / 1e6, 1),
    } for k, t in capital_types.items()])
    return "\n\n".join([
        f"# Phase 3 stress test summary\n\n{len(result)} hospitals in scope; "
        f"{int(result['headroom_stressed'].notna().sum())} have every input needed.",
        "## Headroom (extra annual payment the hospital could carry)\n\n" + pd.DataFrame(rows).to_markdown(index=False),
        "## Which case sets stressed headroom\n\n" + binding.to_markdown(index=False),
        "## Affordable principal at stressed headroom\n\nRates and terms are PLACEHOLDERS from config.yaml, "
        "not official program terms.\n\n" + principal.to_markdown(index=False),
    ])


def main() -> None:
    cfg = load_config()
    data, st = cfg["data"], cfg["stress"]
    scenarios = {name: stress.Scenario(**shocks) for name, shocks in st["scenarios"].items()}
    with duckdb.connect(str(ROOT / data["db_path"]), read_only=True) as con:
        metrics = con.execute("SELECT * FROM metrics").df()

    result = stress.run(metrics, scenarios, st["target_dscr"], st["variable_cost_share"], cfg["capital_types"])

    ingest.write_duckdb(ROOT / data["db_path"], {"stress": result})
    report_dir = ROOT / data["report_dir"]
    result.to_csv(report_dir / "phase3_stress.csv", index=False)
    (report_dir / "phase3_summary.md").write_text(
        summary(result, list(scenarios), cfg["capital_types"]), encoding="utf-8")
    print("Wrote table 'stress', reports/phase3_stress.csv and reports/phase3_summary.md")


if __name__ == "__main__":
    main()
