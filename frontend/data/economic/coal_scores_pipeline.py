
# coal_scores_pipeline.py
# -------------------------------------------------------------
# Utilities to compute coal-related 'small scores' and a composite
# economic score, with normalization and basic visualizations.
#
# Expected inputs (CSV files):
# - score1_global.csv: ['year','global_coal_rents_usd','global_gdp_usd','score1_coal_rent_share_percent']
# - score1a_country_year.csv: ['country_iso3','country_name','year','coal_rents_pct','gdp_usd','coal_rents_usd']
# - score2_global.csv: ['year','world_coal_share_electricity_pct','assumed_electricity_sector_share_gdp','score2_global_pct']
# - score2a_country_year.csv: ['country_iso3','country_name','year','coal_share_electricity_pct','assumed_electricity_sector_share_gdp','score2a_coal_power_gdp_share_pct']
# - score3_country_year.csv: ['country_iso3','country_name','coal_exports_usd','total_exports_usd','total_exports_year','coal_export_share_percent']
#
# If your column names differ slightly, use the 'rename_*' helpers below to adapt.
#
# Notes
# -----
# * Score 1 (global) is context; the country-level 'small scores' are:
#     - Score1a: Coal rents (% of GDP) = coal_rents_pct
#     - Score2a: Coal-power GDP share (%) = coal_share_electricity_pct * assumed_electricity_sector_share_gdp
#     - Score3 : Coal export dependency (%) = 100 * coal_exports_usd / total_exports_usd
# * The composite economic score is a weighted mean of normalized small scores.
# * Normalization can be min-max (default) or z-score (optional).
#
# -------------------------------------------------------------

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------
# Column harmonization
# ----------------------

def rename_score1a_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        'country': 'country_name',
        'iso3': 'country_iso3',
        'coal_rents_percent_gdp': 'coal_rents_pct',
        'coal_rents_%_gdp': 'coal_rents_pct'
    }
    return df.rename(columns={k:v for k,v in mapping.items() if k in df.columns})

def rename_score2a_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        'coal_elec_share_pct': 'coal_share_electricity_pct',
        'elec_sector_share_gdp': 'assumed_electricity_sector_share_gdp',
        'coal_power_gdp_share_pct': 'score2a_coal_power_gdp_share_pct'
    }
    return df.rename(columns={k:v for k,v in mapping.items() if k in df.columns})

def rename_score3_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        'exports_total_usd': 'total_exports_usd',
        'exports_year': 'total_exports_year',
        'coal_exports_value_usd': 'coal_exports_usd',
        'coal_exports_share_pct': 'coal_export_share_percent'
    }
    return df.rename(columns={k:v for k,v in mapping.items() if k in df.columns})

# ----------------------
# Loaders
# ----------------------

def load_score1a(path_score1a: str) -> pd.DataFrame:
    """
    Returns columns: country_iso3, country_name, year, score1a
    where score1a = coal_rents_pct
    """
    df = pd.read_csv(path_score1a)
    df = rename_score1a_columns(df)
    # infer the % column name
    pct_col = 'coal_rents_pct' if 'coal_rents_pct' in df.columns else None
    if pct_col is None:
        cand = [c for c in df.columns if ('coal' in c.lower() and 'rent' in c.lower()) and ('%' in c.lower() or 'pct' in c.lower())]
        if cand:
            pct_col = cand[0]
        else:
            raise ValueError("Could not find coal_rents_pct column.")
    # ensure minimal columns exist
    need = ['country_iso3','country_name','year',pct_col]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns in score1a: {miss}")
    out = df[['country_iso3','country_name','year',pct_col]].copy()
    out = out.rename(columns={pct_col:'score1a'})
    return out

def load_score2a(path_score2a: str) -> pd.DataFrame:
    """
    Returns columns: country_iso3, country_name, year, score2a
    where score2a = coal_share_electricity_pct * assumed_electricity_sector_share_gdp
    If 'score2a_coal_power_gdp_share_pct' already exists, it is used directly.
    """
    df = pd.read_csv(path_score2a)
    df = rename_score2a_columns(df)
    # If precomputed score2a exists, use it
    if 'score2a_coal_power_gdp_share_pct' in df.columns:
        out = df[['country_iso3','country_name','year','score2a_coal_power_gdp_share_pct']].copy()
        out = out.rename(columns={'score2a_coal_power_gdp_share_pct':'score2a'})
        return out
    # Otherwise compute it
    need = ['country_iso3','country_name','year','coal_share_electricity_pct','assumed_electricity_sector_share_gdp']
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns for score2a: {miss}")
    out = df[['country_iso3','country_name','year','coal_share_electricity_pct','assumed_electricity_sector_share_gdp']].copy()
    out['score2a'] = (out['coal_share_electricity_pct'] / 100.0) * (out['assumed_electricity_sector_share_gdp'] * 100.0)
    # score2a is in percentage points of GDP
    out = out[['country_iso3','country_name','year','score2a']]
    return out

