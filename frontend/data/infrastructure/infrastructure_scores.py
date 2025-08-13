
"""
Infrastructure / Asset Restructuring Scores – computation & visualization

Inputs (as available):
- infra_asset_repurposing_score1_coal_all.csv  (Operating, Under_Construction, PreConstruction)
- infra_asset_repurposing_score2_coal_all.csv  (reuse %, transition speed, expert score, circularity %, community %)
- infra_asset_repurposing_score3_coal_all.csv  (cleanup cost, hazard %, time horizon)
- infra_asset_repurposing_score4_coal_all.csv  (public reclamation, human need, land feasibility, rewilding, demolition vs retrofit)
- infra_asset_repurposing_score5_coal_all.csv  (root causes qualitative %)

Scoring approach (robust to missing fields):
- For #1, we compute:
    Future_Risk_Index = (Under_Construction + PreConstruction) / Total_Units
    Fleet_Size_Pressure = Operating (normalized)
  Composite_1 = mean(normalized(Future_Risk_Index), normalized(Fleet_Size_Pressure))
- For #2–#5, any numeric fields found are normalized (higher = better for reuse/circularity/community;
  higher = worse for hazard/cost/time). If a file has no numeric fields, its composite is NaN.
- Overall Infrastructure Composite = mean of available file composites.

Outputs:
- infrastructure_scores_country.csv
- PNG charts in ./infrastructure_charts/
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

POSITIVE_TOKENS = ['reuse','circular','community','feasibility','public']

def normalize(series: pd.Series, higher_is_worse: bool = True, method: str = 'minmax') -> pd.Series:
    s = pd.to_numeric(series, errors='coerce')
    if s.dropna().empty:
        return pd.Series(np.nan, index=s.index)
    if method == 'zscore':
        z = (s - s.mean()) / (s.std(ddof=0) if s.std(ddof=0) else 1.0)
        mi, ma = z.min(), z.max()
        scaled = (z - mi) / (ma - mi) if ma != mi else pd.Series(0.5, index=s.index)
    else:
        mi, ma = s.min(), s.max()
        scaled = (s - mi) / (ma - mi) if ma != mi else pd.Series(0.5, index=s.index)
    if not higher_is_worse:
        scaled = 1 - scaled
    return 100 * scaled

def score_infra1(path: str, method: str = 'minmax') -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.copy()
    # Try to identify columns by common names
    colmap = {c.lower(): c for c in df.columns}
    op = next((df[colmap[k]] for k in colmap if 'operat' in k), None)
    uc = next((df[colmap[k]] for k in colmap if 'under' in k), None)
    pc = next((df[colmap[k]] for k in colmap if 'pre' in k), None)
    out = df[['Country']].copy()
    if op is not None and uc is not None and pc is not None:
        total_units = pd.to_numeric(op, errors='coerce').fillna(0) + pd.to_numeric(uc, errors='coerce').fillna(0) + pd.to_numeric(pc, errors='coerce').fillna(0)
        future_risk = (pd.to_numeric(uc, errors='coerce').fillna(0) + pd.to_numeric(pc, errors='coerce').fillna(0)) / total_units.replace({0: np.nan})
        out['Future_Risk_Index_score'] = normalize(future_risk, higher_is_worse=True, method=method)
        out['Fleet_Size_Pressure_score'] = normalize(op, higher_is_worse=True, method=method)
        out['composite'] = out[['Future_Risk_Index_score','Fleet_Size_Pressure_score']].mean(axis=1, skipna=True)
    else:
        # fallback: normalize all numeric columns (higher worse)
        num_cols = [c for c in df.columns if c.lower()!='country']
        for c in num_cols:
            out[c + '_score'] = normalize(df[c], higher_is_worse=True, method=method)
        out['composite'] = out[[c for c in out.columns if c.endswith('_score')]].mean(axis=1, skipna=True)
    return out

def score_generic(path: str, method: str = 'minmax') -> pd.DataFrame:
    df = pd.read_csv(path)
    out = df[['Country']].copy()
    found = False
    for c in df.columns:
        if c.lower() == 'country':
            continue
        # decide direction: positive tokens imply higher=better (invert)
        higher_is_worse = True
        name = c.lower()
        for t in POSITIVE_TOKENS:
            if t in name:
                higher_is_worse = False
                break
        out[c + '_score'] = normalize(df[c], higher_is_worse=higher_is_worse, method=method)
        found = True
    out['composite'] = out[[c for c in out.columns if c.endswith('_score')]].mean(axis=1, skipna=True) if found else pd.Series(np.nan, index=out.index)
    return out

def compute_infrastructure(
    file1='infra_asset_repurposing_score1_coal_all.csv',
    file2='infra_asset_repurposing_score2_coal_all.csv',
    file3='infra_asset_repurposing_score3_coal_all.csv',
    file4='infra_asset_repurposing_score4_coal_all.csv',
    file5='infra_asset_repurposing_score5_coal_all.csv',
    norm_method='minmax',
    output_csv='infrastructure_scores_country.csv',
    charts_dir='infrastructure_charts'
) -> pd.DataFrame:
    s1 = score_infra1(file1, method=norm_method).rename(columns={'composite':'Infra1_composite'})
    s2 = score_generic(file2, method=norm_method).rename(columns={'composite':'Infra2_composite'})
    s3 = score_generic(file3, method=norm_method).rename(columns={'composite':'Infra3_composite'})
    s4 = score_generic(file4, method=norm_method).rename(columns={'composite':'Infra4_composite'})
    s5 = score_generic(file5, method=norm_method).rename(columns={'composite':'Infra5_composite'})
    infra = s1.merge(s2, on='Country', how='outer')\
              .merge(s3, on='Country', how='outer')\
              .merge(s4, on='Country', how='outer')\
              .merge(s5, on='Country', how='outer')
    infra['Infrastructure_Composite'] = infra[['Infra1_composite','Infra2_composite','Infra3_composite','Infra4_composite','Infra5_composite']].mean(axis=1, skipna=True)

    os.makedirs(charts_dir, exist_ok=True)
    top = infra.sort_values('Infrastructure_Composite', ascending=False).head(20)
    plt.figure(figsize=(10,6))
    plt.bar(top['Country'], top['Infrastructure_Composite'])
    plt.xticks(rotation=70, ha='right')
    plt.ylabel('Infrastructure Composite (0–100)')
    plt.title('Top 20 – Infrastructure Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'top20_infrastructure_composite.png'))
    plt.close()

    plt.figure(figsize=(8,5))
    plt.hist(infra['Infrastructure_Composite'].dropna(), bins=20)
    plt.xlabel('Infrastructure Composite (0–100)')
    plt.ylabel('Number of countries')
    plt.title('Distribution – Infrastructure Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'infrastructure_distribution.png'))
    plt.close()

    infra.to_csv(output_csv, index=False)
    return infra

if __name__ == '__main__':
    compute_infrastructure()
