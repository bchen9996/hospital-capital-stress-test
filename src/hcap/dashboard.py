"""Phase 5 helpers: everything the dashboard computes, kept free of Streamlit so it can be tested."""

import pandas as pd

from hcap import matcher, stress
from hcap.stress import Scenario

DISCLAIMER = (
    "Screening and educational tool only. Not financial, investment, or municipal advisory advice. "
    "Based on public data that may be 1–2 years old."
)

# Diverging scale: red = negative headroom, blue = positive, grey = cannot assess.
BAND_COLORS = ["#b3261e", "#eb9a93", "#7fb0ea", "#1c5cab"]
NO_DATA_COLOR = "#8c8c88"

SCENARIO_LABELS = {
    "baseline": "Baseline", "medicaid_cut": "Medicaid cut", "volume_drop": "Volume drop",
    "labor_shock": "Labor shock", "combined": "Combined",
}


def build_scenarios(medicaid_cut: float, volume_drop: float, labor_increase: float) -> dict[str, Scenario]:
    """The four scenarios for a given set of shock sizes."""
    return {
        "medicaid_cut": Scenario(medicaid_cut=medicaid_cut),
        "volume_drop": Scenario(volume_drop=volume_drop),
        "labor_shock": Scenario(labor_increase=labor_increase),
        "combined": Scenario(medicaid_cut=medicaid_cut, volume_drop=volume_drop, labor_increase=labor_increase),
    }


def recompute(
    base: pd.DataFrame,
    scenarios: dict[str, Scenario],
    target_dscr: float,
    variable_cost_share: float,
    capital_types: dict[str, dict],
    ladder_cfg: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rerun the stress test and the capital matcher. Returns (hospitals, per-rung details)."""
    stressed = stress.run(base, scenarios, target_dscr, variable_cost_share, capital_types)
    hospitals, details = matcher.run(stressed, ladder_cfg)
    hospitals["headroom_stressed_margin"] = hospitals["headroom_stressed"] / hospitals["net_patient_revenue"].where(
        hospitals["net_patient_revenue"] > 0)
    hospitals["label"] = hospitals["hospital_name"].str.title() + " (" + hospitals["ccn"] + ")"
    return hospitals, details


def band_labels(bands: list[float]) -> list[str]:
    """Legend text for each colour band, lowest first."""
    low, mid, high = bands
    return [f"below {low:.0%}", f"{low:.0%} to {mid:.0%}", f"{mid:.0%} to {high:.0%}", f"above {high:.0%}"]


def band_color(margin: float | None, bands: list[float]) -> str:
    """Map colour for a stressed-headroom margin. Grey when it cannot be assessed."""
    if margin is None or pd.isna(margin):
        return NO_DATA_COLOR
    return BAND_COLORS[sum(margin >= edge for edge in bands)]


def nearest_label(hospitals: pd.DataFrame, click: dict | None) -> str | None:
    """Label of the hospital whose dot was clicked (the map reports the dot's coordinates)."""
    if not click or click.get("lat") is None:
        return None
    located = hospitals[hospitals["latitude"].notna()]
    distance = (located["latitude"] - click["lat"]) ** 2 + (located["longitude"] - click["lng"]) ** 2
    return located.loc[distance.idxmin(), "label"]


def fmt_money(value: float | None) -> str:
    """Dollar amount, or 'n/a' when missing."""
    return "n/a" if value is None or pd.isna(value) else matcher.money(value)


def fmt_pct(value: float | None) -> str:
    return "n/a" if value is None or pd.isna(value) else f"{value:.1%}"


def fmt_number(value: float | None, suffix: str = "") -> str:
    return "n/a" if value is None or pd.isna(value) else f"{value:,.1f}{suffix}"


def scenario_table(row: pd.Series) -> pd.DataFrame:
    """One hospital's EBIDA and headroom under each scenario."""
    names = [n for n in SCENARIO_LABELS if n == "baseline" or f"headroom_{n}" in row.index]
    return pd.DataFrame({
        "Scenario": [SCENARIO_LABELS[n] for n in names],
        "EBIDA": [fmt_money(row["ebida"] if n == "baseline" else row[f"ebida_{n}"]) for n in names],
        "Headroom": [fmt_money(row[f"headroom_{n}"]) for n in names],
    })


def principal_table(row: pd.Series, capital_types: dict[str, dict]) -> pd.DataFrame:
    """Loan size each capital type's placeholder rate and term would support at stressed headroom."""
    return pd.DataFrame({
        "Capital type": [t["label"] for t in capital_types.values()],
        "Rate (placeholder)": [f"{t['annual_rate']:.2%}" for t in capital_types.values()],
        "Term (placeholder)": [f"{t['term_years']} years" for t in capital_types.values()],
        "Affordable principal": [fmt_money(row[f"principal_{k}"]) for k in capital_types],
    })


TABLE_COLUMNS = {
    "hospital_name": "Hospital", "town_name": "Town", "ccn_facility_type": "Type", "beds": "Beds",
    "star_rating": "Stars", "operating_margin": "Operating margin", "days_cash_on_hand": "Days cash",
    "avg_age_of_plant": "Age of plant (yrs)", "debt_to_capitalization": "Debt / capitalization",
    "medicaid_share_days": "Medicaid share of days", "medicare_share_days": "Medicare share of days",
    "ebida": "EBIDA ($)", "existing_debt_service": "Existing debt service ($)",
    "headroom_baseline": "Baseline headroom ($)", "headroom_stressed": "Stressed headroom ($)",
    "headroom_stressed_margin": "Stressed headroom / revenue", "primary_label": "Primary match",
    "alternates": "Alternates", "flags": "Data caveats", "ccn": "CCN",
}


def export_table(hospitals: pd.DataFrame) -> pd.DataFrame:
    """The sortable table: one row per hospital with readable column names."""
    return hospitals[list(TABLE_COLUMNS)].rename(columns=TABLE_COLUMNS)
