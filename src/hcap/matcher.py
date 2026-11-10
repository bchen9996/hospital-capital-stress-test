"""Phase 4: rules-based capital ladder. No machine learning; every rule is readable below.

Each rung has one function that looks at a hospital and returns a Verdict: does it
qualify (yes / no / unknown), and a plain-English reason. Thresholds come from
config.yaml and are screening PLACEHOLDERS, not official program requirements.
"""

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

# The ladder, from least to most financial strength required.
LADDER: dict[str, str] = {
    "grants_affiliation": "Grants / affiliation / Rural Emergency Hospital conversion",
    "usda": "USDA Community Facilities loan",
    "cdfi_nmtc": "CDFI / New Markets Tax Credits",
    "hud_bank": "HUD Section 242 / bank loan",
    "bonds": "Tax-exempt municipal bonds",
    "sale_leaseback": "Sale-leaseback / REIT capital",
}
CANNOT_ASSESS = "cannot_assess"
CANNOT_ASSESS_LABEL = "Cannot assess"

SALE_LEASEBACK_WARNING = (
    "WARNING: a sale-leaseback gives up ownership of the buildings in exchange for a long lease "
    "whose rent usually rises every year and must be paid whatever happens to patient volume. "
    "Hospitals have been pushed into distress by leases like this. Treat it as a last resort "
    "and get independent advice."
)

Row = Mapping[str, Any]


@dataclass(frozen=True)
class Verdict:
    """Result of testing one hospital against one rung. `qualifies` is None when unknown."""

    rung: str
    qualifies: bool | None
    reason: str


