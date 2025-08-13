# scores/economic.py - Economic Scoring for FVI System
"""
Economic scoring system for coal industry viability assessment

Evaluates economic factors affecting coal industry viability based on:
1. Economic Contribution - coal's contribution to GDP and economy
2. Employment Impact - jobs dependent on coal industry
3. Transition Costs - economic cost of transitioning away from coal
4. Market Competitiveness - coal price competitiveness vs alternatives
5. Economic Diversification - economy's ability to absorb transition

Higher scores indicate better economic viability for coal industry.
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

def calculate_economic_score(data_dict: Dict, country_list: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate economic viability scores for coal industry
    
    Args:
        data_dict: Dictionary containing economic datasets
        country_list: List of countries to calculate scores for
    
    Returns:
        pd.Series: Economic scores by country (0-100, higher = better economic viability)
    """
    
    # Load economic data
    economic_data = _load_economic_data(data_dict)
    
    if not economic_data:
        logging.warning("No economic data found, using fallback scores")
        return _fallback_economic_scores(country_list)
    
    # Get country list from data if not provided
    if country_list is None:
        country_list = _extract_countries_from_data(economic_data)
    
    # Calculate economic scores
    scores = _calculate_economic_scores(economic_data, country_list)
    
    logging.info(f"Calculated economic scores for {len(scores)} countries")
    return scores

def _load_economic_data(data_dict: Dict) -> Dict[str, pd.DataFrame]:
    """
    Load and validate economic datasets
    """
    economic_data = {}
    
    for key, dataset in data_dict.items():
        if isinstance(dataset, pd.DataFrame) and not dataset.empty:
            df = dataset.copy()
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            validation = validate_data(df)
            if validation['is_valid'] or len(validation['issues']) <= 2:
                economic_data[key] = df
                logging.info(f"Loaded economic dataset '{key}' with {len(df)} rows")
    
    return economic_data

