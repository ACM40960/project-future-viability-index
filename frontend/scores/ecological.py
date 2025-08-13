# scores/ecological.py - Ecological Scoring for FVI System
"""
Ecological scoring system for coal industry viability assessment.

Components (higher = worse ecological impact):
1) production_mt                (score1)
2) deforestation_ha_per_year    (score1)
3) land_mined_ha                (score1)
4) land_restoration_ratio (inverted) (score1)
5) co2_emissions_mt             (score2)
6) so2_emissions_mt             (score3)
7) nox_emissions_mt             (score3)

Notes
- All dataset columns are treated as lowercase_with_underscores.
- We detect the right dataset by checking for the presence of expected columns.
- We build one feature vector per country, then compute a single weighted score.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional

from .utils import (
    normalize_score,
    validate_data,
    standardize_country_name,
)

#  Weights (sum to 1.0) and caps 

W_PRODUCTION    = 0.20
W_DEFOREST      = 0.25
W_LAND_MINED    = 0.20
W_RESTORATION   = 0.15  
W_CO2           = 0.10
W_SO2           = 0.05
W_NOX           = 0.05

CAP_PRODUCTION  = 5000      # Mt
CAP_DEFOREST    = 1_000_000 # ha/year
CAP_LAND_MINED  = 500_000   # ha
CAP_CO2         = 15000     # Mt
CAP_SO2         = 100       # Mt
CAP_NOX         = 50        # Mt

COUNTRY_COLS = ["entity", "country", "country_name", "Country"]  


#  Public API 

def calculate_ecological_score(
    data_dict: Dict[str, pd.DataFrame],
    country_list: Optional[List[str]] = None
) -> pd.Series:
    """
    Calculate ecological impact scores for coal industry.

    Returns:
        pd.Series: Ecological scores by country (0–100, higher = worse impact)
    """
    datasets = _load_ecological_data(data_dict)
    if not datasets:
        logging.warning("No ecological datasets found. Using fallback scores.")
        return _fallback_ecological_scores(country_list)

    if country_list is None:
        country_list = _extract_countries_from_data(datasets)

    # Index datasets by which metric columns they contain (column-driven routing)
    col_index = _build_column_index(datasets)

    scores: Dict[str, float] = {}
    for country in country_list:
        features = _extract_features_for_country(datasets, col_index, country)
        score = _score_from_features(features)
        scores[country] = score

    logging.info("Calculated ecological scores for %d countries", len(scores))
    return pd.Series(scores)


#  Data loading 

def _load_ecological_data(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for key, df in (data_dict or {}).items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        d = df.copy()
        d.columns = d.columns.str.strip().str.lower().str.replace(" ", "_")
        v = validate_data(d)
        if v.get("is_valid") or len(v.get("issues", [])) <= 2:
            out[key] = d
            logging.info("Loaded ecological dataset '%s' with %d rows", key, len(d))
        else:
            logging.warning("Dropped dataset '%s' due to validation issues: %s", key, v)
    return out


def _extract_countries_from_data(datasets: Dict[str, pd.DataFrame]) -> List[str]:
    seen: set[str] = set()
    for df in datasets.values():
        for col in COUNTRY_COLS:
            if col in df.columns:
                for name in df[col].dropna().unique():
                    std = standardize_country_name(name)
                    if std:
                        seen.add(std)
    return sorted(seen)


#  Column index 

def _build_column_index(datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    """
    Map column_name -> list of dataset keys containing that column.
    Helps us fetch a metric from the correct dataset.
    """
    idx: Dict[str, List[str]] = {}
    for key, df in datasets.items():
        for col in df.columns:
            idx.setdefault(col, []).append(key)
    return idx


#  Feature extraction 

def _candidate_names(country: str) -> List[str]:
    c = country or ""
    names = {c, c.replace(" ", ""), standardize_country_name(c)}
    if c.upper() in {"USA", "US"}:
        names.update({"United States", "United States of America"})
    return [n for n in names if n]


def _latest_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the last row per country-like column, preferring 'year' if present.
    """
    # pick the first available country column
    ccol = next((c for c in COUNTRY_COLS if c in df.columns), None)
    if ccol is None:
        return df
    if "year" in df.columns:
        return df.sort_values("year").drop_duplicates(subset=[ccol], keep="last")
    return df.drop_duplicates(subset=[ccol], keep="last")


def _match_row(df: pd.DataFrame, country: str) -> Optional[pd.Series]:
    latest = _latest_by_country(df)
    candidates = _candidate_names(country)
    for col in COUNTRY_COLS:
        if col not in latest.columns:
            continue
        hit = latest[latest[col].isin(candidates)]
        if not hit.empty:
            return hit.iloc[-1]
    return None


