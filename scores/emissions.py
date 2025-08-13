# scores/emissions.py - Emissions Scoring for FVI System
"""
Emissions scoring system for coal industry viability assessment.

Evaluates carbon emissions and climate impact based on:
1) Direct CO2 Emissions (coal_co2_emissions)
2) Global Share of emissions (global_share)
3) Carbon Tax Coverage (share_carbontax or share_covered_carbon_price)
4) Carbon Abatement Readiness (carbon_abatement_readiness)
5) Emissions Intensity (emissions_intensity_tco2_per_twh)

Notes:
- Higher scores indicate a worse emissions profile (worse for coal viability).
- Columns are handled in lowercase with underscores (standardized).
- Metrics are sourced from preferred datasets; we avoid double counting.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

from .utils import (
    normalize_score,
    validate_data,
    get_latest_data_by_country,   # assumed to use 'year' when present
    standardize_country_name
)

# ----------------------------- Configuration ---------------------------------

# Component weights (sum to 1.0)
W_CO2 = 0.30
W_SHARE = 0.30
W_TAX = 0.20
W_READINESS = 0.15
W_INTENSITY = 0.05

# Normalization caps (tune as needed)
CO2_MAX = 15000         # coal CO2 emissions (Mt)
INTENSITY_MAX = 2000    # tCO2 / TWh

# Columns we rely on (lowercase, underscored)
COL_ENTITY = "entity"
COL_COUNTRY = "country"
COL_COUNTRY_NAME = "country_name"

# ----------------------------- Public API ------------------------------------


def calculate_emissions_score(
    data_dict: Dict[str, pd.DataFrame],
    country_list: Optional[List[str]] = None
) -> pd.Series:
    """
    Calculate emissions impact scores for the coal industry.

    Args:
        data_dict: dict[str, DataFrame]; each DataFrame is a dataset
        country_list: optional list of countries (names as in CSVs or standardized)

    Returns:
        pd.Series: Emissions scores by country (0–100, higher = worse)
    """
    emissions_data = _load_emissions_data(data_dict)
    if not emissions_data:
        logging.warning("No usable emissions datasets found. Using fallback scores.")
        return _fallback_emissions_scores(country_list)

    # Determine countries to score
    if country_list is None:
        country_list = _extract_countries_from_data(emissions_data)

    # Classify datasets by "kind" (based on columns)
    kind_index = _build_kind_index(emissions_data)

    scores: Dict[str, float] = {}
    for country in country_list:
        features = _extract_features_for_country(emissions_data, kind_index, country)
        score = _score_from_features(features)
        scores[country] = score

    logging.info("Calculated emissions scores for %d countries", len(scores))
    return pd.Series(scores)


# ----------------------------- Data Loading ----------------------------------


def _load_emissions_data(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Normalize, validate, and keep usable datasets.
    - Lowercases columns, strips, replaces spaces with underscores.
    - Keeps datasets that pass validation (or have <=2 minor issues).
    """
    out: Dict[str, pd.DataFrame] = {}

    for key, df in (data_dict or {}).items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue

        d = df.copy()
        d.columns = d.columns.str.strip().str.lower().str.replace(" ", "_")
        validation = validate_data(d)
        if validation.get("is_valid") or len(validation.get("issues", [])) <= 2:
            out[key] = d
            logging.info("Loaded emissions dataset '%s' with %d rows", key, len(d))
        else:
            logging.warning("Dropped dataset '%s' due to validation issues: %s", key, validation)

    return out


