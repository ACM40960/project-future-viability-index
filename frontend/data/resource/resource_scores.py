
"""
Resource Scores – computation & visualization

Inputs:
- resource_score1_coal_all.csv  (land use intensity, #plants, R/P ratio etc.)
- resource_score2_coal_all.csv  (water use, share of global water use)
- resource_score3_coal_all.csv  (extraction share, ash waste, waste/use ratio)

Assumptions about direction (higher-is-worse):
- By default, higher = worse for resource pressure.
- Columns containing tokens ['restored','replenish','efficiency'] are treated as better.

Normalization: min–max to 0–100 per metric.
Composite: mean of sub-scores inside each file; Resource Composite = mean of the three.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BETTER_TOKENS = ['restored','replenish','efficiency']

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

def infer_direction(colname: str) -> bool:
    name = colname.lower()
    for token in BETTER_TOKENS:
        if token in name:
            return False
    return True

def score_file(path: str, method: str = 'minmax') -> pd.DataFrame:
    df = pd.read_csv(path)
    num_cols = [c for c in df.columns if c.lower() != 'country']
    out = df[['Country']].copy()
    for c in num_cols:
        out[c + '_score'] = normalize(df[c], higher_is_worse=infer_direction(c), method=method)
    out['composite'] = out[[c for c in out.columns if c.endswith('_score')]].mean(axis=1, skipna=True)
    return out

def join_on_country(frames):
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on='Country', how='outer')
    return out

def compute_resource(
    file1='resource_score1_coal_all.csv',
    file2='resource_score2_coal_all.csv',
    file3='resource_score3_coal_all.csv',
    norm_method='minmax',
    output_csv='resource_scores_country.csv',
    charts_dir='resource_charts'
) -> pd.DataFrame:
    r1 = score_file(file1, method=norm_method).rename(columns={'composite':'Res1_composite'})
    r2 = score_file(file2, method=norm_method).rename(columns={'composite':'Res2_composite'})
    r3 = score_file(file3, method=norm_method).rename(columns={'composite':'Res3_composite'})
    res = join_on_country([r1, r2, r3])
    res['Resource_Composite'] = res[['Res1_composite','Res2_composite','Res3_composite']].mean(axis=1, skipna=True)

    os.makedirs(charts_dir, exist_ok=True)
    top = res.sort_values('Resource_Composite', ascending=False).head(20)
    plt.figure(figsize=(10,6))
    plt.bar(top['Country'], top['Resource_Composite'])
    plt.xticks(rotation=70, ha='right')
    plt.ylabel('Resource Composite (0–100)')
    plt.title('Top 20 – Resource Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'top20_resource_composite.png'))
    plt.close()

    plt.figure(figsize=(8,5))
    plt.hist(res['Resource_Composite'].dropna(), bins=20)
    plt.xlabel('Resource Composite (0–100)')
    plt.ylabel('Number of countries')
    plt.title('Distribution – Resource Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'resource_distribution.png'))
    plt.close()

    res.to_csv(output_csv, index=False)
    return res

if __name__ == '__main__':
    compute_resource()
