# scores/__init__.py - FVI Scoring System
"""
FVI Scoring System - All Dimension Calculators

This module provides scoring functions for all 7 FVI dimensions:
1. Infrastructure - Coal dependency and transition readiness
2. Necessity - Energy security and coal dependency needs  
3. Resource - Coal reserves, production, and quality
4. Artificial Support - Government subsidies and policy support
5. Ecological - Environmental impact and biodiversity effects
6. Economic - Economic contribution and transition costs
7. Emissions - Carbon emissions and climate impact

All scoring functions return values in 0-100 range where:
- Lower scores = Better coal industry viability
- Higher scores = Worse coal industry viability
"""

from .infrastructure import calculate_infrastructure_score
from .necessity import calculate_necessity_score
from .resource import calculate_resource_score
from .artificial_support import calculate_artificial_support_score
from .ecological import calculate_ecological_score
from .economic import calculate_economic_score
from .emissions import calculate_emissions_score
from .utils import (
    normalize_score, 
    validate_data, 
    calculate_weighted_average,
    standardize_country_name,
    normalize_series,
    validate_score_range
)

__all__ = [
    # Main scoring functions
    'calculate_infrastructure_score',
    'calculate_necessity_score', 
    'calculate_resource_score',
    'calculate_artificial_support_score',
    'calculate_ecological_score',
    'calculate_economic_score',
    'calculate_emissions_score',
    
    # Utility functions
    'normalize_score',
    'validate_data',
    'calculate_weighted_average',
    'standardize_country_name',
    'normalize_series',
    'validate_score_range'
]

# Version information
__version__ = "2.0.0"
__author__ = "FVI Development Team"
__description__ = "Future Viability Index Scoring System for Coal Industry Assessment"

def get_all_scoring_functions():
    """
    Get dictionary of all scoring functions
    
    Returns:
        Dict mapping dimension names to scoring functions
    """
    return {
        'infrastructure': calculate_infrastructure_score,
        'necessity': calculate_necessity_score,
        'resource': calculate_resource_score,
        'artificial_support': calculate_artificial_support_score,
        'ecological': calculate_ecological_score,
        'economic': calculate_economic_score,
        'emissions': calculate_emissions_score
    }

def validate_all_dimensions(data_dict, country_list=None):
    """
    Validate data availability across all dimensions
    
    Args:
        data_dict: Data dictionary from load_all_data
        country_list: List of countries to check
    
    Returns:
        Dict with validation results for each dimension
    """
    results = {}
    scoring_functions = get_all_scoring_functions()
    
    for dimension, func in scoring_functions.items():
        try:
            scores = func(data_dict.get(dimension, {}), country_list)
            results[dimension] = {
                'success': True,
                'countries_scored': len(scores),
                'avg_score': scores.mean() if not scores.empty else 0,
                'score_range': [scores.min(), scores.max()] if not scores.empty else [0, 0]
            }
        except Exception as e:
            results[dimension] = {
                'success': False,
                'error': str(e),
                'countries_scored': 0
            }
    
    return results