def load_score3(path_score3: str) -> pd.DataFrame:
    """
    Returns columns: country_iso3, country_name, year, score3
    where score3 = 100 * coal_exports_usd / total_exports_usd
    Uses 'total_exports_year' as 'year' if present; otherwise requires a year column.
    """
    df = pd.read_csv(path_score3)
    df = rename_score3_columns(df)
    # prefer provided 'coal_export_share_percent'
    if 'coal_export_share_percent' in df.columns:
        year_col = 'total_exports_year' if 'total_exports_year' in df.columns else ('year' if 'year' in df.columns else None)
        if year_col is None:
            raise ValueError("Provide 'total_exports_year' or 'year' in score3 file.")
        out = df[['country_iso3','country_name',year_col,'coal_export_share_percent']].copy()
        out = out.rename(columns={year_col:'year','coal_export_share_percent':'score3'})
        return out
    # else compute
    need = ['country_iso3','country_name','coal_exports_usd','total_exports_usd']
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns for score3: {miss}")
    year_col = 'total_exports_year' if 'total_exports_year' in df.columns else ('year' if 'year' in df.columns else None)
    if year_col is None:
        raise ValueError("Provide 'total_exports_year' or 'year' in score3 file.")
    out = df[['country_iso3','country_name',year_col,'coal_exports_usd','total_exports_usd']].copy()
    out['score3'] = 100.0 * out['coal_exports_usd'] / out['total_exports_usd']
    out = out.rename(columns={year_col:'year'})[['country_iso3','country_name','year','score3']]
    return out

def load_small_scores(path_score1a: str, path_score2a: str, path_score3: str) -> pd.DataFrame:
    s1a = load_score1a(path_score1a)
    s2a = load_score2a(path_score2a)
    s3  = load_score3(path_score3)
    # merge on country/year
    df = s1a.merge(s2a, on=['country_iso3','country_name','year'], how='outer')
    df = df.merge(s3, on=['country_iso3','country_name','year'], how='outer')
    # rename columns to ensure uniqueness
    df = df.rename(columns={'score1a':'score1a','score2a':'score2a','score3':'score3'})
    return df

# ----------------------
# Normalization
# ----------------------

def minmax(x: pd.Series, lower_clip: float=None, upper_clip: float=None) -> pd.Series:
    y = x.copy()
    if lower_clip is not None:
        y = y.clip(lower=y.quantile(lower_clip))
    if upper_clip is not None:
        y = y.clip(upper=y.quantile(upper_clip))
    mn, mx = y.min(), y.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        return pd.Series(np.nan, index=x.index)
    return (y - mn) / (mx - mn)

def zscore(x: pd.Series, winsorize: float=None) -> pd.Series:
    y = x.copy()
    if winsorize is not None and winsorize > 0:
        lo, hi = y.quantile(winsorize), y.quantile(1-winsorize)
        y = y.clip(lower=lo, upper=hi)
    mu, sd = y.mean(), y.std(ddof=0)
    if pd.isna(mu) or sd == 0 or pd.isna(sd):
        return pd.Series(np.nan, index=x.index)
    return (y - mu) / sd

def normalize_by_year(df: pd.DataFrame, metrics, method: str='minmax', **kwargs) -> pd.DataFrame:
    """
    Returns a copy of df with new columns 'n_<metric>' normalized within each year.
    method: 'minmax' (default) or 'zscore'.
    kwargs passed to minmax/zscore (e.g., lower_clip=0.01, upper_clip=0.99).
    """
    out = df.copy()
    for m in metrics:
        col = f'n_{m}'
        out[col] = np.nan
        for year, g in out.groupby('year'):
            idx = g.index
            s = g[m]
            if method == 'minmax':
                normed = minmax(s, lower_clip=kwargs.get('lower_clip'), upper_clip=kwargs.get('upper_clip'))
            else:
                normed = zscore(s, winsorize=kwargs.get('winsorize'))
            out.loc[idx, col] = normed.values
    return out

