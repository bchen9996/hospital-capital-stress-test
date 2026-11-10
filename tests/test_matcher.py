"""Capital ladder rules, tested rung by rung on hand-built hospitals."""

import pandas as pd
import pytest

from hcap import geo, matcher

CFG = {
    "usda": {"max_town_population": 20000},
    "hud_bank": {"min_baseline_headroom_margin": 0.02},
    "bonds": {"min_stressed_headroom_margin": 0.03, "min_net_patient_revenue": 75_000_000},
    "sale_leaseback": {"rent_yield_on_fixed_assets": 0.075, "min_combined_rent_coverage": 2.0, "can_be_primary": False},
}


def hospital(**overrides: object) -> dict:
    """A strong, large, urban hospital outside any low-income tract; tests override what they need."""
    base = {
        "ccn": "000001", "flags": "",
        "headroom_baseline": 10e6, "headroom_stressed": 5e6, "binding_scenario": "combined",
        "net_patient_revenue": 100e6, "ebida_combined": 8e6, "existing_debt_service": 1e6,
        "total_fixed_assets": 40e6,  # rent = 7.5% x 40M = 3M ; coverage = 8 / (1 + 3) = 2.0
        "town_population": 150_000, "town_name": "Bigtown", "town_source": "geocoded address",
        "nmtc_eligible": False, "tract_geoid": "29000000100",
    }
    return {**base, **overrides}


def test_negative_baseline_goes_to_grants_only() -> None:
    out = matcher.match_hospital(hospital(headroom_baseline=-2e6, headroom_stressed=-6e6, ebida_combined=-1e6,
                                          town_population=3000, nmtc_eligible=True), CFG)
    assert out["primary"] == "grants_affiliation"
    assert out["alternates"] == []  # rural and low-income tract do not help: it cannot carry a loan
    assert "-$2.0M" in out["primary_reason"]


def test_thin_rural_hospital_gets_usda() -> None:
    # baseline 0.5M on 100M revenue = 0.5% (thin), negative under stress, town of 4,000
    out = matcher.match_hospital(hospital(headroom_baseline=0.5e6, headroom_stressed=-1e6, ebida_combined=0,
                                          town_population=4000), CFG)
    assert out["primary"] == "usda" and out["alternates"] == []


def test_town_over_limit_fails_usda() -> None:
    assert matcher.usda(hospital(town_population=20001), CFG["usda"]).qualifies is False
    assert matcher.usda(hospital(town_population=20000), CFG["usda"]).qualifies is True


def test_low_income_tract_gets_cdfi_and_unknown_tract_is_unknown() -> None:
    assert matcher.cdfi_nmtc(hospital(nmtc_eligible=True)).qualifies is True
    assert matcher.cdfi_nmtc(hospital(nmtc_eligible=False)).qualifies is False
    assert matcher.cdfi_nmtc(hospital(nmtc_eligible=None)).qualifies is None


def test_hud_bank_needs_moderate_baseline_and_positive_stress() -> None:
    cfg = CFG["hud_bank"]
    assert matcher.hud_bank(hospital(headroom_baseline=2e6, headroom_stressed=1), cfg).qualifies is True  # 2.0%
    assert matcher.hud_bank(hospital(headroom_baseline=1.9e6), cfg).qualifies is False  # 1.9% is thin
    assert matcher.hud_bank(hospital(headroom_stressed=-1), cfg).qualifies is False  # turns negative


def test_bonds_need_solid_stressed_headroom_and_scale() -> None:
    cfg = CFG["bonds"]
    assert matcher.bonds(hospital(), cfg).qualifies is True  # 5% stressed margin, 100M revenue
    assert matcher.bonds(hospital(headroom_stressed=2.9e6), cfg).qualifies is False  # 2.9% < 3%
    # 5% margin but only 50M revenue
    assert matcher.bonds(hospital(net_patient_revenue=50e6, headroom_stressed=2.5e6), cfg).qualifies is False


def test_rent_coverage_formula() -> None:
    # 8M / (1M existing + 7.5% x 40M = 3M rent) = 2.0
    assert matcher.rent_coverage(hospital(), 0.075) == pytest.approx(2.0)
    assert matcher.rent_coverage(hospital(total_fixed_assets=0), 0.075) is None


def test_sale_leaseback_is_alternate_only_and_always_warns() -> None:
    df = pd.DataFrame([hospital()])
    matches, details = matcher.run(df, CFG)
    row = matches.iloc[0]
    assert row["primary_match"] == "bonds"
    assert row["alternates"].split(" | ") == [matcher.LADDER["sale_leaseback"], matcher.LADDER["hud_bank"]]
    assert row["sale_leaseback_warning"].startswith("WARNING")
    slb = details[details["rung"] == "sale_leaseback"].iloc[0]
    assert slb["warning"].startswith("WARNING")


def test_sale_leaseback_below_threshold_is_not_offered() -> None:
    out = matcher.match_hospital(hospital(ebida_combined=7.9e6), CFG)  # coverage 1.98
    assert "sale_leaseback" not in out["alternates"]


def test_positive_but_nothing_qualifies_falls_back_to_grants() -> None:
    # thin, urban, not low-income, negative under stress
    out = matcher.match_hospital(hospital(headroom_baseline=0.5e6, headroom_stressed=-1e6, ebida_combined=0), CFG)
    assert out["primary"] == "grants_affiliation"
    assert "meets no debt rung" in out["primary_reason"]


def test_missing_headroom_cannot_be_assessed() -> None:
    out = matcher.match_hospital(hospital(headroom_baseline=float("nan"), flags="interest negative, unusable"), CFG)
    assert out["primary"] == matcher.CANNOT_ASSESS and out["alternates"] == []
    assert "interest negative" in out["primary_reason"]


def test_money_format() -> None:
    assert matcher.money(3_200_000) == "$3.2M" and matcher.money(-450_000) == "-$450K"


def test_clean_street_and_town_names() -> None:
    assert geo.clean_street("26136 US Highway 59, PO Box 107") == "26136 US HIGHWAY 59"
    assert geo.clean_street("One Hospital Drive") == "1 HOSPITAL DRIVE"
    assert geo.normalize_town("Jefferson City city", census_name=True) == "JEFFERSON CITY"
    assert geo.normalize_town("JEFFERSON CITY") == "JEFFERSON CITY"
    assert geo.normalize_town("Ste. Genevieve city", census_name=True) == geo.normalize_town("SAINTE GENEVIEVE")
    assert geo.normalize_town("St. Louis city", census_name=True) == geo.normalize_town("SAINT LOUIS")


def test_parse_geocoder_response() -> None:
    payload = {"result": {"addressMatches": [{
        "coordinates": {"x": -92.3, "y": 38.9},
        "geographies": {"Census Tracts": [{"GEOID": "29019001100"}],
                        "Incorporated Places": [{"GEOID": "2915670", "NAME": "Columbia city"}]},
    }]}}
    out = geo.parse_geocoder_response(payload)
    assert out == {"latitude": 38.9, "longitude": -92.3, "tract_geoid": "29019001100",
                   "place_geoid": "2915670", "place_name": "Columbia city"}
    assert geo.parse_geocoder_response({"result": {"addressMatches": []}}) is None
