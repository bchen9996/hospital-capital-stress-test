"""Tests for raw HCRIS extraction, using a tiny hand-built cell table."""

import pandas as pd

from hcap import hcris, quality


def _cells() -> pd.DataFrame:
    rows = [
        # report 1: buildings 1000 less 400, equipment 500 less 100 (sub-line), total 1000
        ("1", "G000000", "01500", "00100", 1000.0),
        ("1", "G000000", "01600", "00100", -400.0),
        ("1", "G000000", "02300", "00100", 500.0),
        ("1", "G000000", "02401", "00100", -100.0),
        ("1", "G000000", "03000", "00100", 1000.0),
        ("1", "A000000", "11300", "00200", 75.0),
        ("1", "A000000", "11300", "00300", 75.0),  # column 3 must be ignored
        ("1", "A700003", "00300", "01100", 60.0),
        ("1", "A700003", "00100", "01100", 60.0),  # line 1 must be ignored (line 3 is the total)
        # report 2: plant fund column, and no interest cells at all
        ("2", "G000000", "01600", "00400", -250.0),
    ]
    return pd.DataFrame(rows, columns=["rpt", "ws", "line", "col", "val"])


def test_accumulated_depreciation_sums_contra_lines_as_positive() -> None:
    out = hcris.build_fields(_cells(), hcris.FIELDS).set_index("hcris_rpt_rec_num")
    assert out.loc["1", "accumulated_depreciation"] == 500.0  # 400 + 100
    assert out.loc["2", "accumulated_depreciation"] == 250.0


def test_interest_uses_only_the_named_line_and_column() -> None:
    out = hcris.build_fields(_cells(), hcris.FIELDS).set_index("hcris_rpt_rec_num")
    assert out.loc["1", "interest_ws_a"] == 75.0
    assert out.loc["1", "interest_a7_allowable"] == 60.0


def test_absent_cells_stay_missing_not_zero() -> None:
    out = hcris.build_fields(_cells(), hcris.FIELDS).set_index("hcris_rpt_rec_num")
    assert pd.isna(out.loc["2", "interest_ws_a"])
    assert pd.isna(out.loc["1", "interest_a7_booked"])


def test_match_reports_by_ccn_and_period_flags_version_change() -> None:
    period = {"fy_begin": pd.to_datetime(["2024-01-01"] * 2), "fy_end": pd.to_datetime(["2024-12-31"] * 2)}
    hospitals = pd.DataFrame({"ccn": ["000001", "000002"], "rpt_rec_num": ["10", "20"], **period})
    rpt = pd.DataFrame({"hcris_rpt_rec_num": ["10", "99"], "ccn": ["000001", "000002"],
                        "hcris_status": ["1", "5"], **period})
    out = hcris.match_reports(hospitals, rpt)
    assert out["hcris_matched"].tolist() == [True, True]
    assert out["hcris_same_version"].tolist() == [True, False]


def test_fixed_asset_rollup_flags_only_the_broken_report() -> None:
    ids = {"hospital_name": ["a", "b"], "ccn_facility_type": ["STH", "STH"]}
    df = pd.DataFrame({"ccn": ["1", "2"], **ids, "hcris_gross_fixed_assets": [1500.0, 1500.0],
                       "accumulated_depreciation": [500.0, 500.0],
                       "hcris_total_fixed_assets": [1000.0, 900.0]})
    out = quality.fixed_asset_rollup(df)
    assert out["ccn"].tolist() == ["2"] and out.loc[0, "gap"] == 100.0
