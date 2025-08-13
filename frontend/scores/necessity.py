# scores/necessity.py - Necessity Scoring for FVI System
"""
Necessity scoring system for coal industry dependency assessment

Evaluates how necessary coal is for a country based on:
1. Energy Security - dependence on coal for reliable energy
2. Economic Dependency - jobs and economic contribution from coal
3. Industrial Requirements - industrial processes requiring coal
4. Alternative Availability - feasibility of alternatives
5. Strategic Importance - national energy strategy role

Higher scores indicate greater necessity (better for coal viability).
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from .utils import (
    normalize_score, 
    validate_data, 
    get_latest_data_by_country,
    standardize_country_name
)

def calculate_necessity_score(data_dict: Dict, country_list: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate necessity scores for coal industry dependency
    
    Args:
        data_dict: Dictionary containing necessity datasets
        country_list: List of countries to calculate scores for
    
    Returns:
        pd.Series: Necessity scores by country (0-100, higher = greater necessity)
    """
    
    # Load necessity data
    necessity_data = _load_necessity_data(data_dict)
    
    if not necessity_data:
        logging.warning("No necessity data found, using fallback scores")
        return _fallback_necessity_scores(country_list)
    
    # Get country list from data if not provided
    if country_list is None:
        country_list = _extract_countries_from_data(necessity_data)
    
    # Calculate necessity scores based on available data
    scores = _calculate_necessity_scores(necessity_data, country_list)
    
    logging.info(f"Calculated necessity scores for {len(scores)} countries")
    return scores

def _load_necessity_data(data_dict: Dict) -> Dict[str, pd.DataFrame]:
    """
    Load and validate necessity datasets
    
    Args:
        data_dict: Dictionary containing necessity datasets
    
    Returns:
        Dictionary of validated DataFrames
    """
    necessity_data = {}
    
    for key, dataset in data_dict.items():
        if isinstance(dataset, pd.DataFrame) and not dataset.empty:
            # Clean and validate dataset
            df = dataset.copy()
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Basic validation
            validation = validate_data(df)
            if validation['is_valid'] or len(validation['issues']) <= 2:
                necessity_data[key] = df
                logging.info(f"Loaded necessity dataset '{key}' with {len(df)} rows")
            else:
                logging.warning(f"Skipped invalid dataset '{key}': {validation['issues']}")
    
    return necessity_data

