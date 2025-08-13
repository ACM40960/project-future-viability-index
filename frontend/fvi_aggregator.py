# fvi_aggregator.py - FVI Calculation and Aggregation Module
"""
FVI Aggregator - Dynamic FVI Calculator with Persona-based Weighting

This module computes Future Viability Index (FVI) scores using different weighting schemes
based on user personas (investor, policy_maker, ngo, analyst, citizen).

Lower FVI scores indicate better coal industry viability.
"""

import yaml
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Union, List
from pathlib import Path

class FVI_Aggregator:
    """Main class for FVI calculation with persona-based weighting"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize FVI Aggregator with persona weights from config
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.weights = self.config.get("persona_weights", {})
        self.current_persona = "analyst"
        self.scores_df = None
        
        # Set default weights if config missing
        if not self.weights:
            self._set_default_weights()
        
        self.current_weights = self.weights.get(self.current_persona, self._get_equal_weights())
        
        logging.info(f"FVI Aggregator initialized with {len(self.weights)} personas")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file) as f:
                    return yaml.safe_load(f)
            else:
                logging.warning(f"Config file not found: {self.config_path}")
                return {}
        except Exception as e:
            logging.warning(f"Config loading failed: {e}, using defaults")
            return {}
    
    def _set_default_weights(self):
        """Set default persona weights if config is missing"""
        self.weights = {
            "investor": {
                "economic": 0.25,
                "artificial_support": 0.20,
                "emissions": 0.20,
                "infrastructure": 0.15,
                "resource": 0.10,
                "ecological": 0.05,
                "necessity": 0.05
            },
            "policy_maker": {
                "necessity": 0.20,
                "economic": 0.20,
                "emissions": 0.20,
                "infrastructure": 0.15,
                "ecological": 0.15,
                "artificial_support": 0.05,
                "resource": 0.05
            },
            "ngo": {
                "emissions": 0.25,
                "ecological": 0.25,
                "necessity": 0.20,
                "infrastructure": 0.10,
                "resource": 0.10,
                "artificial_support": 0.05,
                "economic": 0.05
            },
            "analyst": {
                "infrastructure": 0.143,
                "necessity": 0.143,
                "resource": 0.143,
                "artificial_support": 0.143,
                "ecological": 0.143,
                "economic": 0.143,
                "emissions": 0.143
            },
            "citizen": {
                "necessity": 0.25,
                "ecological": 0.20,
                "infrastructure": 0.20,
                "economic": 0.15,
                "emissions": 0.10,
                "artificial_support": 0.05,
                "resource": 0.05
            }
        }
    
    def _get_equal_weights(self) -> Dict[str, float]:
        """Get equal weights for all dimensions"""
        dimensions = ["infrastructure", "necessity", "resource", "artificial_support",
                     "ecological", "economic", "emissions"]
        equal_weight = 1.0 / len(dimensions)
        return {dim: equal_weight for dim in dimensions}
    
    def set_persona(self, persona: str) -> 'FVI_Aggregator':
        """
        Update weights based on detected persona
        
        Args:
            persona: Persona name (investor, policy_maker, ngo, analyst, citizen)
        
        Returns:
            Self for method chaining
        """
        if persona not in self.weights:
            logging.warning(f"Unknown persona '{persona}', using analyst")
            persona = "analyst"
        
        self.current_persona = persona
        self.current_weights = self.weights[persona]
        
        logging.info(f"Set persona to: {persona}")
        return self
    
    def compute_fvi(self, scores_df: pd.DataFrame) -> pd.Series:
        """
        Compute FVI using current persona weights
        
        Args:
            scores_df: DataFrame with index=country, columns=[infrastructure, necessity, ...]
        
        Returns:
            pd.Series: FVI scores by country (0-100, lower = better viability)
        """
        if scores_df.empty:
            logging.warning("Empty scores DataFrame provided")
            return pd.Series(dtype=float)
        
        self.scores_df = scores_df.copy()
        
        # Standardize column names (remove capital letters, replace spaces with underscores)
        column_mapping = {
            col: col.lower().replace(' ', '_').replace('-', '_')
            for col in scores_df.columns
        }
        self.scores_df.rename(columns=column_mapping, inplace=True)
        
        # Get weights as Series for easier computation
        weights = pd.Series(self.current_weights)
        available_cols = self.scores_df.columns.intersection(weights.index)
        
        if len(available_cols) == 0:
            logging.error("No overlapping scores for weighting")
            logging.error(f"Available columns: {list(self.scores_df.columns)}")
            logging.error(f"Expected columns: {list(weights.index)}")
            return pd.Series(dtype=float)
        
        # Fill missing values with median of available data
        for col in available_cols:
            median_val = self.scores_df[col].median()
            if pd.isna(median_val):
                median_val = 50.0  # Default middle score
            self.scores_df[col] = self.scores_df[col].fillna(median_val)
        
        # Compute weighted FVI
        weighted_scores = self.scores_df[available_cols] * weights[available_cols]
        fvi = weighted_scores.sum(axis=1) / weights[available_cols].sum()
        
        # Ensure FVI is in 0-100 range
        fvi = fvi.clip(0, 100)
        
        logging.info(f"Computed FVI for {len(fvi)} countries using {self.current_persona} weights")
        logging.info(f"Used dimensions: {list(available_cols)}")
        
        return fvi
    
    def get_top_countries(self, scores_df: pd.DataFrame, n: int = 5, 
                         ascending: bool = True) -> pd.Series:
        """
        Get top N countries by FVI score
        
        Args:
            scores_df: DataFrame with scores
            n: Number of countries to return
            ascending: If True, lower FVI = better (typical), if False, higher FVI = better
        
        Returns:
            pd.Series: Top N countries with their FVI scores
        """
        fvi = self.compute_fvi(scores_df)
        
        if ascending:
            return fvi.nsmallest(n)  # Low FVI = high viability
        else:
            return fvi.nlargest(n)   # High FVI = high viability
    
    def get_dimension_contribution(self, scores_df: pd.DataFrame, country: str) -> Dict:
        """
        Get breakdown of how each dimension contributes to a country's FVI
        
        Args:
            scores_df: DataFrame with scores
            country: Country to analyze
        
        Returns:
            Dict: Dimension contributions to FVI
        """
        if country not in scores_df.index:
            logging.warning(f"Country '{country}' not found in scores")
            return {}
        
        # Compute FVI first to ensure proper column mapping
        self.compute_fvi(scores_df)
        
        if self.scores_df is None:
            return {}
        
        country_scores = self.scores_df.loc[country]
        weights = pd.Series(self.current_weights)
        available_cols = self.scores_df.columns.intersection(weights.index)
        
        contributions = {}
        total_weighted_score = 0
        total_weight = 0
        
        for dim in available_cols:
            score = float(country_scores[dim])
            weight = weights[dim]
            weighted_score = score * weight
            
            contributions[dim] = {
                'raw_score': score,
                'weight': weight,
                'weighted_score': weighted_score,
                'contribution_pct': 0  # Will be calculated after loop
            }
            
            total_weighted_score += weighted_score
            total_weight += weight
        
        # Calculate contribution percentages
        for dim in contributions:
            if total_weighted_score > 0:
                contributions[dim]['contribution_pct'] = (
                    contributions[dim]['weighted_score'] / total_weighted_score * 100
                )
        
        # Add summary
        contributions['_summary'] = {
            'total_fvi_score': total_weighted_score / total_weight if total_weight > 0 else 0,
            'total_weight_used': total_weight,
            'dimensions_included': len(available_cols)
        }
        
        return contributions
    
    def get_persona_info(self) -> Dict:
        """Get information about current persona and weights"""
        return {
            'current_persona': self.current_persona,
            'weights': self.current_weights.copy(),
            'available_personas': list(self.weights.keys()),
            'dimensions': list(self.current_weights.keys())
        }
    
    def compare_personas(self, scores_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare FVI scores across all personas
        
        Args:
            scores_df: DataFrame with dimension scores
        
        Returns:
            DataFrame with FVI scores for each persona
        """
        results = {}
        original_persona = self.current_persona
        
        for persona in self.weights.keys():
            self.set_persona(persona)
            fvi_scores = self.compute_fvi(scores_df)
            results[persona] = fvi_scores
        
        # Restore original persona
        self.set_persona(original_persona)
        
        return pd.DataFrame(results)
    
    def validate_scores(self, scores_df: pd.DataFrame) -> Dict:
        """
        Validate input scores DataFrame
        
        Args:
            scores_df: DataFrame to validate
        
        Returns:
            Dict with validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'summary': {}
        }
        
        if scores_df.empty:
            validation['is_valid'] = False
            validation['issues'].append("DataFrame is empty")
            return validation
        
        # Check for required dimensions
        expected_dims = set(self.current_weights.keys())
        available_dims = set(col.lower().replace(' ', '_') for col in scores_df.columns)
        missing_dims = expected_dims - available_dims
        
        if missing_dims:
            validation['issues'].append(f"Missing dimensions: {missing_dims}")
        
        # Check score ranges
        for col in scores_df.columns:
            col_stats = scores_df[col].describe()
            if col_stats['min'] < 0 or col_stats['max'] > 100:
                validation['issues'].append(f"Column {col} has values outside 0-100 range")
        
        # Check for missing values
        missing_counts = scores_df.isnull().sum()
        if missing_counts.any():
            validation['issues'].append(f"Missing values detected: {missing_counts.to_dict()}")
        
        # Summary statistics
        validation['summary'] = {
            'countries': len(scores_df),
            'dimensions': len(scores_df.columns),
            'missing_values': scores_df.isnull().sum().sum(),
            'available_dimensions': list(available_dims),
            'coverage': len(available_dims & expected_dims) / len(expected_dims)
        }
        
        if validation['issues']:
            validation['is_valid'] = False
        
        return validation

if __name__ == "__main__":
    # Test FVI aggregator
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Infrastructure': [65, 85, 45, 50],
        'Necessity': [75, 80, 40, 55],
        'Resource': [70, 85, 45, 75],
        'Artificial_Support': [65, 80, 25, 45],
        'Ecological': [40, 30, 75, 55],
        'Economic': [60, 80, 25, 45],
        'Emissions': [32, 25, 75, 68]
    }, index=['India', 'China', 'Germany', 'USA'])
    
    # Test aggregator
    agg = FVI_Aggregator()
    
    print("Testing FVI Aggregator...")
    for persona in ['investor', 'policy_maker', 'ngo', 'analyst', 'citizen']:
        agg.set_persona(persona)
        fvi_scores = agg.compute_fvi(sample_data)
        print(f"\n{persona.title()} perspective:")
        for country, score in fvi_scores.items():
            print(f"  {country}: {score:.1f}")
