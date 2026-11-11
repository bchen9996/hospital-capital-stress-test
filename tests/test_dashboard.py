"""Dashboard helpers, plus a smoke test that the whole page renders."""

from pathlib import Path

import pandas as pd
import pytest

from hcap import dashboard as dash
from hcap.config import load_config

ROOT = Path(__file__).resolve().parents[1]
BANDS = [-0.05, 0.0, 0.05]


def test_band_color_picks_the_right_band() -> None:
    assert dash.band_color(-0.10, BANDS) == dash.BAND_COLORS[0]
    assert dash.band_color(-0.01, BANDS) == dash.BAND_COLORS[1]
    assert dash.band_color(0.0, BANDS) == dash.BAND_COLORS[2]  # zero counts as not negative
    assert dash.band_color(0.20, BANDS) == dash.BAND_COLORS[3]
    assert dash.band_color(float("nan"), BANDS) == dash.NO_DATA_COLOR


def test_band_labels() -> None:
    assert dash.band_labels(BANDS) == ["below -5%", "-5% to 0%", "0% to 5%", "above 5%"]


def test_build_scenarios_combined_carries_all_three_shocks() -> None:
    combined = dash.build_scenarios(0.1, 0.2, 0.05)["combined"]
    assert (combined.medicaid_cut, combined.volume_drop, combined.labor_increase) == (0.1, 0.2, 0.05)


def test_formatters_handle_missing_values() -> None:
    assert dash.fmt_money(None) == "n/a" and dash.fmt_pct(float("nan")) == "n/a"
    assert dash.fmt_money(2_500_000) == "$2.5M" and dash.fmt_pct(0.123) == "12.3%"
    assert dash.fmt_number(14.56, " yrs") == "14.6 yrs"


def test_disclaimer_wording_is_exact() -> None:
    assert dash.DISCLAIMER == (
        "Screening and educational tool only. Not financial, investment, or municipal advisory advice. "
        "Based on public data that may be 1–2 years old."
    )


def test_bigger_shock_never_raises_stressed_headroom() -> None:
    cfg = load_config()
    base = pd.DataFrame({
        "ccn": ["1"], "hospital_name": ["test"], "flags": [""], "ebida": [100.0],
        "existing_debt_service": [30.0], "net_patient_revenue": [1000.0], "medicaid_net_revenue": [200.0],
        "medicaid_share_days": [0.2], "salaries": [400.0], "operating_expense": [960.0],
        "depreciation": [50.0], "interest_expense": [10.0], "total_fixed_assets": [500.0],
        "town_population": [5000.0], "town_name": ["Smallville"], "town_source": ["geocoded address"],
        "nmtc_eligible": [False], "tract_geoid": ["29000000100"],
    })
    def stressed(volume_drop: float) -> float:
        hospitals, _ = dash.recompute(base, dash.build_scenarios(0.1, volume_drop, 0.05), 1.25, 0.4,
                                      cfg["capital_types"], cfg["capital_ladder"])
        return hospitals.loc[0, "headroom_stressed"]
    assert stressed(0.20) < stressed(0.10) < stressed(0.0)


@pytest.mark.skipif(not (ROOT / "data" / "hospitals.duckdb").exists(), reason="database not built")
def test_app_renders_without_error() -> None:
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert any(dash.DISCLAIMER in caption.value for caption in app.caption)


@pytest.mark.skipif(not (ROOT / "data" / "hospitals.duckdb").exists(), reason="database not built")
def test_sliders_recalculate_the_page() -> None:
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    negative = lambda a: int(next(m.value for m in a.metric if m.label == "Negative under stress"))  # noqa: E731
    before = negative(app)
    volume = next(s for s in app.sidebar.slider if s.label == "Patient volume drop")
    volume.set_value(0.30).run()
    assert not app.exception
    assert negative(app) > before  # a deeper volume drop pushes more hospitals negative


def test_nearest_label_finds_the_clicked_dot() -> None:
    hospitals = pd.DataFrame({"label": ["A", "B", "C"], "latitude": [38.0, 39.0, None], "longitude": [-92.0, -94.0, None]})
    assert dash.nearest_label(hospitals, {"lat": 39.0001, "lng": -94.0001}) == "B"
    assert dash.nearest_label(hospitals, None) is None