def _get_metric(
    datasets: Dict[str, pd.DataFrame],
    col_index: Dict[str, List[str]],
    country: str,
    column: str
) -> Optional[float]:
    """
    Fetch a single metric for a country from whichever dataset contains the column.
    Preference: if multiple datasets have the column, we take the first that matches the country.
    """
    for key in col_index.get(column, []):
        df = datasets[key]
        row = _match_row(df, country)
        if row is not None and column in row.index and pd.notna(row[column]):
            return float(row[column])
    return None


def _extract_features_for_country(
    datasets: Dict[str, pd.DataFrame],
    col_index: Dict[str, List[str]],
    country: str
) -> Dict[str, float]:
    """
    Build ecological feature vector from the proper datasets/columns.
    """
    feats: Dict[str, float] = {}

    # score1
    feats["production_mt"] = _get_metric(datasets, col_index, country, "production_mt")
    feats["deforestation_ha_per_year"] = _get_metric(datasets, col_index, country, "deforestation_ha_per_year")
    feats["land_mined_ha"] = _get_metric(datasets, col_index, country, "land_mined_ha")
    feats["land_restoration_ratio"] = _get_metric(datasets, col_index, country, "land_restoration_ratio")

    # score2
    feats["co2_emissions_mt"] = _get_metric(datasets, col_index, country, "co2_emissions_mt")

    # score3
    feats["so2_emissions_mt"] = _get_metric(datasets, col_index, country, "so2_emissions_mt")
    feats["nox_emissions_mt"] = _get_metric(datasets, col_index, country, "nox_emissions_mt")

    # drop Nones
    return {k: v for k, v in feats.items() if v is not None}


#  Scoring 

def _score_from_features(features: Dict[str, float]) -> float:
    comps: List[float] = []

    if "production_mt" in features:
        comps.append(normalize_score(features["production_mt"], 0, CAP_PRODUCTION) * W_PRODUCTION)

    if "deforestation_ha_per_year" in features:
        comps.append(normalize_score(features["deforestation_ha_per_year"], 0, CAP_DEFOREST) * W_DEFOREST)

    if "land_mined_ha" in features:
        comps.append(normalize_score(features["land_mined_ha"], 0, CAP_LAND_MINED) * W_LAND_MINED)

    if "land_restoration_ratio" in features:
        r = features["land_restoration_ratio"]
        r_pct = r * 100.0 if r <= 1.0 else r
        inv = max(0.0, min(100.0, 100.0 - r_pct))  # lower restoration = worse (higher score)
        comps.append(inv * W_RESTORATION)

    if "co2_emissions_mt" in features:
        comps.append(normalize_score(features["co2_emissions_mt"], 0, CAP_CO2) * W_CO2)

    if "so2_emissions_mt" in features:
        comps.append(normalize_score(features["so2_emissions_mt"], 0, CAP_SO2) * W_SO2)

    if "nox_emissions_mt" in features:
        comps.append(normalize_score(features["nox_emissions_mt"], 0, CAP_NOX) * W_NOX)

    if not comps:
        return 50.0

    total = sum(comps)
    return float(min(100.0, max(0.0, total)))


#  Fallback 

def _fallback_ecological_scores(country_list: Optional[List[str]]) -> pd.Series:
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia",
                        "Indonesia", "South Africa", "Poland"]
    fallback = {
        "India": 75.0, "China": 85.0, "Germany": 35.0, "USA": 55.0,
        "Australia": 50.0, "Indonesia": 70.0, "South Africa": 65.0, "Poland": 60.0
    }
    scores = {c: fallback.get(c, 60.0) for c in country_list}
    logging.info("Using fallback ecological scores for %d countries", len(scores))
    return pd.Series(scores)


#  Demo 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Minimal synthetic example with correct column names
    s1 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "year": [2023, 2023, 2023],
        "production_mt": [4362.1, 968.8, 524.0],
        "deforestation_ha_per_year": [4347.7, 965.6, 6000.0],
        "land_mined_ha": [554379, 123125, 66595],
        "land_restoration_ratio": [0.12, 0.12, 0.40],
    })
    s2 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "year": [2023, 2023, 2023],
        "co2_emissions_mt": [3500, 2344.5, 1268.1],
    })
    s3 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "year": [2023, 2023, 2023],
        "so2_emissions_mt": [16.36, 3.63, 1.97],
        "nox_emissions_mt": [9.10, 2.02, 1.09],
    })
    data = {"score1": s1, "score2": s2, "score3": s3}
    print(calculate_ecological_score(data, ["China", "India", "USA"]))
