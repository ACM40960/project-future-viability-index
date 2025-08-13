
"""
coal_scores_dashboard.py

Compute coal sector composite sub-scores per country and a combined emissions score.
Also provides normalization utilities and basic matplotlib visualizations.

Inputs expected (CSV files with the following columns):
- total_emissions_intensity.csv:
  ['Entity','Code','Year','Coal_CO2_Emissions','Coal_Production_TWh','Emissions_Intensity_tCO2_per_TWh']
- absolute_global_emissions_share.csv:
  ['Entity','Code','Year','Coal_CO2_Emissions','Global_Share']
- policy_exempt_emissions.csv:
  ['Entity','Code','Year','Share_Covered_Carbon_Price','Policy_Exempt_Emissions']  # coverage is a FRACTION (0-1)
- lifecycle_emissions_coverage.csv:
  ['Entity','Code','Year','Lifecycle_Emissions_Coverage']  # fraction 0-1
- historical_emissions_debt.csv:
  ['Entity','Code','Cumulative_Emissions_1850_2023','First_Year']
- carbon_abatement_readiness.csv:
  ['Entity','Code','Year','Share_CarbonTax','Carbon_Abatement_Readiness']  # fraction 0-1

All computations are country-by-country and align on ISO3 'Code'.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Standardize column names (strip spaces)
    df.columns = [c.strip() for c in df.columns]
    return df

def load_inputs(
    root: Path
) -> dict:
    """Load the six pre-computed datasets from disk."""
    files = {
        "intensity": root / "total_emissions_intensity.csv",
        "global_share": root / "absolute_global_emissions_share.csv",
        "policy_exempt": root / "policy_exempt_emissions.csv",
        "lifecycle_cov": root / "lifecycle_emissions_coverage.csv",
        "historical_debt": root / "historical_emissions_debt.csv",
        "abatement_ready": root / "carbon_abatement_readiness.csv",
    }
    dfs = {k: _read_csv(v) for k, v in files.items()}
    return dfs

def compute_small_scores(dfs: dict) -> pd.DataFrame:
    """
    Return a single DataFrame keyed by ISO3 'Code' with the six raw sub-metrics.
    """
    # Start from a country list
    countries = (
        dfs["global_share"][["Entity", "Code"]]
        .drop_duplicates(subset=["Code"])
        .dropna(subset=["Code"])
    ).copy()

    # Merge the metrics
    out = countries.copy()

    # 1) Emissions intensity (tCO2/TWh) - lower is better
    inten = dfs["intensity"][["Code", "Emissions_Intensity_tCO2_per_TWh"]].drop_duplicates("Code")
    out = out.merge(inten, on="Code", how="left")

    # 2) Absolute global share of coal emissions (0-1) - lower is better
    gshare = dfs["global_share"][["Code", "Global_Share"]].drop_duplicates("Code")
    out = out.merge(gshare, on="Code", how="left")

    # 3) Policy-exempt emissions (fraction uncovered = 1 - coverage) - lower is better
    pex = dfs["policy_exempt"][["Code", "Policy_Exempt_Emissions"]].drop_duplicates("Code")
    out = out.merge(pex, on="Code", how="left")

    # 4) Lifecycle emissions coverage (fraction covered) - higher is better
    cov = dfs["lifecycle_cov"][["Code", "Lifecycle_Emissions_Coverage"]].drop_duplicates("Code")
    out = out.merge(cov, on="Code", how="left")

    # 5) Historical emissions debt (cumulative coal CO2 since 1850) - lower is better
    debt = dfs["historical_debt"][["Code", "Cumulative_Emissions_1850_2023"]].drop_duplicates("Code")
    out = out.merge(debt, on="Code", how="left")

    # 6) Carbon abatement readiness (share under a carbon TAX) - higher is better
    ready = dfs["abatement_ready"][["Code", "Carbon_Abatement_Readiness"]].drop_duplicates("Code")
    out = out.merge(ready, on="Code", how="left")

    # Rename columns to short metric names
    out = out.rename(
        columns={
            "Emissions_Intensity_tCO2_per_TWh": "intensity",
            "Global_Share": "global_share",
            "Policy_Exempt_Emissions": "policy_exempt",
            "Lifecycle_Emissions_Coverage": "lifecycle_coverage",
            "Cumulative_Emissions_1850_2023": "historical_debt",
            "Carbon_Abatement_Readiness": "abatement_readiness",
        }
    )

    return out

def minmax_normalize(series: pd.Series, higher_is_better: bool) -> pd.Series:
    """
    Min-max normalize to [0,1].
    If higher_is_better is False, invert so that higher normalized values still mean better.
    NaNs are preserved.
    """
    s = series.astype(float)
    minv, maxv = s.min(skipna=True), s.max(skipna=True)
    norm = (s - minv) / (maxv - minv) if pd.notnull(minv) and pd.notnull(maxv) and maxv != minv else pd.Series([np.nan]*len(s), index=s.index)
    if not higher_is_better:
        norm = 1 - norm
    return norm

def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce normalized sub-scores in [0,1], where 1 = better performance.
    Directionality:
        - intensity: lower is better
        - global_share: lower is better
        - policy_exempt: lower is better
        - lifecycle_coverage: higher is better
        - historical_debt: lower is better
        - abatement_readiness: higher is better
    """
    out = df.copy()
    out["intensity_n"]           = minmax_normalize(out["intensity"], higher_is_better=False)
    out["global_share_n"]        = minmax_normalize(out["global_share"], higher_is_better=False)
    out["policy_exempt_n"]       = minmax_normalize(out["policy_exempt"], higher_is_better=False)
    out["lifecycle_coverage_n"]  = minmax_normalize(out["lifecycle_coverage"], higher_is_better=True)
    out["historical_debt_n"]     = minmax_normalize(out["historical_debt"], higher_is_better=False)
    out["abatement_readiness_n"] = minmax_normalize(out["abatement_readiness"], higher_is_better=True)
    return out