def _extract_countries_from_data(data_dict: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Extract unique countries from necessity datasets
    
    Args:
        data_dict: Dictionary of DataFrames
    
    Returns:
        List of unique country names
    """
    countries = set()
    
    for df in data_dict.values():
        # Look for country columns
        country_cols = [col for col in df.columns if 'country' in col]
        
        for col in country_cols:
            if col in df.columns:
                country_names = df[col].dropna().unique()
                for name in country_names:
                    standardized = standardize_country_name(name)
                    if standardized:
                        countries.add(standardized)
    
    return sorted(list(countries))

def _calculate_necessity_scores(data_dict: Dict[str, pd.DataFrame], 
                               country_list: List[str]) -> pd.Series:
    """
    Calculate necessity scores based on available data
    
    Args:
        data_dict: Dictionary of necessity DataFrames
        country_list: List of countries to score
    
    Returns:
        Series of necessity scores
    """
    scores = {}
    
    # Use the best available dataset
    if len(data_dict) == 1:
        # Single comprehensive dataset
        df = list(data_dict.values())[0]
        scores = _calculate_from_single_dataset(df, country_list)
    
    else:
        # Multiple datasets - combine scores
        component_scores = {}
        
        for dataset_name, df in data_dict.items():
            dataset_scores = _calculate_from_single_dataset(df, country_list)
            if not dataset_scores.empty:
                component_scores[dataset_name] = dataset_scores
        
        # Aggregate component scores
        scores = _aggregate_necessity_scores(component_scores, country_list)
    
    return pd.Series(scores)

def _calculate_from_single_dataset(df: pd.DataFrame, country_list: List[str]) -> pd.Series:
    """
    Calculate necessity scores from a single dataset
    
    Args:
        df: Necessity dataset
        country_list: List of countries
    
    Returns:
        Series of scores
    """
    scores = {}
    
    # Get latest data for each country
    latest_df = get_latest_data_by_country(df)
    
    # Find country column
    country_cols = [col for col in latest_df.columns if 'country' in col]
    if not country_cols:
        logging.warning("No country column found in necessity data")
        return pd.Series(scores)
    
    country_col = country_cols[0]
    
    for country in country_list:
        country_data = latest_df[latest_df[country_col] == country]
        
        if country_data.empty:
            # Try standardized name matching
            for data_country in latest_df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = latest_df[latest_df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            # Calculate necessity based on available columns
            necessity_components = []
            
            # Pre-calculated necessity scores (highest priority)
            if 'necessity_score1' in latest.index:
                necessity_score1 = latest['necessity_score1']
                if pd.notna(necessity_score1):
                    # Convert to 0-100 scale (assuming it's 0-1 scale)
                    normalized_score = necessity_score1 * 100 if necessity_score1 <= 1.0 else necessity_score1
                    necessity_components.append(normalized_score * 0.4)  # 40% weight
            
            # Energy fulfillment score
            if 'necessity_energy_fulfillment_score' in latest.index:
                energy_score = latest['necessity_energy_fulfillment_score']
                if pd.notna(energy_score):
                    necessity_components.append(energy_score * 0.2)  # 20% weight
            
            # Health score
            if 'necessity_health_score' in latest.index:
                health_score = latest['necessity_health_score']
                if pd.notna(health_score):
                    necessity_components.append(health_score * 0.2)  # 20% weight
            
            # Education score  
            if 'necessity_education_score' in latest.index:
                education_score = latest['necessity_education_score']
                if pd.notna(education_score):
                    necessity_components.append(education_score * 0.1)  # 10% weight
            
            # Coal jobs (economic dependency)
            if 'jobs_coal_estimated' in latest.index:
                coal_jobs = latest['jobs_coal_estimated']
                if pd.notna(coal_jobs):
                    # Normalize coal jobs (higher jobs = higher necessity)
                    job_score = normalize_score(coal_jobs, 0, 3000000)  # Max ~3M jobs globally
                    necessity_components.append(job_score * 0.05)  # 5% weight
            
            # Electricity from coal (basic necessity indicator)
            if 'share_electricity_coal_pct' in latest.index:
                coal_electricity = latest['share_electricity_coal_pct']
                if pd.notna(coal_electricity):
                    necessity_components.append(coal_electricity * 0.05)  # 5% weight
            
            # Calculate weighted necessity score
            if necessity_components:
                necessity_score = sum(necessity_components)
                scores[country] = min(100.0, max(0.0, necessity_score))
            else:
                scores[country] = 50.0  # Default neutral score
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _aggregate_necessity_scores(component_scores: Dict[str, pd.Series], 
                              country_list: List[str]) -> Dict[str, float]:
    """
    Aggregate multiple necessity component scores
    
    Args:
        component_scores: Dictionary of component score Series
        country_list: List of countries
    
    Returns:
        Dictionary of aggregated scores
    """
    aggregated_scores = {}
    
    for country in country_list:
        country_scores = []
        
        # Collect scores for this country from all components
        for component_name, scores in component_scores.items():
            if country in scores and pd.notna(scores[country]):
                country_scores.append(scores[country])
        
        if country_scores:
            # Calculate mean of available component scores
            aggregated_scores[country] = np.mean(country_scores)
        else:
            aggregated_scores[country] = 50.0  # Default score
    
    return aggregated_scores

def _fallback_necessity_scores(country_list: Optional[List[str]]) -> pd.Series:
    """
    Provide fallback scores when data is not available
    
    Args:
        country_list: List of countries
    
    Returns:
        Series with fallback scores
    """
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia", 
                       "Indonesia", "South Africa", "Poland"]
    
    # Mock scores based on typical coal necessity patterns
    fallback_scores = {
        "India": 75.0,       # High necessity - large population, industrial needs
        "China": 85.0,       # Very high necessity - massive industrial base
        "Germany": 40.0,     # Low necessity - advanced alternatives
        "USA": 55.0,         # Medium necessity - mixed energy portfolio
        "Australia": 65.0,   # High necessity - mining economy, exports
        "Indonesia": 80.0,   # Very high necessity - developing economy
        "South Africa": 90.0, # Extremely high necessity - coal-dependent economy
        "Poland": 70.0       # High necessity - industrial heritage
    }
    
    scores = {}
    for country in country_list:
        scores[country] = fallback_scores.get(country, 65.0)  # Default: medium-high necessity
    
    logging.info(f"Using fallback necessity scores for {len(scores)} countries")
    return pd.Series(scores)

# Additional helper functions for specific necessity calculations

def calculate_energy_security_dependency(coal_share: float, alternatives_available: float) -> float:
    """
    Calculate energy security dependency on coal
    
    Args:
        coal_share: Percentage of energy from coal
        alternatives_available: Score for alternative energy availability
    
    Returns:
        Energy security dependency score
    """
    if pd.isna(coal_share) or pd.isna(alternatives_available):
        return 50.0
    
    # High coal share + low alternatives = high dependency
    dependency = coal_share * (100 - alternatives_available) / 100
    return normalize_score(dependency, 0, 100)

def calculate_economic_dependency(coal_jobs: float, total_jobs: float, 
                                coal_gdp: float) -> float:
    """
    Calculate economic dependency on coal sector
    
    Args:
        coal_jobs: Number of jobs in coal sector
        total_jobs: Total employment
        coal_gdp: Coal contribution to GDP (%)
    
    Returns:
        Economic dependency score
    """
    dependency_factors = []
    
    # Job dependency
    if pd.notna(coal_jobs) and pd.notna(total_jobs) and total_jobs > 0:
        job_share = (coal_jobs / total_jobs) * 100
        dependency_factors.append(job_share * 20)  # Scale up
    
    # GDP dependency
    if pd.notna(coal_gdp):
        dependency_factors.append(coal_gdp * 10)  # Scale up
    
    if dependency_factors:
        return normalize_score(np.mean(dependency_factors), 0, 100)
    else:
        return 50.0

def calculate_industrial_necessity(steel_production: float, cement_production: float,
                                 power_generation: float) -> float:
    """
    Calculate industrial necessity for coal
    
    Args:
        steel_production: Steel production requiring coal
        cement_production: Cement production requiring coal
        power_generation: Power generation from coal
    
    Returns:
        Industrial necessity score
    """
    necessity_factors = []
    
    # Steel industry (coking coal necessity)
    if pd.notna(steel_production):
        steel_score = normalize_score(steel_production, 0, 1000)  # Normalize to reasonable range
        necessity_factors.append(steel_score)
    
    # Cement industry
    if pd.notna(cement_production):
        cement_score = normalize_score(cement_production, 0, 500)
        necessity_factors.append(cement_score)
    
    # Power generation
    if pd.notna(power_generation):
        power_score = normalize_score(power_generation, 0, 100)
        necessity_factors.append(power_score)
    
    if necessity_factors:
        return np.mean(necessity_factors)
    else:
        return 50.0

if __name__ == "__main__":
    # Test necessity scoring
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    sample_data = {
        'necessity_sample': pd.DataFrame({
            'country_name': ['India', 'China', 'Germany', 'USA'],
            'energy_security_score': [45.2, 72.8, 85.6, 78.9],
            'coal_jobs_thousands': [350.5, 2800.1, 18.2, 42.8],
            'industrial_dependence_pct': [68.2, 85.4, 35.1, 25.7]
        })
    }
    
    countries = ['India', 'China', 'Germany', 'USA']
    scores = calculate_necessity_score(sample_data, countries)
    
    print("Necessity Scores:")
    for country, score in scores.items():
        print(f"  {country}: {score:.1f}")
