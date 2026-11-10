"""Tests for Phase 1 helpers, using tiny hand-built frames."""

import pandas as pd
import pytest

from hcap import ingest, quality


def test_normalize_ccn_pads_leading_zeros() -> None:
    assert ingest.normalize_ccn(pd.Series(["10001", " 260050 "])).tolist() == ["010001", "260050"]


def test_check_columns_raises_on_renamed_column() -> None:
    with pytest.raises(KeyError, match="Net Income"):
        ingest.check_columns(pd.DataFrame({"a": [1]}), ["Net Income"], "test")


def _periods() -> pd.DataFrame:
    return pd.DataFrame({
        "ccn": ["000001", "000002", "000002"],
        "fy_begin": pd.to_datetime(["2024-01-01", "2023-10-01", "2024-07-01"]),
        "fy_end": pd.to_datetime(["2024-12-31", "2024-06-30", "2025-06-30"]),
    })


def test_period_days_counts_both_end_dates() -> None:
    out = ingest.add_period_fields(_periods(), 360, 371)
    assert out["period_days"].tolist() == [366, 274, 365]  # 2024 is a leap year


def test_partial_year_and_latest_flags() -> None:
    out = ingest.add_period_fields(_periods(), 360, 371)
    assert out["is_full_year"].tolist() == [True, False, True]
    assert out["reports_for_ccn"].tolist() == [1, 2, 2]
    assert out["is_latest_for_ccn"].tolist() == [True, False, True]


def test_join_hgi_marks_unmatched_without_dropping() -> None:
    cost = pd.DataFrame({"ccn": ["000001", "000009"]})
    hgi = pd.DataFrame({"ccn": ["000001"], "star_rating": [4.0]})
    out = ingest.join_hgi(cost, hgi)
    assert out["hgi_matched"].tolist() == [True, False]
    assert pd.isna(out.loc[1, "star_rating"])


def test_negative_values_reports_only_negatives() -> None:
    df = pd.DataFrame({
        "ccn": ["1", "2"], "hospital_name": ["a", "b"], "ccn_facility_type": ["STH", "CAH"],
        "cash": [-5.0, 10.0], "beds": [20.0, None],
    })
    out = quality.negative_values(df, ["cash", "beds"])
    assert out[["ccn", "field", "value"]].values.tolist() == [["1", "cash", -5.0]]


def test_missing_summary_counts_blanks() -> None:
    out = quality.missing_summary(pd.DataFrame({"x": [1.0, None, None, 4.0]}), ["x"])
    assert out.loc[0, "missing"] == 2 and out.loc[0, "pct_missing"] == 50.0