# ----------------------
# Composite score
# ----------------------

def build_composite(df_norm: pd.DataFrame, metrics, weights=None, name: str='economic_composite') -> pd.DataFrame:
    """
    Computes weighted mean of normalized metrics per country-year.
    'metrics' are the *original* metric names; function expects normalized columns 'n_<metric>' to exist.
    """
    if weights is None:
        weights = {m:1.0 for m in metrics}
    # ensure normalized columns exist
    for m in metrics:
        if f'n_{m}' not in df_norm.columns:
            raise ValueError(f"Missing normalized column n_{m}. Run normalize_by_year first.")
    W = np.array([weights[m] for m in metrics], dtype=float)
    W = W / W.sum()
    ncols = [f'n_{m}' for m in metrics]
    df = df_norm.copy()
    df[name] = df[ncols].mul(W, axis=1).sum(axis=1, min_count=len(ncols))
    return df

# ----------------------
# Visualizations (matplotlib-only; each chart has its own figure)
# ----------------------

def plot_country_trends(df: pd.DataFrame, country_iso3: str) -> None:
    """Plots time series for the three small scores and the composite for a given country."""
    sub = df[df['country_iso3'] == country_iso3].sort_values('year')
    if sub.empty:
        print(f"No data for {country_iso3}")
        return
    for metric in ['score1a','score2a','score3']:
        if metric in sub.columns:
            plt.figure()
            plt.plot(sub['year'], sub[metric], marker='o')
            plt.title(f"{country_iso3} - {metric} over time")
            plt.xlabel('Year'); plt.ylabel(metric)
            plt.grid(True); plt.tight_layout()
            plt.show()
    if 'economic_composite' in sub.columns:
        plt.figure()
        plt.plot(sub['year'], sub['economic_composite'], marker='o')
        plt.title(f"{country_iso3} - Composite economic score over time")
        plt.xlabel('Year'); plt.ylabel('economic_composite')
        plt.grid(True); plt.tight_layout()
        plt.show()

def plot_top_countries(df: pd.DataFrame, year: int, metric: str='economic_composite', top_n: int=15) -> None:
    """Bar chart of top countries for a given metric and year."""
    sub = df[df['year'] == year].dropna(subset=[metric])
    if sub.empty:
        print(f"No data for year={year}")
        return
    sub = sub.sort_values(metric, ascending=False).head(top_n)
    plt.figure()
    plt.barh(sub['country_iso3'], sub[metric])
    plt.gca().invert_yaxis()
    plt.title(f"Top {top_n} countries by {metric} in {year}")
    plt.xlabel(metric); plt.ylabel('country_iso3')
    plt.tight_layout()
    plt.show()

def plot_metric_distribution(df: pd.DataFrame, metric: str, year: int) -> None:
    """Histogram for a given metric in a specified year."""
    sub = df[df['year'] == year].dropna(subset=[metric])
    if sub.empty:
        print(f"No data for {metric} in {year}")
        return
    plt.figure()
    plt.hist(sub[metric], bins=20)
    plt.title(f"Distribution of {metric} in {year}")
    plt.xlabel(metric); plt.ylabel('count')
    plt.tight_layout()
    plt.show()

# ----------------------
# Example pipeline (not executed on import)
# ----------------------

def example_pipeline(data_dir: str='data', norm_method: str='minmax') -> pd.DataFrame:
    """Example end-to-end usage. Adjust paths to your data folder.
    Returns a DataFrame with the normalized small scores and the composite.
    """
    p1 = os.path.join(data_dir, 'score1a_country_year.csv')
    p2 = os.path.join(data_dir, 'score2a_country_year.csv')
    p3 = os.path.join(data_dir, 'score3_country_year.csv')
    df = load_small_scores(p1, p2, p3)
    dfn = normalize_by_year(df, metrics=['score1a','score2a','score3'], method=norm_method, lower_clip=0.01, upper_clip=0.99)
    comp = build_composite(dfn, metrics=['score1a','score2a','score3'], weights={'score1a':1,'score2a':1,'score3':1})
    return comp

if __name__ == '__main__':
    pass