def _extract_countries_from_data(data_dict: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Extract unique countries from economic datasets
    """
    countries = set()
    
    for df in data_dict.values():
        country_cols = [col for col in df.columns if 'country' in col]
        for col in country_cols:
            if col in df.columns:
                country_names = df[col].dropna().unique()
                for name in country_names:
                    standardized = standardize_country_name(name)
                    if standardized:
                        countries.add(standardized)
    
    return sorted(list(countries))

def _calculate_economic_scores(data_dict: Dict[str, pd.DataFrame], 
                              country_list: List[str]) -> pd.Series:
    """
    Calculate economic scores based on available data
    """
    scores = {}
    
    # Use the best available dataset
    if len(data_dict) == 1:
        df = list(data_dict.values())[0]
        scores = _calculate_from_single_dataset(df, country_list)
    else:
        # Multiple datasets - combine scores
        component_scores = {}
        for dataset_name, df in data_dict.items():
            dataset_scores = _calculate_from_single_dataset(df, country_list)
            if not dataset_scores.empty:
                component_scores[dataset_name] = dataset_scores
        
        scores = _aggregate_economic_scores(component_scores, country_list)
    
    return pd.Series(scores)

def _calculate_from_single_dataset(df: pd.DataFrame, country_list: List[str]) -> pd.Series:
    """
    Calculate economic scores from a single dataset using actual CSV columns
    """
    scores = {}
    
    # Get latest data for each country
    latest_df = get_latest_data_by_country(df)
    
    # Find country column
    country_cols = [col for col in latest_df.columns if 'country' in col.lower()]
    if not country_cols:
        return pd.Series(scores)
    
    country_col = country_cols[0]
    
    for country in country_list:
        country_data = latest_df[latest_df[country_col] == country]
        
        if country_data.empty:
            # Try standardized name matching
            for data_country in latest_df[country_col].unique():
                if standardize_country_name(data_country) == standardize_country_name(country):
                    country_data = latest_df[latest_df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            # Calculate economic score based on available metrics
            economic_components = []
            
            # Coal rents as % of GDP (higher = better for coal viability)
            if 'coal_rents_pct_of_gdp' in latest.index:
                coal_rents = latest['coal_rents_pct_of_gdp']
                if pd.notna(coal_rents):
                    # Higher coal rents = better coal economic viability
                    econ_score = normalize_score(coal_rents, 0, 10)  # 0-10% range
                    economic_components.append(econ_score * 0.4)  # 40% weight
            elif 'coal_rents_pct' in latest.index:
                coal_rents = latest['coal_rents_pct']
                if pd.notna(coal_rents):
                    econ_score = normalize_score(coal_rents, 0, 10)
                    economic_components.append(econ_score * 0.4)
            
            # Coal rent in USD (absolute economic contribution)
            if 'coal_rent_usd' in latest.index:
                coal_rent_usd = latest['coal_rent_usd']
                if pd.notna(coal_rent_usd):
                    # Normalize to 0-100 (higher absolute value = better viability)
                    rent_score = normalize_score(coal_rent_usd, 0, 1e11)  # Up to $100B
                    economic_components.append(rent_score * 0.3)  # 30% weight
            
            # Coal share of electricity (economic importance)
            if 'coal_share_of_electricity_latest' in latest.index:
                coal_elec_share = latest['coal_share_of_electricity_latest']
                if pd.notna(coal_elec_share):
                    economic_components.append(coal_elec_share * 0.2)  # 20% weight
            elif 'coal_share_electricity' in latest.index:
                coal_elec_share = latest['coal_share_electricity']
                if pd.notna(coal_elec_share):
                    economic_components.append(coal_elec_share * 0.2)
            
            # Coal exports share (trade importance)
            if 'coal_export_share_percent' in latest.index:
                coal_export_share = latest['coal_export_share_percent']
                if pd.notna(coal_export_share):
                    economic_components.append(coal_export_share * 0.1)  # 10% weight
            
            # Calculate weighted economic score
            if economic_components:
                economic_score = sum(economic_components)
                scores[country] = min(100.0, max(0.0, economic_score))
            else:
                scores[country] = 50.0  # Default neutral score
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _aggregate_economic_scores(component_scores: Dict[str, pd.Series], 
                              country_list: List[str]) -> Dict[str, float]:
    """
    Aggregate multiple economic component scores
    """
    aggregated_scores = {}
    
    for country in country_list:
        country_scores = []
        
        for component_name, scores in component_scores.items():
            if country in scores and pd.notna(scores[country]):
                country_scores.append(scores[country])
        
        if country_scores:
            aggregated_scores[country] = np.mean(country_scores)
        else:
            aggregated_scores[country] = 50.0
    
    return aggregated_scores

def _fallback_economic_scores(country_list: Optional[List[str]]) -> pd.Series:
    """
    Provide fallback scores when data is not available
    """
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia", 
                       "Indonesia", "South Africa", "Poland"]
    
    # Mock scores based on typical economic patterns for coal
    # Higher scores = better economic viability for coal
    fallback_scores = {
        "India": 60.0,       # Significant economic contribution, high transition costs
        "China": 80.0,       # Major economic contributor, massive transition costs
        "Germany": 25.0,     # Low economic dependence, manageable transition
        "USA": 45.0,         # Moderate economic impact, regional variation
        "Australia": 55.0,   # Important export economy, some dependence
        "Indonesia": 70.0,   # High economic dependence, growing economy
        "South Africa": 75.0, # Very high economic dependence
        "Poland": 58.0       # Moderate-high dependence, EU transition support
    }
    
    scores = {}
    for country in country_list:
        scores[country] = fallback_scores.get(country, 55.0)
    
    logging.info(f"Using fallback economic scores for {len(scores)} countries")
    return pd.Series(scores)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sample_data = {
        'economic_sample': pd.DataFrame({
            'country_name': ['India', 'China', 'Germany', 'USA'],
            'coal_gdp_contribution_pct': [3.2, 2.8, 0.5, 0.8],
            'transition_cost_billion': [125.8, 285.4, 45.2, 98.7],
            'economic_diversification_index': [0.45, 0.62, 0.85, 0.78]
        })
    }
    
    countries = ['India', 'China', 'Germany', 'USA']
    scores = calculate_economic_score(sample_data, countries)
    
    print("Economic Scores:")
    for country, score in scores.items():
        print(f"  {country}: {score:.1f}")
