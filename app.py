"""Phase 5 dashboard.

Run:  streamlit run app.py      (after scripts/phase1.py ... phase4.py have built the database)
"""

import sys
from pathlib import Path

import duckdb
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from hcap import dashboard as dash  # noqa: E402
from hcap import matcher  # noqa: E402
from hcap.config import load_config  # noqa: E402

LOCATION = ["ccn", "latitude", "longitude", "geocoded", "geocode_source", "tract_geoid", "nmtc_eligible",
            "town_name", "town_population", "town_source"]


@st.cache_data
def load_base(db_path: str) -> pd.DataFrame:
    """Phase 2 metrics plus Phase 4 location facts: the inputs the sliders recompute from."""
    with duckdb.connect(db_path, read_only=True) as con:
        metrics = con.execute("SELECT * FROM metrics").df()
        location = con.execute(f"SELECT {', '.join(LOCATION)} FROM matches").df()
    return metrics.merge(location, on="ccn")


def sidebar_sliders(cfg: dict) -> dict[str, float]:
    """Scenario assumption sliders. Starting values and ranges come from config.yaml."""
    st.sidebar.header("Scenario assumptions")
    st.sidebar.caption("Move a slider and every number, colour and match on the page is recalculated.")
    ranges, defaults = cfg["dashboard"]["sliders"], cfg["stress"]
    combined = defaults["scenarios"]["combined"]
    start = {"target_dscr": defaults["target_dscr"], "variable_cost_share": defaults["variable_cost_share"], **combined}
    labels = {
        "target_dscr": ("Target debt service coverage (x)", "%.2f"),
        "medicaid_cut": ("Medicaid revenue cut", "%.2f"),
        "volume_drop": ("Patient volume drop", "%.2f"),
        "labor_increase": ("Salary increase", "%.2f"),
        "variable_cost_share": ("Share of costs that fall with volume", "%.2f"),
    }
    values = {}
    for key, (label, fmt) in labels.items():
        low, high, step = ranges[key]
        values[key] = st.sidebar.slider(label, float(low), float(high), float(start[key]), float(step), format=fmt)
    st.sidebar.caption("Fractions: 0.10 means 10%.")
    return values


def draw_map(hospitals: pd.DataFrame, cfg: dict) -> str | None:
    """Folium map coloured by stressed headroom. Returns the label of the hospital clicked, if any."""
    bands = cfg["dashboard"]["headroom_margin_bands"]
    fmap = folium.Map(location=cfg["dashboard"]["map_center"], zoom_start=cfg["dashboard"]["map_zoom"],
                      tiles="OpenStreetMap")
    for _, row in hospitals[hospitals["latitude"].notna()].iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=8, weight=2, color="#ffffff",
            fill=True, fill_color=dash.band_color(row["headroom_stressed_margin"], bands), fill_opacity=0.95,
            tooltip=row["label"],
            popup=folium.Popup(
                f"<b>{row['label']}</b><br>Stressed headroom: {dash.fmt_money(row['headroom_stressed'])} a year"
                f"<br>Primary match: {row['primary_label']}", max_width=320),
        ).add_to(fmap)
    chips = [*zip(dash.BAND_COLORS, dash.band_labels(bands)), (dash.NO_DATA_COLOR, "cannot assess")]
    legend = " &nbsp; ".join(
        f"<span style='display:inline-block;width:12px;height:12px;border-radius:50%;background:{c};"
        f"margin-right:4px;vertical-align:middle'></span>{text}" for c, text in chips)
    st.markdown(f"<div style='font-size:0.85rem'>Stressed headroom as a share of patient revenue: &nbsp; {legend}</div>",
                unsafe_allow_html=True)
    out = st_folium(fmap, height=520, use_container_width=True, returned_objects=["last_object_clicked"], key="map")
    return dash.nearest_label(hospitals, (out or {}).get("last_object_clicked"))


