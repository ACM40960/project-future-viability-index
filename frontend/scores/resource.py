# scores/resource.py - Resource Scoring for FVI System
"""
Resource scoring system for coal industry viability assessment.

Components (higher = better resource availability):
1) production_mt            (score1 preferred; score2/score3 fallback)
2) proven_reserves_mt       (score1 preferred; score3 fallback)
3) r_p_ratio                (score1)
4) land_mined_share (inverted: lower is better)  (score1)
5) water_usage_share (inverted: lower is better) (score2)
6) production_share         (score3)

All dataset columns are treated as lowercase_with_underscores.
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

W_PRODUCTION   = 0.30
W_RESERVES     = 0.30
W_RP           = 0.20
W_LAND_SHARE   = 0.10   # inverted (lower share => higher score)
W_WATER_SHARE  = 0.05   # inverted
W_PROD_SHARE   = 0.05

CAP_PRODUCTION = 5000      # Mt
# reserves use log10 scaling; typical range ~ 10^2 ... 10^6 Mt  => 2..6
LOG_RES_MIN    = 2.0
LOG_RES_MAX    = 6.0
CAP_RP         = 200       # years (cap)
# shares are handled as percentages (0..100) after normalization

COUNTRY_COLS = ["entity", "country", "country_name"]


#  Public API 

def calculate_resource_score(
    data_dict: Dict[str, pd.DataFrame],
    country_list: Optional[List[str]] = None
) -> pd.Series:
    """
    Returns:
        pd.Series: Resource scores by country (0–100, higher = better)
    """
    datasets = _load_resource_data(data_dict)
    if not datasets:
        logging.warning("No resource datasets found. Using fallback scores.")
        return _fallback_resource_scores(country_list)

    if country_list is None:
        country_list = _extract_countries_from_data(datasets)

    kind_index = _build_kind_index(datasets)  # classify datasets by columns

    scores: Dict[str, float] = {}
    for country in country_list:
        feats = _extract_features_for_country(datasets, kind_index, country)
        scores[country] = _score_from_features(feats)

    logging.info("Calculated resource scores for %d countries", len(scores))
    return pd.Series(scores)


#  Data loading 

def _load_resource_data(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for key, df in (data_dict or {}).items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        d = df.copy()
        d.columns = d.columns.str.strip().str.lower().str.replace(" ", "_")
        v = validate_data(d)
        if v.get("is_valid") or len(v.get("issues", [])) <= 2:
            out[key] = d
            logging.info("Loaded resource dataset '%s' with %d rows", key, len(d))
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


#  Dataset classification (by columns) 

def _classify_dataset(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    # Heuristics to tag resource dataset "kinds"
    if {"r_p_ratio", "land_mined_share"} & cols or "r_p_ratio" in cols:
        return "resource_score1"
    if {"water_usage_share", "water_usage_mm3"} & cols:
        return "resource_score2"
    if {"production_share", "waste_to_use_ratio", "coal_ash_mt"} & cols:
        return "resource_score3"
    return "other"


def _build_kind_index(datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    for name, df in datasets.items():
        kind = _classify_dataset(df)
        idx.setdefault(kind, []).append(name)
    return idx


#  Feature extraction 

def _candidate_names(country: str) -> List[str]:
    c = country or ""
    names = {c, c.replace(" ", ""), standardize_country_name(c)}
    if c.upper() in {"USA", "US"}:
        names.update({"United States", "United States of America"})
    return [n for n in names if n]


def _latest_by_country(df: pd.DataFrame) -> pd.DataFrame:
    # Choose first available country-like column
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


def _get_metric_from_kinds(
    datasets: Dict[str, pd.DataFrame],
    kind_index: Dict[str, List[str]],
    country: str,
    preferences: List[str],
    column: str
) -> Optional[float]:
    # Try in preferred dataset kinds
    for kind in preferences:
        for key in kind_index.get(kind, []):
            df = datasets.get(key)
            if df is None or column not in df.columns:
                continue
            row = _match_row(df, country)
            if row is not None:
                val = row.get(column)
                if pd.notna(val):
                    return float(val)
    # Last resort: scan any dataset that has the column
    for key, df in datasets.items():
        if column in df.columns:
            row = _match_row(df, country)
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
    feats: Dict[str, float] = {}

    # production_mt: prefer score1, then score2, then score3
    feats["production_mt"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score1", "resource_score2", "resource_score3"],
        column="production_mt"
    )

    # proven_reserves_mt: prefer score1, fallback score3
    feats["proven_reserves_mt"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score1", "resource_score3"],
        column="proven_reserves_mt"
    )

    # r_p_ratio, land_mined_share: score1
    feats["r_p_ratio"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score1"],
        column="r_p_ratio"
    )

    feats["land_mined_share"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score1"],
        column="land_mined_share"
    )

    # water_usage_share: score2
    feats["water_usage_share"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score2"],
        column="water_usage_share"
    )

    # production_share: score3
    feats["production_share"] = _get_metric_from_kinds(
        datasets, kind_index, country,
        preferences=["resource_score3"],
        column="production_share"
    )

    return {k: v for k, v in feats.items() if v is not None}


#  Scoring 

def _score_from_features(features: Dict[str, float]) -> float:
    comps: List[float] = []

    # 1) Production capacity (higher is better)
    if "production_mt" in features:
        comps.append(normalize_score(features["production_mt"], 0, CAP_PRODUCTION) * W_PRODUCTION)

    # 2) Proven reserves (log scale; higher is better)
    if "proven_reserves_mt" in features:
        res = max(1.0, float(features["proven_reserves_mt"]))
        res_log = np.log10(res)
        res_log = max(LOG_RES_MIN, min(LOG_RES_MAX, res_log))
        comps.append(normalize_score(res_log, LOG_RES_MIN, LOG_RES_MAX) * W_RESERVES)

    # 3) R/P ratio (higher is better, capped)
    if "r_p_ratio" in features:
        rp = min(float(features["r_p_ratio"]), CAP_RP)
        comps.append(normalize_score(rp, 0, CAP_RP) * W_RP)

    # 4) Land mined share (lower is better) -> invert to 0..100
    if "land_mined_share" in features:
        v = float(features["land_mined_share"])
        v_pct = v * 100.0 if v <= 1.0 else v
        inv = max(0.0, min(100.0, 100.0 - v_pct))
        comps.append(inv * W_LAND_SHARE)

    # 5) Water usage share (lower is better)
    if "water_usage_share" in features:
        v = float(features["water_usage_share"])
        v_pct = v * 100.0 if v <= 1.0 else v
        inv = max(0.0, min(100.0, 100.0 - v_pct))
        comps.append(inv * W_WATER_SHARE)

    # 6) Production share (higher is better; assume 0..100 or 0..1)
    if "production_share" in features:
        v = float(features["production_share"])
        v_pct = v * 100.0 if v <= 1.0 else v
        comps.append(max(0.0, min(100.0, v_pct)) * W_PROD_SHARE)

    if not comps:
        return 50.0

    total = sum(comps)
    return float(min(100.0, max(0.0, total)))


#  Fallback 

def _fallback_resource_scores(country_list: Optional[List[str]]) -> pd.Series:
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia",
                        "Indonesia", "South Africa", "Poland"]
    fallback = {
        "India": 70.0, "China": 85.0, "Germany": 45.0, "USA": 80.0,
        "Australia": 90.0, "Indonesia": 75.0, "South Africa": 60.0, "Poland": 55.0
    }
    scores = {c: fallback.get(c, 60.0) for c in country_list}
    logging.info("Using fallback resource scores for %d countries", len(scores))
    return pd.Series(scores)


#  Demo 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Minimal synthetic example with correct column names
    s1 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "production_mt": [4362.1, 968.8, 524.0],
        "land_mined_share": [0.1524, 0.1524, 0.08],
        "proven_reserves_mt": [143197.0, 111052.0, 251500.0],
        "r_p_ratio": [33.0, 115.0, 370.0],  # will be capped at 200
    })
    s2 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "production_mt": [4362.1, 968.8, 524.0],
        "water_usage_share": [0.50, 0.11, 0.20],
    })
    s3 = pd.DataFrame({
        "country": ["China", "India", "United States"],
        "production_mt": [4362.1, 968.8, 524.0],
        "production_share": [31.0, 7.2, 14.5],
        "proven_reserves_mt": [143197.0, 111052.0, 251500.0],
    })
    data = {"score1": s1, "score2": s2, "score3": s3}
    out = calculate_resource_score(data, ["China", "India", "USA"])
    print(out)
