
"""
Ecological Scores – computation & visualization

Inputs (CSV paths; change as needed):
- ecological_score1_coal_all.csv  (deforestation, land mined, restoration ratio)
- ecological_score2_coal_all.csv  (ocean acid load, etc. – numeric columns)
- ecological_score3_coal_all.csv  (SO2, NOx, coal ash)
Each file must contain a 'Country' column and numeric metric columns.

Outputs:
- ecological_scores_country.csv (sub-scores & composite by country)
- PNG charts in ./ecological_charts/

How scores are built (defaults, can be overridden):
- Higher values are treated as “worse” (more ecological impact), EXCEPT any
  column name containing one of the following tokens is treated as better-is-higher
  and inverted during normalization: ['restoration', 'reuse', 'treated', 'reclaimed']

Normalization:
- Min–max scaled to 0–100 across available countries for each metric.
- Optionally pass method='zscore' to normalize() for z-score then min–max mapping.

Composite:
- Simple unweighted mean of the available sub-scores for Ecological Score 1–3.
- Overall Ecological Composite = mean of the three sub-score composites.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BETTER_TOKENS = ['restoration', 'reuse', 'treated', 'reclaimed']

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
    """Return True if higher is worse; False if higher is better and should be inverted."""
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
        higher_is_worse = infer_direction(c)
        out[c + '_score'] = normalize(df[c], higher_is_worse=higher_is_worse, method=method)
    # composite for this file
    score_cols = [c for c in out.columns if c.endswith('_score')]
    out['composite'] = out[score_cols].mean(axis=1, skipna=True)
    return out

def join_on_country(frames: list[pd.DataFrame]) -> pd.DataFrame:
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on='Country', how='outer', suffixes=('', '_dup'))
        dup_cols = [c for c in out.columns if c.endswith('_dup')]
        if dup_cols:
            out.drop(columns=dup_cols, inplace=True)
    return out

def compute_ecological(
    file1='ecological_score1_coal_all.csv',
    file2='ecological_score2_coal_all.csv',
    file3='ecological_score3_coal_all.csv',
    norm_method='minmax',
    output_csv='ecological_scores_country.csv',
    charts_dir='ecological_charts'
) -> pd.DataFrame:
    s1 = score_file(file1, method=norm_method).rename(columns={'composite':'Eco1_composite'})
    s2 = score_file(file2, method=norm_method).rename(columns={'composite':'Eco2_composite'})
    s3 = score_file(file3, method=norm_method).rename(columns={'composite':'Eco3_composite'})
    eco = join_on_country([s1, s2, s3])
    eco['Ecological_Composite'] = eco[['Eco1_composite','Eco2_composite','Eco3_composite']].mean(axis=1, skipna=True)

    os.makedirs(charts_dir, exist_ok=True)
    eco_sorted = eco.sort_values('Ecological_Composite', ascending=False).head(20)
    # Top 20 bar
    plt.figure(figsize=(10,6))
    plt.bar(eco_sorted['Country'], eco_sorted['Ecological_Composite'])
    plt.xticks(rotation=70, ha='right')
    plt.ylabel('Ecological Composite (0–100)')
    plt.title('Top 20 – Ecological Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'top20_ecological_composite.png'))
    plt.close()

    # Distribution
    plt.figure(figsize=(8,5))
    plt.hist(eco['Ecological_Composite'].dropna(), bins=20)
    plt.xlabel('Ecological Composite (0–100)')
    plt.ylabel('Number of countries')
    plt.title('Distribution – Ecological Composite')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'ecological_distribution.png'))
    plt.close()

    eco.to_csv(output_csv, index=False)
    return eco

if __name__ == '__main__':
    compute_ecological()
