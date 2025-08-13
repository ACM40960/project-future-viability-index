# scores/artificial_support.py - Artificial Support Scoring for FVI System
"""
Artificial Support scoring system for coal industry viability assessment

Evaluates government and policy support for coal industry based on:
1. Direct Subsidies - financial support and tax breaks
2. Policy Support - regulatory framework favoring coal
3. Trade Protection - tariffs and import restrictions
4. Investment Support - public investment in coal infrastructure
5. Transition Resistance - resistance to renewable energy transition

Higher scores indicate more artificial support (better for coal viability).
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

def calculate_artificial_support_score(data_dict: Dict, country_list: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate artificial support scores for coal industry
    
    Args:
        data_dict: Dictionary containing artificial support datasets
        country_list: List of countries to calculate scores for
    
    Returns:
        pd.Series: Support scores by country (0-100, higher = more artificial support)
    """
    
    # Load support data
    support_data = _load_support_data(data_dict)
    
    if not support_data:
        logging.warning("No artificial support data found, using fallback scores")
        return _fallback_support_scores(country_list)
    
    # Get country list from data if not provided
    if country_list is None:
        country_list = _extract_countries_from_data(support_data)
    
    # Calculate support scores
    scores = _calculate_support_scores(support_data, country_list)
    
    logging.info(f"Calculated artificial support scores for {len(scores)} countries")
    return scores

def _load_support_data(data_dict: Dict) -> Dict[str, pd.DataFrame]:
    """
    Load and validate artificial support datasets
    """
    support_data = {}
    
    for key, dataset in data_dict.items():
        if isinstance(dataset, pd.DataFrame) and not dataset.empty:
            df = dataset.copy()
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            validation = validate_data(df)
            if validation['is_valid'] or len(validation['issues']) <= 2:
                support_data[key] = df
                logging.info(f"Loaded support dataset '{key}' with {len(df)} rows")
    
    return support_data

def _extract_countries_from_data(data_dict: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Extract unique countries from support datasets
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

def _calculate_support_scores(data_dict: Dict[str, pd.DataFrame], 
                             country_list: List[str]) -> pd.Series:
    """
    Calculate artificial support scores based on available data
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
        
        scores = _aggregate_support_scores(component_scores, country_list)
    
    return pd.Series(scores)

def _calculate_from_single_dataset(df: pd.DataFrame, country_list: List[str]) -> pd.Series:
    """
    Calculate artificial support scores from a single dataset using actual CSV columns
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
            
            # Calculate support score based on available metrics from actual CSV files
            support_components = []
            
            # Direct subsidy score
            if 'score_direct_subsidy' in latest.index:
                subsidy_score = latest['score_direct_subsidy']
                if pd.notna(subsidy_score):
                    # Scale to 0-100 if needed
                    score = subsidy_score * 100 if subsidy_score <= 1.0 else subsidy_score
                    support_components.append(score * 0.25)  # 25% weight
            
            # Tariff trade protection score
            if 'score_tariff_trade_protection' in latest.index:
                tariff_score = latest['score_tariff_trade_protection']
                if pd.notna(tariff_score):
                    score = tariff_score * 100 if tariff_score <= 1.0 else tariff_score
                    support_components.append(score * 0.25)  # 25% weight
            
            # Tax privilege score
            if 'score_tax_privilege' in latest.index:
                tax_score = latest['score_tax_privilege']
                if pd.notna(tax_score):
                    score = tax_score * 100 if tax_score <= 1.0 else tax_score
                    support_components.append(score * 0.25)  # 25% weight
            
            # Dependency conflict score
            if 'score_dependency_conflict' in latest.index:
                conflict_score = latest['score_dependency_conflict']
                if pd.notna(conflict_score):
                    score = conflict_score * 100 if conflict_score <= 1.0 else conflict_score
                    support_components.append(score * 0.25)  # 25% weight
            
            # Fallback to fossil fuel subsidies and coal rents
            if not support_components:
                if 'fossil_fuel_subsidy_usd' in latest.index:
                    subsidy_usd = latest['fossil_fuel_subsidy_usd']
                    if pd.notna(subsidy_usd):
                        # Normalize subsidies (higher = more support)
                        subsidy_score = normalize_score(subsidy_usd, 0, 1e11)  # Up to $100B
                        support_components.append(subsidy_score * 0.5)  # 50% weight
                
                if 'coal_rent_usd' in latest.index:
                    coal_rent = latest['coal_rent_usd']
                    if pd.notna(coal_rent):
                        # Higher coal rents indicate more artificial support
                        rent_score = normalize_score(coal_rent, 0, 1e11)  # Up to $100B
                        support_components.append(rent_score * 0.5)  # 50% weight
            
            # Calculate final support score
            if support_components:
                total_score = sum(support_components)
                scores[country] = min(100.0, max(0.0, total_score))
            else:
                scores[country] = 50.0  # Default neutral score
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _aggregate_support_scores(component_scores: Dict[str, pd.Series], 
                             country_list: List[str]) -> Dict[str, float]:
    """
    Aggregate multiple artificial support component scores
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

def _fallback_support_scores(country_list: Optional[List[str]]) -> pd.Series:
    """
    Provide fallback scores when data is not available
    """
    if not country_list:
        country_list = ["India", "China", "Germany", "USA", "Australia", 
                       "Indonesia", "South Africa", "Poland"]
    
    # Mock scores based on typical artificial support patterns
    fallback_scores = {
        "India": 65.0,       # Moderate support, some subsidies
        "China": 80.0,       # High state support for coal
        "Germany": 25.0,     # Low support, transitioning away
        "USA": 45.0,         # Mixed support depending on administration
        "Australia": 70.0,   # High support for coal exports
        "Indonesia": 75.0,   # High support for domestic coal
        "South Africa": 80.0, # High support due to economic dependence
        "Poland": 55.0       # Moderate support, EU pressure
    }
    
    scores = {}
    for country in country_list:
        scores[country] = fallback_scores.get(country, 50.0)
    
    logging.info(f"Using fallback artificial support scores for {len(scores)} countries")
    return pd.Series(scores)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sample_data = {
        'support_sample': pd.DataFrame({
            'country_name': ['India', 'China', 'Germany', 'USA'],
            'subsidies_usd_billion': [12.5, 8.7, 0.8, 3.2],
            'policy_support_index': [0.45, 0.62, 0.15, 0.28],
            'transition_investment_billion': [15.2, 85.4, 45.6, 28.9]
        })
    }
    
    countries = ['India', 'China', 'Germany', 'USA']
    scores = calculate_artificial_support_score(sample_data, countries)
    
    print("Artificial Support Scores:")
    for country, score in scores.items():
        print(f"  {country}: {score:.1f}")