def show_hospital(row: pd.Series, details: pd.DataFrame, cfg: dict) -> None:
    """Metrics, scenario results and capital matches for one hospital."""
    st.subheader(row["label"])
    stars = "no star rating" if pd.isna(row["star_rating"]) else f"{row['star_rating']:.0f} of 5 stars"
    population = "" if pd.isna(row["town_population"]) else f" (population {row['town_population']:,.0f})"
    st.caption(f"{row['hospital_type'] or row['ccn_facility_type']} · {row['town_name']}{population} · {stars} · "
               f"fiscal year ending {pd.Timestamp(row['fy_end']):%b %Y}")
    if row["flags"]:
        st.caption(f"Data caveats: {row['flags']}")

    tiles = [
        ("Operating margin", dash.fmt_pct(row["operating_margin"])),
        ("EBIDA", dash.fmt_money(row["ebida"])),
        ("Days cash on hand", dash.fmt_number(row["days_cash_on_hand"])),
        ("Average age of plant", dash.fmt_number(row["avg_age_of_plant"], " yrs")),
        ("Debt / capitalization", dash.fmt_pct(row["debt_to_capitalization"])),
        ("Existing debt service (approx.)", dash.fmt_money(row["existing_debt_service"])),
        ("Medicaid share of days", dash.fmt_pct(row["medicaid_share_days"])),
        ("Medicare share of days", dash.fmt_pct(row["medicare_share_days"])),
    ]
    for start in (0, 4):
        for column, (name, value) in zip(st.columns(4), tiles[start:start + 4]):
            column.metric(name, value)

    left, right = st.columns(2)
    with left:
        st.markdown("**Stress test**")
        if pd.isna(row["headroom_stressed"]):
            st.write("Not available: headroom needs EBIDA and debt service, and interest expense is missing.")
        else:
            st.dataframe(dash.scenario_table(row), hide_index=True, use_container_width=True)
            st.caption(f"Stressed headroom (the lowest): {dash.fmt_money(row['headroom_stressed'])} a year.")
            st.markdown("**What that payment could borrow**")
            st.dataframe(dash.principal_table(row, cfg["capital_types"]), hide_index=True, use_container_width=True)
    with right:
        st.markdown("**Capital match**")
        st.info(f"**Primary: {row['primary_label']}**\n\n{row['primary_reason']}")
        mine = details[details["ccn"] == row["ccn"]].set_index("rung")
        for rung in [r for r in reversed(list(matcher.LADDER)) if r in mine.index and r != row["primary_match"]]:
            if mine.loc[rung, "qualifies"] is True or mine.loc[rung, "qualifies"] == True:  # noqa: E712
                st.success(f"**Alternate: {mine.loc[rung, 'label']}**\n\n{mine.loc[rung, 'reason']}")
        if row["sale_leaseback_warning"]:
            st.warning(row["sale_leaseback_warning"])
        with st.expander("Why each rung of the ladder does or does not fit"):
            if mine.empty:
                st.write("No rung was tested because headroom could not be calculated.")
            for rung, item in mine.iterrows():
                mark = {True: "✅ Fits", False: "❌ Does not fit"}.get(item["qualifies"], "❔ Unknown")
                st.markdown(f"**{item['label']}** — {mark}  \n{item['reason']}")
                if rung == "sale_leaseback":
                    st.caption(matcher.SALE_LEASEBACK_WARNING)
        st.caption("Thresholds, rates and terms are placeholders set in config.yaml. "
                   "They are not official program eligibility rules.")


def main() -> None:
    st.set_page_config(page_title="Hospital capital stress test", layout="wide")
    cfg = load_config()
    db_path = ROOT / cfg["data"]["db_path"]
    if not db_path.exists():
        st.error("No database found. Run scripts/phase1.py through scripts/phase4.py first.")
        st.stop()

    s = sidebar_sliders(cfg)
    hospitals, details = dash.recompute(
        load_base(str(db_path)),
        dash.build_scenarios(s["medicaid_cut"], s["volume_drop"], s["labor_increase"]),
        s["target_dscr"], s["variable_cost_share"], cfg["capital_types"], cfg["capital_ladder"])
    hospitals = hospitals.sort_values("label").reset_index(drop=True)

    st.title(f"Hospital capital stress test: {cfg['location']['state_name']}")
    assessed = hospitals["headroom_stressed"].notna()
    for column, (name, value) in zip(st.columns(4), [
        ("Hospitals", len(hospitals)),
        ("Positive under stress", int((hospitals["headroom_stressed"] > 0).sum())),
        ("Negative under stress", int((hospitals["headroom_stressed"] <= 0).sum())),
        ("Cannot assess", int((~assessed).sum())),
    ]):
        column.metric(name, value)

    clicked = draw_map(hospitals, cfg)
    off_map = int(hospitals["latitude"].isna().sum())
    if off_map:
        st.caption(f"{off_map} hospital(s) could not be located and are not on the map; they are in the list below.")
    if clicked and clicked != st.session_state.get("last_click") and clicked in set(hospitals["label"]):
        st.session_state["last_click"] = clicked
        st.session_state["selected"] = clicked

    st.selectbox("Hospital (or click a dot on the map)", hospitals["label"], key="selected")
    show_hospital(hospitals.set_index("label").reset_index().query("label == @st.session_state.selected").iloc[0],
                  details, cfg)

    st.subheader("All hospitals")
    st.caption("Click a column heading to sort.")
    table = dash.export_table(hospitals)
    st.dataframe(table, hide_index=True, use_container_width=True, column_config={
        "Operating margin": st.column_config.NumberColumn(format="percent"),
        "Debt / capitalization": st.column_config.NumberColumn(format="percent"),
        "Medicaid share of days": st.column_config.NumberColumn(format="percent"),
        "Medicare share of days": st.column_config.NumberColumn(format="percent"),
        "Stressed headroom / revenue": st.column_config.NumberColumn(format="percent"),
        "Days cash": st.column_config.NumberColumn(format="%.0f"),
        "Age of plant (yrs)": st.column_config.NumberColumn(format="%.1f"),
        "EBIDA ($)": st.column_config.NumberColumn(format="dollar"),
        "Existing debt service ($)": st.column_config.NumberColumn(format="dollar"),
        "Baseline headroom ($)": st.column_config.NumberColumn(format="dollar"),
        "Stressed headroom ($)": st.column_config.NumberColumn(format="dollar"),
    })
    st.download_button("Download table as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="hospital_capital_matches.csv", mime="text/csv")

    st.divider()
    st.caption(dash.DISCLAIMER)


main()
