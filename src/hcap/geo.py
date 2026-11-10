"""Location facts for each hospital: coordinates, census tract, town and town population.

Sources:
  - U.S. Census Bureau geocoder (address -> coordinates, 2020 tract, incorporated place)
  - Census Bureau city/town population file (place -> population)
  - CDFI Fund NMTC Low-Income Community dataset (tract -> eligible yes/no)
"""

import re
from pathlib import Path

import pandas as pd
import requests

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
GEO_COLUMNS = ["ccn", "geocoded_address", "latitude", "longitude", "tract_geoid", "place_geoid", "place_name"]


def clean_street(street: str) -> str:
    """Tidy a street line so the geocoder can read it: drop PO boxes, spell 'ONE' as 1."""
    street = re.sub(r",?\s*P\.?\s?O\.?\s*BOX.*$", "", street.upper().strip())
    street = re.sub(r"^ONE\b", "1", street)
    return re.sub(r"\s+", " ", street.replace(".", " ").replace("'", "")).strip()


def normalize_town(name: str, census_name: bool = False) -> str:
    """Comparable town name: upper case, 'ST.' spelled out.

    Census names end in a type word ("Jefferson City city"); `census_name=True` drops it.
    """
    name = name.upper().strip()
    if census_name:
        name = re.sub(r"\s+(CITY|TOWN|VILLAGE)$", "", name)
    name = re.sub(r"\bSTE\b\.?", "SAINTE", name)
    name = re.sub(r"\bST\b\.?", "SAINT", name)
    return re.sub(r"[^A-Z ]", "", name).strip()


def candidate_addresses(row: pd.Series) -> list[str]:
    """Addresses to try, best first: Care Compare address, then the cost report address."""
    pairs = [
        (row.get("hgi_address"), row.get("hgi_city"), row.get("hgi_zip")),
        (row.get("street"), row.get("city"), row.get("zip")),
    ]
    found = [f"{clean_street(street)}, {city}, MO {str(zip_code)[:5]}" for street, city, zip_code in pairs
             if pd.notna(street) and pd.notna(city)]
    return list(dict.fromkeys(found))


def parse_geocoder_response(payload: dict) -> dict | None:
    """Pull coordinates, tract and incorporated place out of a geocoder reply. None if no match."""
    matches = payload.get("result", {}).get("addressMatches", [])
    if not matches:
        return None
    match = matches[0]
    layers = match.get("geographies", {})
    tract = (layers.get("Census Tracts") or [{}])[0]
    place = (layers.get("Incorporated Places") or [{}])[0]
    return {
        "latitude": match["coordinates"]["y"],
        "longitude": match["coordinates"]["x"],
        "tract_geoid": tract.get("GEOID"),
        "place_geoid": place.get("GEOID"),
        "place_name": place.get("NAME"),
    }


def geocode_address(address: str, session: requests.Session) -> dict | None:
    """Look up one address with the Census geocoder."""
    params = {"address": address, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"}
    resp = session.get(GEOCODER_URL, params=params, timeout=60)
    resp.raise_for_status()
    return parse_geocoder_response(resp.json())


def geocode_hospitals(hospitals: pd.DataFrame, cache_path: Path) -> pd.DataFrame:
    """Geocode every hospital once; results are cached in a CSV so reruns make no calls."""
    cache = (pd.read_csv(cache_path, dtype={"ccn": str, "tract_geoid": str, "place_geoid": str})
             if cache_path.exists() else pd.DataFrame(columns=GEO_COLUMNS))
    todo = hospitals[~hospitals["ccn"].isin(cache["ccn"])]
    rows = []
    with requests.Session() as session:
        for _, row in todo.iterrows():
            result, used = None, None
            for address in candidate_addresses(row):
                result, used = geocode_address(address, session), address
                if result:
                    break
            rows.append({"ccn": row["ccn"], "geocoded_address": used if result else None, **(result or {})})
    if rows:
        cache = pd.concat([cache, pd.DataFrame(rows, columns=GEO_COLUMNS)], ignore_index=True)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.to_csv(cache_path, index=False)
    return cache


def load_town_population(path: Path, population_column: str) -> pd.DataFrame:
    """Population of each incorporated place (Census summary level 162), keyed by place GEOID."""
    raw = pd.read_csv(path, dtype=str, encoding="latin-1")
    places = raw[raw["SUMLEV"] == "162"]
    return pd.DataFrame({
        "place_geoid": places["STATE"] + places["PLACE"],
        "town_name": places["NAME"],
        "town_population": pd.to_numeric(places[population_column]),
    })


def load_nmtc_tracts(path: Path) -> pd.DataFrame:
    """CDFI Fund list of 2020 census tracts and whether each is an NMTC Low-Income Community."""
    raw = pd.read_excel(path, sheet_name=0, header=1, dtype=str)
    tract_col, eligible_col = raw.columns[0], raw.columns[2]
    if "GEOID" not in tract_col or "Qualify For NMTC" not in eligible_col:
        raise KeyError(f"NMTC file layout changed: {tract_col!r}, {eligible_col!r}")
    return pd.DataFrame({
        "tract_geoid": raw[tract_col].str.zfill(11),
        "nmtc_eligible": raw[eligible_col].str.strip().str.upper() == "YES",
    })


def attach_location(df: pd.DataFrame, geo: pd.DataFrame, towns: pd.DataFrame, nmtc: pd.DataFrame) -> pd.DataFrame:
    """Join location facts onto the hospital table.

    Town population comes from the incorporated place the address falls in. Where the
    address was not geocoded, or sits outside town limits, the mailing city's name is
    matched to a town instead; `town_source` records which was used. `nmtc_eligible`
    stays missing when the address could not be geocoded (the tract is unknown).
    """
    out = df.merge(geo, on="ccn", how="left")
    out = out.merge(towns[["place_geoid", "town_population"]], on="place_geoid", how="left")
    keys = towns["town_name"].map(lambda n: normalize_town(n, census_name=True))
    by_name = towns.assign(key=keys).drop_duplicates("key", keep=False)
    city = out["hgi_city"].fillna(out["city"]).map(normalize_town)
    fallback = city.map(by_name.set_index("key")["town_population"])
    out["town_source"] = "geocoded address"
    out.loc[out["town_population"].isna() & fallback.notna(), "town_source"] = "mailing city name"
    out["town_population"] = out["town_population"].fillna(fallback)
    out["town_name"] = out["place_name"].fillna(out["hgi_city"].fillna(out["city"]).str.title())
    out.loc[out["town_population"].isna(), "town_source"] = "unknown"
    out = out.merge(nmtc, on="tract_geoid", how="left")
    out["geocoded"] = out["latitude"].notna()
    return out