def money(value: float) -> str:
    """Dollars as a short string: $3.2M, -$450K."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    return f"{sign}${value / 1e6:.1f}M" if value >= 1e6 else f"{sign}${value / 1e3:.0f}K"


def margin(headroom: float, revenue: float) -> float:
    """Headroom as a share of net patient revenue (0 if revenue is not positive)."""
    return headroom / revenue if revenue and revenue > 0 else 0.0


def grants_affiliation(row: Row) -> Verdict:
    """Rung 1: negative baseline headroom."""
    base = row["headroom_baseline"]
    if base < 0:
        return Verdict("grants_affiliation", True,
                       f"Baseline headroom is {money(base)} a year: cash flow does not cover existing "
                       "payments with the required cushion, so new debt is not supportable.")
    return Verdict("grants_affiliation", False,
                   f"Baseline headroom is positive ({money(base)} a year), so it is not limited to non-debt options.")


def usda(row: Row, cfg: dict) -> Verdict:
    """Rung 2: non-negative baseline headroom AND a town at or under the population limit."""
    base, pop, limit = row["headroom_baseline"], row["town_population"], cfg["max_town_population"]
    if base < 0:
        return Verdict("usda", False, f"Baseline headroom is negative ({money(base)} a year); it cannot carry a loan.")
    if pd.isna(pop):
        return Verdict("usda", None, "Town population could not be determined, so rural status is unknown.")
    where = f"{row['town_name']} (population {pop:,.0f}, from {row['town_source']})"
    if pop <= limit:
        return Verdict("usda", True,
                       f"Baseline headroom is positive ({money(base)} a year) and it is in {where}, "
                       f"within this tool's {limit:,} screening limit for a rural town.")
    return Verdict("usda", False, f"It is in {where}, above this tool's {limit:,} screening limit for a rural town.")


def cdfi_nmtc(row: Row) -> Verdict:
    """Rung 3: located in an NMTC-eligible low-income census tract, with non-negative baseline headroom."""
    base, eligible = row["headroom_baseline"], row["nmtc_eligible"]
    if base < 0:
        return Verdict("cdfi_nmtc", False, f"Baseline headroom is negative ({money(base)} a year); it cannot carry a loan.")
    if pd.isna(eligible):
        return Verdict("cdfi_nmtc", None, "The address could not be geocoded, so its census tract is unknown.")
    tract = row["tract_geoid"]
    if eligible:
        return Verdict("cdfi_nmtc", True,
                       f"Census tract {tract} is on the CDFI Fund's list of NMTC low-income communities.")
    return Verdict("cdfi_nmtc", False, f"Census tract {tract} is not on the CDFI Fund's list of NMTC low-income communities.")


def hud_bank(row: Row, cfg: dict) -> Verdict:
    """Rung 4: moderate baseline headroom that stays positive under stress."""
    base, stressed = row["headroom_baseline"], row["headroom_stressed"]
    base_margin, floor = margin(base, row["net_patient_revenue"]), cfg["min_baseline_headroom_margin"]
    if base_margin < floor:
        return Verdict("hud_bank", False,
                       f"Baseline headroom is {base_margin:.1%} of patient revenue, under this tool's "
                       f"{floor:.0%} screening floor for 'moderate'.")
    if stressed <= 0:
        return Verdict("hud_bank", False,
                       f"Headroom falls to {money(stressed)} a year in the {row['binding_scenario']} scenario; "
                       "it does not stay positive under stress.")
    return Verdict("hud_bank", True,
                   f"Baseline headroom is {base_margin:.1%} of patient revenue and stays positive under stress "
                   f"({money(stressed)} a year in the worst scenario).")


def bonds(row: Row, cfg: dict) -> Verdict:
    """Rung 5: solid stressed headroom plus enough scale."""
    stressed, revenue = row["headroom_stressed"], row["net_patient_revenue"]
    stressed_margin = margin(stressed, revenue)
    floor, scale = cfg["min_stressed_headroom_margin"], cfg["min_net_patient_revenue"]
    if stressed_margin < floor:
        return Verdict("bonds", False,
                       f"Stressed headroom is {stressed_margin:.1%} of patient revenue, under this tool's "
                       f"{floor:.0%} screening floor for 'solid'.")
    if revenue < scale:
        return Verdict("bonds", False,
                       f"Net patient revenue is {money(revenue)}, under this tool's {money(scale)} screening floor for scale.")
    return Verdict("bonds", True,
                   f"Stressed headroom is {stressed_margin:.1%} of patient revenue ({money(stressed)} a year) "
                   f"and net patient revenue is {money(revenue)}.")


def rent_coverage(row: Row, rent_yield: float) -> float | None:
    """Combined-scenario EBIDA / (existing debt service + hypothetical rent).

    Hypothetical rent = rent_yield x net book value of fixed assets. None if no fixed assets.
    """
    fixed = row["total_fixed_assets"]
    if pd.isna(fixed) or fixed <= 0:
        return None
    return row["ebida_combined"] / (row["existing_debt_service"] + rent_yield * fixed)


def sale_leaseback(row: Row, cfg: dict) -> Verdict:
    """Rung 6: only if rent coverage stays above a high threshold in the combined stress scenario."""
    coverage, floor = rent_coverage(row, cfg["rent_yield_on_fixed_assets"]), cfg["min_combined_rent_coverage"]
    if coverage is None:
        return Verdict("sale_leaseback", None, "No fixed assets are reported, so a rent figure cannot be estimated.")
    detail = (f"Under the combined stress scenario, cash flow would cover existing payments plus an estimated "
              f"rent {coverage:.1f} times")
    if coverage >= floor:
        return Verdict("sale_leaseback", True, f"{detail}, at or above this tool's {floor:.1f}x screening threshold.")
    return Verdict("sale_leaseback", False, f"{detail}, below this tool's {floor:.1f}x screening threshold.")


def all_verdicts(row: Row, cfg: dict) -> list[Verdict]:
    """Test one hospital against every rung, in ladder order."""
    return [
        grants_affiliation(row), usda(row, cfg["usda"]), cdfi_nmtc(row),
        hud_bank(row, cfg["hud_bank"]), bonds(row, cfg["bonds"]), sale_leaseback(row, cfg["sale_leaseback"]),
    ]


def match_hospital(row: Row, cfg: dict) -> dict[str, Any]:
    """Primary match, alternates and reasons for one hospital.

    Primary = the highest rung it qualifies for (sale-leaseback only if config allows).
    Alternates = every other rung it qualifies for, highest first.
    """
    if pd.isna(row["headroom_baseline"]) or pd.isna(row["headroom_stressed"]):
        reason = ("Headroom could not be calculated because a required input is missing "
                  f"({row.get('flags') or 'see flags'}).")
        return {"primary": CANNOT_ASSESS, "primary_reason": reason, "alternates": [], "verdicts": []}

    verdicts = all_verdicts(row, cfg)
    qualified = [v for v in reversed(verdicts) if v.qualifies]
    can_lead = [v for v in qualified if v.rung != "sale_leaseback" or cfg["sale_leaseback"]["can_be_primary"]]
    if can_lead:
        primary, reason = can_lead[0].rung, can_lead[0].reason
    else:
        primary = "grants_affiliation"
        reason = ("Baseline headroom is positive but it meets no debt rung's screen "
                  "(not rural, not in an eligible tract, and headroom is thin or turns negative under stress).")
    return {
        "primary": primary,
        "primary_reason": reason,
        "alternates": [v.rung for v in qualified if v.rung != primary],
        "verdicts": verdicts,
    }


def run(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Match every hospital. Returns (one row per hospital, one row per hospital x rung)."""
    summaries, details = [], []
    for _, row in df.iterrows():
        result = match_hospital(row, cfg)
        labels = {**LADDER, CANNOT_ASSESS: CANNOT_ASSESS_LABEL}
        offered = [result["primary"], *result["alternates"]]
        summaries.append({
            "ccn": row["ccn"],
            "primary_match": result["primary"],
            "primary_label": labels[result["primary"]],
            "primary_reason": result["primary_reason"],
            "alternates": " | ".join(LADDER[a] for a in result["alternates"]),
            "sale_leaseback_warning": SALE_LEASEBACK_WARNING if "sale_leaseback" in offered else "",
        })
        details += [{
            "ccn": row["ccn"], "rung": v.rung, "label": LADDER[v.rung], "qualifies": v.qualifies,
            "reason": v.reason, "warning": SALE_LEASEBACK_WARNING if v.rung == "sale_leaseback" else "",
        } for v in result["verdicts"]]
    detail_frame = pd.DataFrame(details, columns=["ccn", "rung", "label", "qualifies", "reason", "warning"])
    return df.merge(pd.DataFrame(summaries), on="ccn"), detail_frame