def composite_score(df_n: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    """
    Compute weighted composite score from normalized sub-scores.
    Default: equal weights across the 6 metrics.
    You may pass a custom weights dict (keys must be the *_n names).  It will be renormalized to sum to 1.
    """
    # default equal weights
    default_w = {
        "intensity_n":           1/6,
        "global_share_n":        1/6,
        "policy_exempt_n":       1/6,
        "lifecycle_coverage_n":  1/6,
        "historical_debt_n":     1/6,
        "abatement_readiness_n": 1/6,
    }
    w = default_w if weights is None else weights.copy()

    # ensure full set
    for k in default_w:
        if k not in w:
            w[k] = default_w[k]
    # renormalize to 1
    total = sum(v for v in w.values() if v is not None)
    if total == 0:
        w = default_w
        total = 1.0
    w = {k: v/total for k, v in w.items()}

    df = df_n.copy()
    df["composite"] = sum(df.get(k, 0).fillna(0) * w[k] for k in w.keys())
    return df, w

# ---------------------- Visualization helpers (matplotlib) ----------------------

def plot_top_countries(df: pd.DataFrame, column: str, top_n: int = 15, title: str | None = None):
    """
    Bar chart of top_n countries by the chosen column.
    """
    data = (
        df.dropna(subset=[column])
          .nlargest(top_n, column)[["Entity", column]]
          .set_index("Entity")
    )
    plt.figure()
    data[column].plot(kind="bar")
    plt.title(title or f"Top {top_n} countries by {column}")
    plt.ylabel(column)
    plt.tight_layout()
    return plt.gcf()

def plot_scatter(df: pd.DataFrame, xcol: str, ycol: str, title: str | None = None):
    """
    Simple scatter of y vs. x.
    """
    sub = df.dropna(subset=[xcol, ycol])
    plt.figure()
    plt.scatter(sub[xcol], sub[ycol])
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.title(title or f"{ycol} vs {xcol}")
    plt.tight_layout()
    return plt.gcf()

def build_dashboard(charts_out_dir: Path, df_comp: pd.DataFrame):
    """
    Produce a small 'dashboard' as a set of PNG charts:
      - Top composite score
      - Top normalized lifecycle coverage
      - Bottom 15 policy-exempt (i.e., best countries after inversion)
      - Scatter: normalized intensity vs normalized lifecycle coverage
    """
    charts_out_dir.mkdir(parents=True, exist_ok=True)

    # Top composite
    fig = plot_top_countries(df_comp, "composite", top_n=15, title="Top composite scores (coal)")
    fig.savefig(charts_out_dir / "top_composite.png")
    plt.close(fig)

    # Top lifecycle coverage (normalized)
    fig = plot_top_countries(df_comp, "lifecycle_coverage_n", top_n=15, title="Best lifecycle coverage (normalized)")
    fig.savefig(charts_out_dir / "top_lifecycle_coverage.png")
    plt.close(fig)

    # Since policy_exempt_n is already oriented (1=better), "top" are actually least exempt
    fig = plot_top_countries(df_comp, "policy_exempt_n", top_n=15, title="Lowest policy-exempt share (normalized)")
    fig.savefig(charts_out_dir / "top_lowest_policy_exempt.png")
    plt.close(fig)

    # Scatter: intensity vs lifecycle coverage (normalized)
    fig = plot_scatter(df_comp, "intensity_n", "lifecycle_coverage_n", title="Intensity (n) vs Lifecycle coverage (n)")
    fig.savefig(charts_out_dir / "scatter_intensity_vs_coverage.png")
    plt.close(fig)

    return charts_out_dir

def run_pipeline(input_dir: Path, outputs_dir: Path, weights: dict | None = None) -> dict:
    """
    Full end‑to‑end pipeline:
      - load six datasets
      - assemble small scores
      - normalize
      - compute composite
      - write outputs to CSV
      - generate simple dashboard PNGs
    Returns dict with paths of main outputs.
    """
    dfs = load_inputs(input_dir)
    raw_scores = compute_small_scores(dfs)
    norm_scores = normalize_scores(raw_scores)
    comp, used_weights = composite_score(norm_scores, weights)

    outputs_dir.mkdir(parents=True, exist_ok=True)
    raw_csv  = outputs_dir / "coal_small_scores_raw.csv"
    norm_csv = outputs_dir / "coal_small_scores_normalized.csv"
    comp_csv = outputs_dir / "coal_composite_scores.csv"

    raw_scores.to_csv(raw_csv, index=False)
    norm_scores.to_csv(norm_csv, index=False)
    comp.to_csv(comp_csv, index=False)

    charts_dir = outputs_dir / "charts"
    build_dashboard(charts_dir, comp)

    return {
        "raw_csv": raw_csv,
        "norm_csv": norm_csv,
        "composite_csv": comp_csv,
        "charts_dir": charts_dir,
        "weights": used_weights,
    }

if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser(description="Compute coal composite scores and a simple dashboard.")
    p.add_argument("--inputs", type=str, required=True, help="Folder containing the six CSV input files")
    p.add_argument("--out", type=str, required=True, help="Output folder")
    p.add_argument("--weights", type=str, default=None, help="JSON dict mapping normalized metric names to weights")
    args = p.parse_args()

    weights = json.loads(args.weights) if args.weights else None
    res = run_pipeline(Path(args.inputs), Path(args.out), weights)
    print("Wrote:", res)
