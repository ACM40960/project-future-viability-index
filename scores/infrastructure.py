# scores/infrastructure.py - Infrastructure Scoring for FVI System
"""
Infrastructure scoring system for coal industry viability assessment

Computes infrastructure scores based on:
1. Coal Dependency - operational and economic reliance on coal
2. Transition Feasibility - ability to transition away from coal  
3. Environmental Hazards - pollution and cleanup costs
4. Infrastructure Quality - existing facilities and grid integration
5. Policy Framework - governance and regulatory environment

Higher scores indicate worse viability for coal industry.
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

def calculate_infrastructure_score(data_dict: Dict, country_list: Optional[List[str]] = None) -> pd.Series:
    
    infrastructure_data = _load_infrastructure_data(data_dict)
    
    if not infrastructure_data:
        logging.warning("No infrastructure data found, using fallback scores")
        return _fallback_infrastructure_scores(country_list)
    
    if country_list is None:
        country_list = _extract_countries_from_data(infrastructure_data)
    
    component_scores = _calculate_component_scores(infrastructure_data, country_list)
    
    if not component_scores:
        logging.warning("Failed to calculate component scores, using fallback")
        return _fallback_infrastructure_scores(country_list)
    
    final_scores = _aggregate_infrastructure_scores(component_scores, country_list)
    
    logging.info(f"Calculated infrastructure scores for {len(final_scores)} countries")
    return final_scores

def _load_infrastructure_data(data_dict: Dict) -> Dict[str, pd.DataFrame]:
    
    infrastructure_data = {}
    
    for key, dataset in data_dict.items():
        if isinstance(dataset, pd.DataFrame) and not dataset.empty:
            df = dataset.copy()
            
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            validation = validate_data(df)
            if validation['is_valid'] or len(validation['issues']) <= 2:
                infrastructure_data[key] = df
                logging.info(f"Loaded infrastructure dataset '{key}' with {len(df)} rows")
            else:
                logging.warning(f"Skipped invalid dataset '{key}': {validation['issues']}")
    
    return infrastructure_data

def _extract_countries_from_data(data_dict: Dict[str, pd.DataFrame]) -> List[str]:
    
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

def _calculate_component_scores(data_dict: Dict[str, pd.DataFrame], 
                               country_list: List[str]) -> Dict[str, pd.Series]:
    
    component_scores = {}
    
    if len(data_dict) == 1:
        df = list(data_dict.values())[0]
        component_scores = _extract_scores_from_single_dataset(df, country_list)
    
    else:
        for dataset_name, df in data_dict.items():
            scores = _calculate_scores_for_dataset(df, dataset_name, country_list)
            if not scores.empty:
                component_scores[dataset_name] = scores
    
    return component_scores

def _extract_scores_from_single_dataset(df: pd.DataFrame, country_list: List[str]) -> Dict[str, pd.Series]:
    
    component_scores = {}
    
    latest_df = get_latest_data_by_country(df)
    
    country_cols = [col for col in latest_df.columns if 'country' in col]
    if not country_cols:
        logging.warning("No country column found in infrastructure data")
        return component_scores
    
    country_col = country_cols[0]
    
    score_calculations = {
        'coal_dependency': _calculate_coal_dependency_score,
        'transition_readiness': _calculate_transition_readiness_score,
        'environmental_impact': _calculate_environmental_impact_score,
        'infrastructure_quality': _calculate_infrastructure_quality_score,
        'policy_framework': _calculate_policy_framework_score
    }
    
    for component, calc_func in score_calculations.items():
        try:
            scores = calc_func(latest_df, country_col, country_list)
            if not scores.empty:
                component_scores[component] = scores
        except Exception as e:
            logging.warning(f"Failed to calculate {component}: {e}")
    
    return component_scores

def _calculate_coal_dependency_score(df: pd.DataFrame, country_col: str, 
                                   country_list: List[str]) -> pd.Series:
    
    scores = {}
    
    for country in country_list:
        country_data = df[df[country_col] == country]
        if country_data.empty:
            for data_country in df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = df[df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            dependency_factors = []
            
            if 'electricity_coal_pct' in latest.index:
                coal_elec = latest['electricity_coal_pct']
                if pd.notna(coal_elec):
                    dependency_factors.append(coal_elec)
            
            if 'coal_rents_pct_gdp' in latest.index:
                coal_rents = latest['coal_rents_pct_gdp']
                if pd.notna(coal_rents):
                    dependency_factors.append(coal_rents * 10)
            
            if dependency_factors:
                avg_dependency = np.mean(dependency_factors)
                scores[country] = normalize_score(avg_dependency, 0, 100)
            else:
                scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _calculate_transition_readiness_score(df: pd.DataFrame, country_col: str, 
                                        country_list: List[str]) -> pd.Series:
    
    scores = {}
    
    for country in country_list:
        country_data = df[df[country_col] == country]
        if country_data.empty:
            for data_country in df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = df[df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            readiness_factors = []
            
            if 'electricity_access_pct' in latest.index:
                elec_access = latest['electricity_access_pct']
                if pd.notna(elec_access):
                    readiness_factors.append(elec_access)
            
            if 'urban_pop_pct' in latest.index:
                urban_pop = latest['urban_pop_pct']
                if pd.notna(urban_pop):
                    readiness_factors.append(urban_pop)
            
            if readiness_factors:
                avg_readiness = np.mean(readiness_factors)
                scores[country] = 100 - normalize_score(avg_readiness, 0, 100)
            else:
                scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _calculate_environmental_impact_score(df: pd.DataFrame, country_col: str, 
                                        country_list: List[str]) -> pd.Series:
    
    scores = {}
    
    for country in country_list:
        country_data = df[df[country_col] == country]
        if country_data.empty:
            for data_country in df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = df[df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            if 'pm25_exposure' in latest.index:
                pm25 = latest['pm25_exposure']
                if pd.notna(pm25):
                    scores[country] = normalize_score(pm25, 0, 100)
                else:
                    scores[country] = 50.0
            else:
                scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _calculate_infrastructure_quality_score(df: pd.DataFrame, country_col: str, 
                                          country_list: List[str]) -> pd.Series:
    
    scores = {}
    
    for country in country_list:
        country_data = df[df[country_col] == country]
        if country_data.empty:
            for data_country in df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = df[df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            quality_factors = []
            
            if 'electricity_access_pct' in latest.index:
                elec_access = latest['electricity_access_pct']
                if pd.notna(elec_access):
                    quality_factors.append(elec_access)
            
            if 'urban_pop_pct' in latest.index:
                urban_pop = latest['urban_pop_pct']
                if pd.notna(urban_pop):
                    quality_factors.append(urban_pop)
            
            if quality_factors:
                avg_quality = np.mean(quality_factors)
                scores[country] = 100 - normalize_score(avg_quality, 0, 100)
            else:
                scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _calculate_policy_framework_score(df: pd.DataFrame, country_col: str, 
                                    country_list: List[str]) -> pd.Series:
    """
    Calculate policy framework score
    Better governance = lower score (more likely to enforce transition policies)
    """
    scores = {}
    
    for country in country_list:
        country_data = df[df[country_col] == country]
        if country_data.empty:
            for data_country in df[country_col].unique():
                if standardize_country_name(data_country) == country:
                    country_data = df[df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            # Control of corruption index (higher = better governance)
            if 'control_corruption_index' in latest.index:
                corruption_control = latest['control_corruption_index']
                if pd.notna(corruption_control):
                    # Better governance = lower score for coal viability
                    # Normalize and invert
                    normalized = normalize_score(corruption_control, -2.5, 2.5)  # WGI range
                    scores[country] = 100 - normalized
                else:
                    scores[country] = 50.0
            else:
                scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _calculate_scores_for_dataset(df: pd.DataFrame, dataset_name: str, 
                                country_list: List[str]) -> pd.Series:
    """
    Calculate scores for a specific dataset using actual CSV columns
    
    Args:
        df: Dataset DataFrame
        dataset_name: Name of the dataset
        country_list: List of countries
    
    Returns:
        Series of scores for this dataset
    """
    scores = {}
    
    # Get latest data
    latest_df = get_latest_data_by_country(df)
    
    # Find country column
    country_cols = [col for col in latest_df.columns if 'country' in col.lower()]
    if not country_cols:
        return pd.Series(scores)
    
    country_col = country_cols[0]
    
    for country in country_list:
        country_data = latest_df[latest_df[country_col] == country]
        
        # Try alternate country matching
        if country_data.empty:
            for data_country in latest_df[country_col].unique():
                if standardize_country_name(data_country) == standardize_country_name(country):
                    country_data = latest_df[latest_df[country_col] == data_country]
                    break
        
        if not country_data.empty:
            latest = country_data.iloc[-1]
            
            # Use dataset-specific score columns
            if 'coal_dependency_score' in latest.index:
                score = latest['coal_dependency_score']
                if pd.notna(score):
                    # Convert to 0-100 scale
                    scores[country] = score * 100 if score <= 1.0 else score
                    continue
                    
            if 'transition_feasibility_score' in latest.index:
                score = latest['transition_feasibility_score']
                if pd.notna(score):
                    scores[country] = score * 100 if score <= 1.0 else score
                    continue
                    
            if 'hazard_score' in latest.index:
                score = latest['hazard_score']
                if pd.notna(score):
                    scores[country] = score * 100 if score <= 1.0 else score
                    continue
                    
            if 'reclamation_potential_score' in latest.index:
                score = latest['reclamation_potential_score']
                if pd.notna(score):
                    scores[country] = score * 100 if score <= 1.0 else score
                    continue
                    
            if 'root_cause_score' in latest.index:
                score = latest['root_cause_score']
                if pd.notna(score):
                    scores[country] = score * 100 if score <= 1.0 else score
                    continue
            
            # Fallback to calculating from basic metrics
            if 'electricity_coal_pct' in latest.index:
                coal_pct = latest['electricity_coal_pct']
                if pd.notna(coal_pct):
                    scores[country] = coal_pct  # Higher coal % = worse viability
                    continue
            
            scores[country] = 50.0
        else:
            scores[country] = 50.0
    
    return pd.Series(scores)

def _aggregate_infrastructure_scores(component_scores: Dict[str, pd.Series], 
                                   country_list: List[str]) -> pd.Series:
    """
    Aggregate component scores into final infrastructure scores
    
    Args:
        component_scores: Dictionary of component score Series
        country_list: List of countries
    
    Returns:
        Series of final infrastructure scores
    """
    if not component_scores:
        return _fallback_infrastructure_scores(country_list)
    
    # Define component weights (can be made configurable)
    default_weights = {
        'coal_dependency': 0.25,
        'transition_readiness': 0.20,
        'environmental_impact': 0.20,
        'infrastructure_quality': 0.20,
        'policy_framework': 0.15
    }
    
    final_scores = {}
    
    for country in country_list:
        country_component_scores = {}
        
        # Collect scores for this country from all components
        for component, scores in component_scores.items():
            if country in scores:
                country_component_scores[component] = scores[country]
        
        if country_component_scores:
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0
            
            for component, score in country_component_scores.items():
                weight = default_weights.get(component, 1.0 / len(component_scores))
                weighted_sum += score * weight
                total_weight += weight
            
            if total_weight > 0:
                final_scores[country] = weighted_sum / total_weight
            else:
                final_scores[country] = 50.0
        else:
            final_scores[country] = 50.0
    
    return pd.Series(final_scores)

def _fallback_infrastructure_scores(country_list: Optional[List[str]]) -> pd.Series:
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
    
    # Mock scores based on typical infrastructure patterns
    fallback_scores = {
        "India": 65.0,      # High dependency, developing infrastructure
        "China": 75.0,      # Very high dependency, good infrastructure
        "Germany": 35.0,    # Low dependency, excellent infrastructure
        "USA": 45.0,        # Medium dependency, good infrastructure
        "Australia": 60.0,  # High dependency, good infrastructure
        "Indonesia": 70.0,  # High dependency, developing infrastructure
        "South Africa": 80.0, # Very high dependency, mixed infrastructure
        "Poland": 55.0      # Medium-high dependency, good infrastructure
    }
    
    scores = {}
    for country in country_list:
        scores[country] = fallback_scores.get(country, 55.0)  # Default score
    
    logging.info(f"Using fallback infrastructure scores for {len(scores)} countries")
    return pd.Series(scores)

if __name__ == "__main__":
    # Test infrastructure scoring
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    sample_data = {
        'infrastructure_sample': pd.DataFrame({
            'country_name': ['India', 'China', 'Germany', 'USA'],
            'electricity_coal_pct': [50.2, 62.8, 24.1, 19.5],
            'pm25_exposure': [58.1, 42.3, 11.8, 8.2],
            'electricity_access_pct': [95.2, 100.0, 100.0, 100.0],
            'control_corruption_index': [0.15, 0.22, 1.85, 1.45]
        })
    }
    
    countries = ['India', 'China', 'Germany', 'USA']
    scores = calculate_infrastructure_score(sample_data, countries)
    
    print("Infrastructure Scores:")
    for country, score in scores.items():
        print(f"  {country}: {score:.1f}")