def _extract_countries_from_data(datasets: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Union of country names across datasets using common country columns.
    """
    countries: set[str] = set()
    for df in datasets.values():
        for col in (COL_ENTITY, COL_COUNTRY, COL_COUNTRY_NAME):
            if col in df.columns:
                for name in df[col].dropna().unique():
                    std = standardize_country_name(name)
                    if std:
                        countries.add(std)
    return sorted(countries)


# ----------------------------- Classification --------------------------------


def _classify_dataset(df_name: str, df: pd.DataFrame) -> str:
    """
    Classify datasets into kinds used for metric preference routing.
    Kinds:
        - 'total_emissions_intensity'  -> has 'emissions_intensity_tco2_per_twh'
        - 'absolute_global_emissions_share' -> has 'global_share'
        - 'carbon_abatement_readiness' -> has 'carbon_abatement_readiness' or 'share_carbontax'
        - 'policy_exempt_emissions'    -> has 'share_covered_carbon_price'
        - 'other'                      -> everything else
    """
    cols = set(df.columns)
    if "emissions_intensity_tco2_per_twh" in cols:
        return "total_emissions_intensity"
    if "global_share" in cols:
        return "absolute_global_emissions_share"
    if "carbon_abatement_readiness" in cols or "share_carbontax" in cols:
        return "carbon_abatement_readiness"
    if "share_covered_carbon_price" in cols:
        return "policy_exempt_emissions"
    return "other"


def _build_kind_index(datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    """
    Map kind -> list of dataset keys in that kind.
    """
    index: Dict[str, List[str]] = {}
    for name, df in datasets.items():
        kind = _classify_dataset(name, df)
        index.setdefault(kind, []).append(name)
    return index


# ----------------------------- Feature Extraction ----------------------------


def _candidate_names(country: str) -> List[str]:
    """
    Build robust matching candidates for a country.
    """
    c = country or ""
    names = {c, c.replace(" ", ""), standardize_country_name(c)}
    if c.upper() in {"USA", "US"}:
        names.update({"United States", "United States of America"})
    return [n for n in names if n]


def _latest_by_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the 'latest' row per entity:
    - If 'year' exists, keep the last year per entity.
    - Else, keep the last occurrence per entity (stable).
    """
    if COL_ENTITY in df.columns:
        if "year" in df.columns:
            return (df.sort_values("year")
                      .drop_duplicates(subset=[COL_ENTITY], keep="last"))
        return df.drop_duplicates(subset=[COL_ENTITY], keep="last")
    # Try fallbacks
    for col in (COL_COUNTRY, COL_COUNTRY_NAME):
        if col in df.columns:
            if "year" in df.columns:
                return (df.sort_values("year")
                          .drop_duplicates(subset=[col], keep="last"))
            return df.drop_duplicates(subset=[col], keep="last")
    return df


def _match_country_row(df: pd.DataFrame, country: str) -> Optional[pd.Series]:
    """
    Find a row matching the country by common country columns.
    """
    latest = _latest_by_entity(df)
    candidates = _candidate_names(country)

    for col in (COL_ENTITY, COL_COUNTRY, COL_COUNTRY_NAME):
        if col not in latest.columns:
            continue
        hit = latest[latest[col].isin(candidates)]
        if not hit.empty:
            return hit.iloc[-1]
    return None


def _first_non_null(values: List[Optional[float]]) -> Optional[float]:
    for v in values:
        if v is not None and pd.notna(v):
            return float(v)
    return None


def _get_metric(
    datasets: Dict[str, pd.DataFrame],
    kind_index: Dict[str, List[str]],
    country: str,
    preferences: List[str],
    column: str
) -> Optional[float]:
    """
    Look up a metric for a country following a list of preferred kinds.
    """
    for kind in preferences:
        for key in kind_index.get(kind, []):
            df = datasets.get(key)
            if df is None or column not in df.columns:
                continue
            row = _match_country_row(df, country)
            if row is not None:
                val = row.get(column)
                if pd.notna(val):
                    return float(val)
    # As a very last resort, scan all datasets that contain the column
    for key, df in datasets.items():
        if column in df.columns:
            row = _match_country_row(df, country)
            if row is not None:
                val = row.get(column)
                if pd.notna(val):
                    return float(val)
    return None


def _extract_features_for_country(
    datasets: Dict[str, pd.DataFrame],
    kind_index: Dict[str, List[str]],
    country: str
) -> Dict[str, float]:
    """
    Build the feature vector for a country using preferred dataset sources.
    """
    feats: Dict[str, float] = {}

    # Preferences per metric (ordered by dataset "kind")
    # - coal_co2_emissions: prefer intensity dataset (often co-reported), else global share dataset
    feats["coal_co2_emissions"] = _get_metric(
        datasets, kind_index, country,
        preferences=["total_emissions_intensity", "absolute_global_emissions_share"],
        column="coal_co2_emissions"
    )

    feats["global_share"] = _get_metric(
        datasets, kind_index, country,
        preferences=["absolute_global_emissions_share"],
        column="global_share"
    )

    # Carbon tax coverage: prefer explicit 'share_carbontax' (often 0–1). Fallback to 'share_covered_carbon_price'.
    tax_share = _get_metric(
        datasets, kind_index, country,
        preferences=["carbon_abatement_readiness"],
        column="share_carbontax"
    )
    if tax_share is None:
        tax_share = _get_metric(
            datasets, kind_index, country,
            preferences=["policy_exempt_emissions"],
            column="share_covered_carbon_price"
        )
    feats["tax_share"] = tax_share

    feats["carbon_abatement_readiness"] = _get_metric(
        datasets, kind_index, country,
        preferences=["carbon_abatement_readiness"],
        column="carbon_abatement_readiness"
    )

    feats["emissions_intensity_tco2_per_twh"] = _get_metric(
        datasets, kind_index, country,
        preferences=["total_emissions_intensity"],
        column="emissions_intensity_tco2_per_twh"
    )

    # Drop None entries
    return {k: v for k, v in feats.items() if v is not None}


# ----------------------------- Scoring ---------------------------------------


def _score_from_features(features: Dict[str, float]) -> float:
    """
    Map features to a 0–100 score using fixed weights.
    """
    components: List[float] = []

    # 1) Direct CO2 (coal)
    if "coal_co2_emissions" in features:
        co2 = features["coal_co2_emissions"]
        components.append(normalize_score(co2, 0, CO2_MAX) * W_CO2)

    # 2) Global share (assumed already in 0–100; if 0–1, implicitly scaled below)
    if "global_share" in features:
        s = features["global_share"]
        s = s * 100.0 if s <= 1.0 else s
        components.append(float(s) * W_SHARE)

    # 3) Carbon tax coverage (0–1 or 0–100)
    if "tax_share" in features:
        t = features["tax_share"]
        t = t * 100.0 if t <= 1.0 else t
        components.append(float(t) * W_TAX)

    # 4) Abatement readiness (0–1 or 0–100)
    if "carbon_abatement_readiness" in features:
        r = features["carbon_abatement_readiness"]
        r = r * 100.0 if r <= 1.0 else r
        components.append(float(r) * W_READINESS)

    # 5) Emissions intensity
    if "emissions_intensity_tco2_per_twh" in features:
        ii = features["emissions_intensity_tco2_per_twh"]
        components.append(normalize_score(ii, 0, INTENSITY_MAX) * W_INTENSITY)

    if not components:
        return 50.0

    total = sum(components)
    return float(min(100.0, max(0.0, total)))


# ----------------------------- Fallback --------------------------------------


def _fallback_emissions_scores(country_list: Optional[List[str]]) -> pd.Series:
    """
    Provide fallback scores when no data is available.
    """
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia",
                        "Indonesia", "South Africa", "Poland"]

    fallback_scores = {
        "India": 68.0,
        "China": 75.0,
        "Germany": 25.0,
        "USA": 32.0,
        "Australia": 45.0,
        "Indonesia": 58.0,
        "South Africa": 72.0,
        "Poland": 55.0
    }

    scores = {c: fallback_scores.get(c, 55.0) for c in country_list}
    logging.info("Using fallback emissions scores for %d countries", len(scores))
    return pd.Series(scores)