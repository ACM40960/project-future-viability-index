# scores/utils.py - Utility Functions for FVI Scoring
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional
from scipy import stats

# Standard country name mapping for consistency
COUNTRY_MAPPING = {
    "USA": "United States",
    "CHN": "China", 
    "IND": "India",
    "DEU": "Germany",
    "RUS": "Russia",
    "KOR": "South Korea",
    "GBR": "United Kingdom",
    "FRA": "France",
    "JPN": "Japan",
    "BRA": "Brazil",
    "CAN": "Canada",
    "AUS": "Australia",
    "SAU": "Saudi Arabia",
    "ZAF": "South Africa",
    "ITA": "Italy",
    "ESP": "Spain",
    "NLD": "Netherlands",
    "POL": "Poland",
    "IDN": "Indonesia",
    "TUR": "Turkey",
    "MEX": "Mexico",
    "IRN": "Iran",
    "THA": "Thailand",
    "ARE": "United Arab Emirates",
    "EGY": "Egypt",
    "ISR": "Israel",
    "NOR": "Norway",
    "ARG": "Argentina",
    "IRL": "Ireland",
    "MYS": "Malaysia",
    "BGD": "Bangladesh",
    "PHL": "Philippines",
    "SGP": "Singapore",
    "CHL": "Chile",
    "FIN": "Finland",
    "DNK": "Denmark",
    "NZL": "New Zealand",
    "SWE": "Sweden",
    "AUT": "Austria",
    "ISL": "Iceland",
    "BEL": "Belgium",
    "CHE": "Switzerland"
}

def standardize_country_name(name: Union[str, None]) -> Optional[str]:
    """
    Convert ISO codes, abbreviations to full country names
    
    Args:
        name: Country name or code
    
    Returns:
        Standardized country name or None if invalid
    """
    if pd.isna(name) or name is None:
        return None
    
    name = str(name).strip()
    
    # Try direct mapping first
    if name.upper() in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[name.upper()]
    
    # Common aliases and variations
    aliases = {
        "UK": "United Kingdom",
        "US": "United States",
        "USA": "United States",
        "United States of America": "United States",
        "S. Korea": "South Korea",
        "Viet Nam": "Vietnam",
        "Congo": "Democratic Republic of the Congo",
        "Ivory Coast": "Côte d'Ivoire",
        "Russian Federation": "Russia",
        "Iran, Islamic Rep.": "Iran",
        "Egypt, Arab Rep.": "Egypt"
    }
    
    return aliases.get(name, name)

def normalize_series(series: pd.Series, higher_is_better: bool = True, 
                    method: str = "min_max") -> pd.Series:
    """
    Normalize a pandas Series to 0-100 scale
    
    Args:
        series: Input series to normalize
        higher_is_better: If True, higher values get higher scores
        method: Normalization method ('min_max', 'z_score', 'percentile')
    
    Returns:
        Normalized series with values 0-100
    """
    s = pd.to_numeric(series, errors='coerce').dropna()
    
    if s.empty:
        return pd.Series([50] * len(series), index=series.index)
    
    if method == "min_max":
        min_val, max_val = s.min(), s.max()
        if min_val == max_val:
            normalized = pd.Series([50] * len(s), index=s.index)
        else:
            normalized = 100 * (s - min_val) / (max_val - min_val)
    
    elif method == "z_score":
        # Z-score normalization, then scale to 0-100
        z_scores = stats.zscore(s)
        # Map z-scores to 0-100 (assuming ±3 sigma range)
        normalized = 50 + (z_scores * 50 / 3)
        normalized = normalized.clip(0, 100)
    
    elif method == "percentile":
        # Percentile-based normalization
        normalized = pd.Series([stats.percentileofscore(s, x) for x in s], index=s.index)
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    # Invert if higher values should be worse (typical for coal viability)
    if not higher_is_better:
        normalized = 100 - normalized
    
    # Reindex to original series, fill missing with 50 (neutral score)
    result = pd.Series(50, index=series.index)
    result.update(normalized)
    
    return result

def normalize_score(value: Union[float, int, None], min_val: float = 0, 
                   max_val: float = 100, default: float = 50.0) -> float:
    """
    Simple normalization of a single value to 0-100 range
    
    Args:
        value: Value to normalize
        min_val: Minimum value in original scale
        max_val: Maximum value in original scale
        default: Default value for missing/invalid inputs
    
    Returns:
        Normalized value in 0-100 range
    """
    if pd.isna(value) or value is None:
        return default
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return default
    
    if min_val == max_val:
        return default
    
    normalized = 100 * (value - min_val) / (max_val - min_val)
    return max(0.0, min(100.0, normalized))

def validate_data(df: pd.DataFrame, required_columns: List[str] = None) -> Dict:
    """
    Validate DataFrame structure and data quality
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        'is_valid': True,
        'issues': [],
        'summary': {}
    }
    
    if df.empty:
        validation['is_valid'] = False
        validation['issues'].append("DataFrame is empty")
        return validation
    
    # Check required columns
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            validation['issues'].append(f"Missing required columns: {missing_cols}")
    
    # Check data types
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    text_cols = df.select_dtypes(include=['object']).columns
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.any():
        high_missing = missing_counts[missing_counts > len(df) * 0.5]
        if not high_missing.empty:
            validation['issues'].append(f"High missing values (>50%): {high_missing.to_dict()}")
    
    # Check for duplicate rows
    if df.duplicated().any():
        validation['issues'].append(f"Found {df.duplicated().sum()} duplicate rows")
    
    # Check numeric ranges
    for col in numeric_cols:
        col_stats = df[col].describe()
        if col_stats['std'] == 0:
            validation['issues'].append(f"Column {col} has no variation (all same value)")
    
    # Summary statistics
    validation['summary'] = {
        'rows': len(df),
        'columns': len(df.columns),
        'numeric_columns': len(numeric_cols),
        'text_columns': len(text_cols),
        'missing_values': missing_counts.sum(),
        'duplicate_rows': df.duplicated().sum()
    }
    
    if validation['issues']:
        validation['is_valid'] = False
    
    return validation

def validate_score_range(score: Union[float, int]) -> float:
    """
    Ensure score is in valid 0-100 range
    
    Args:
        score: Score value to validate
    
    Returns:
        Score clamped to 0-100 range
    """
    if pd.isna(score):
        return 50.0
    
    try:
        score = float(score)
        return max(0.0, min(100.0, score))
    except (ValueError, TypeError):
        return 50.0

def calculate_weighted_average(scores_dict: Dict[str, float], 
                              weights_dict: Dict[str, float]) -> float:
    """
    Calculate weighted average of scores
    
    Args:
        scores_dict: Dictionary mapping keys to scores
        weights_dict: Dictionary mapping same keys to weights
    
    Returns:
        Weighted average score
    """
    if not scores_dict or not weights_dict:
        return 0.0
    
    # Find common keys
    common_keys = set(scores_dict.keys()) & set(weights_dict.keys())
    
    if not common_keys:
        return 0.0
    
    total_weight = sum(weights_dict[key] for key in common_keys)
    
    if total_weight == 0:
        return 0.0
    
    weighted_sum = sum(
        scores_dict[key] * weights_dict[key] 
        for key in common_keys 
        if pd.notna(scores_dict[key])
    )
    
    return weighted_sum / total_weight

def get_latest_data_by_country(df: pd.DataFrame, country_col: str = 'country_name', 
                              year_col: str = 'year') -> pd.DataFrame:
    """
    Get latest year data for each country
    
    Args:
        df: DataFrame with country and year columns
        country_col: Name of country column
        year_col: Name of year column
    
    Returns:
        DataFrame with latest data for each country
    """
    if df.empty or country_col not in df.columns:
        return df
    
    if year_col in df.columns:
        # Get latest year for each country
        latest_df = df.loc[df.groupby(country_col)[year_col].idxmax()]
    else:
        # If no year column, just remove duplicates keeping last
        latest_df = df.drop_duplicates(subset=[country_col], keep='last')
    
    return latest_df.reset_index(drop=True)

def handle_outliers(series: pd.Series, method: str = "clip", 
                   percentiles: tuple = (5, 95)) -> pd.Series:
    """
    Handle outliers in a pandas Series
    
    Args:
        series: Input series
        method: Method to handle outliers ('clip', 'remove', 'winsorize')
        percentiles: Percentile bounds for outlier detection
    
    Returns:
        Series with outliers handled
    """
    if series.empty:
        return series
    
    # Calculate percentile bounds
    lower_bound = series.quantile(percentiles[0] / 100)
    upper_bound = series.quantile(percentiles[1] / 100)
    
    if method == "clip":
        return series.clip(lower_bound, upper_bound)
    
    elif method == "remove":
        mask = (series >= lower_bound) & (series <= upper_bound)
        return series[mask]
    
    elif method == "winsorize":
        # Replace outliers with boundary values
        result = series.copy()
        result[series < lower_bound] = lower_bound
        result[series > upper_bound] = upper_bound
        return result
    
    else:
        return series

def create_country_mapping(df: pd.DataFrame, country_list: List[str]) -> Dict[str, str]:
    """
    Create mapping between countries in data and target country list
    
    Args:
        df: DataFrame with country data
        country_list: Target list of countries
    
    Returns:
        Dictionary mapping data countries to target countries
    """
    mapping = {}
    
    # Find country column
    country_cols = [col for col in df.columns if 'country' in col.lower()]
    if not country_cols:
        return mapping
    
    country_col = country_cols[0]
    data_countries = df[country_col].dropna().unique()
    
    # Direct matches
    for data_country in data_countries:
        for target_country in country_list:
            if data_country.lower() == target_country.lower():
                mapping[data_country] = target_country
                break
            # Check standardized names
            elif standardize_country_name(data_country) == target_country:
                mapping[data_country] = target_country
                break
    
    return mapping

def interpolate_missing_values(df: pd.DataFrame, method: str = "linear") -> pd.DataFrame:
    """
    Interpolate missing values in DataFrame
    
    Args:
        df: DataFrame with missing values
        method: Interpolation method ('linear', 'forward', 'backward')
    
    Returns:
        DataFrame with interpolated values
    """
    if df.empty:
        return df
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    result = df.copy()
    
    for col in numeric_cols:
        if method == "linear":
            result[col] = result[col].interpolate(method='linear')
        elif method == "forward":
            result[col] = result[col].fillna(method='ffill')
        elif method == "backward":
            result[col] = result[col].fillna(method='bfill')
    
    return result

if __name__ == "__main__":
    # Test utility functions
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_series = pd.Series([10, 20, 30, 40, 50])
    
    print("Testing normalization:")
    normalized = normalize_series(test_series)
    print(f"Original: {test_series.tolist()}")
    print(f"Normalized: {normalized.tolist()}")
    
    print("\nTesting country standardization:")
    countries = ["USA", "CHN", "DEU", "InvalidCountry"]
    for country in countries:
        standardized = standardize_country_name(country)
        print(f"{country} -> {standardized}")
