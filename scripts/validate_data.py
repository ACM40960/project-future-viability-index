#!/usr/bin/env python3
"""
FVI System Data Validation and Overview Script
Comprehensive validation and analysis of FVI system data files.
"""

import pandas as pd
import numpy as np
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Import our data loader
from data_loader import load_all_data, print_data_overview, get_data_summary, validate_data_completeness

def setup_logging():
    """Setup logging for data validation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data_validation.log')
        ]
    )

def validate_csv_structure(df: pd.DataFrame, file_path: str) -> Dict[str, any]:
    """
    Validate the structure and quality of a CSV file
    
    Args:
        df: DataFrame to validate
        file_path: Path to the file being validated
    
    Returns:
        Dictionary with validation results
    """
    
    validation = {
        'file_path': file_path,
        'valid': True,
        'warnings': [],
        'errors': [],
        'stats': {}
    }
    
    # Basic stats
    validation['stats'] = {
        'rows': len(df),
        'columns': len(df.columns),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
        'missing_values_total': df.isnull().sum().sum(),
        'missing_values_pct': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    }
    
    # Check for empty DataFrame
    if df.empty:
        validation['errors'].append("DataFrame is empty")
        validation['valid'] = False
        return validation
    
    # Check for common column patterns
    common_columns = ['country', 'country_name', 'country_code', 'year', 'score']
    found_columns = [col for col in common_columns if any(col.lower() in df_col.lower() for df_col in df.columns)]
    
    if not found_columns:
        validation['warnings'].append("No standard columns (country, year, score) found")
    
    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        validation['warnings'].append(f"{duplicates} duplicate rows found")
    
    # Check for missing values by column
    missing_by_column = df.isnull().sum()
    high_missing_columns = missing_by_column[missing_by_column > len(df) * 0.5]
    
    if len(high_missing_columns) > 0:
        validation['warnings'].append(f"Columns with >50% missing values: {list(high_missing_columns.index)}")
    
    # Check data types
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    text_columns = df.select_dtypes(include=['object']).columns
    
    validation['stats']['numeric_columns'] = len(numeric_columns)
    validation['stats']['text_columns'] = len(text_columns)
    
    # Check for outliers in numeric columns
    outlier_info = {}
    for col in numeric_columns:
        if len(df[col].dropna()) > 0:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            if outliers > 0:
                outlier_info[col] = outliers
    
    if outlier_info:
        validation['stats']['outliers'] = outlier_info
    
    return validation

def analyze_dimension_consistency(data: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, any]:
    """
    Analyze consistency across dimensions
    
    Args:
        data: Loaded data dictionary
    
    Returns:
        Consistency analysis results
    """
    
    analysis = {
        'countries_by_dimension': {},
        'years_by_dimension': {},
        'common_countries': set(),
        'common_years': set(),
        'coverage_analysis': {}
    }
    
    all_countries = []
    all_years = []
    
    for dimension, datasets in data.items():
        dim_countries = set()
        dim_years = set()
        
        for dataset_name, df in datasets.items():
            if not df.empty:
                # Look for country columns
                country_cols = [col for col in df.columns if 'country' in col.lower()]
                if country_cols:
                    countries = df[country_cols[0]].dropna().unique()
                    dim_countries.update(countries)
                
                # Look for year columns
                year_cols = [col for col in df.columns if 'year' in col.lower()]
                if year_cols:
                    years = df[year_cols[0]].dropna().unique()
                    dim_years.update(years)
        
        analysis['countries_by_dimension'][dimension] = sorted(list(dim_countries))
        analysis['years_by_dimension'][dimension] = sorted(list(dim_years))
        
        all_countries.extend(dim_countries)
        all_years.extend(dim_years)
    
    # Find common countries and years
    if all_countries:
        country_counts = pd.Series(all_countries).value_counts()
        # Countries that appear in at least half the dimensions
        analysis['common_countries'] = set(country_counts[country_counts >= len(data) / 2].index)
    
    if all_years:
        year_counts = pd.Series(all_years).value_counts()
        analysis['common_years'] = set(year_counts[year_counts >= len(data) / 2].index)
    
    # Coverage analysis
    for dimension in data.keys():
        dim_countries = set(analysis['countries_by_dimension'][dimension])
        dim_years = set(analysis['years_by_dimension'][dimension])
        
        analysis['coverage_analysis'][dimension] = {
            'country_count': len(dim_countries),
            'year_count': len(dim_years),
            'common_country_coverage': len(dim_countries.intersection(analysis['common_countries'])),
            'common_year_coverage': len(dim_years.intersection(analysis['common_years']))
        }
    
    return analysis

def generate_data_quality_report(data: Dict[str, Dict[str, pd.DataFrame]]) -> str:
    """
    Generate a comprehensive data quality report
    
    Args:
        data: Loaded data dictionary
    
    Returns:
        Formatted report string
    """
    
    report = []
    report.append("=" * 80)
    report.append("FVI SYSTEM DATA QUALITY REPORT")
    report.append("=" * 80)
    
    # Overall statistics
    total_files = sum(len(datasets) for datasets in data.values())
    total_rows = sum(len(df) for datasets in data.values() for df in datasets.values())
    total_dimensions = len(data)
    
    report.append(f"\n📊 OVERALL STATISTICS:")
    report.append(f"  Total Dimensions: {total_dimensions}")
    report.append(f"  Total Files: {total_files}")
    report.append(f"  Total Rows: {total_rows:,}")
    
    # Dimension-level analysis
    report.append(f"\n📈 DIMENSION BREAKDOWN:")
    
    for dimension, datasets in data.items():
        if datasets:
            dim_files = len(datasets)
            dim_rows = sum(len(df) for df in datasets.values())
            report.append(f"  {dimension.upper()}:")
            report.append(f"    Files: {dim_files}")
            report.append(f"    Rows: {dim_rows:,}")
            
            # List files
            for file_name, df in datasets.items():
                report.append(f"      ✓ {file_name}: {len(df)} rows, {len(df.columns)} columns")
        else:
            report.append(f"  {dimension.upper()}: ❌ NO DATA")
    
    # Consistency analysis
    consistency = analyze_dimension_consistency(data)
    
    report.append(f"\n🔄 CONSISTENCY ANALYSIS:")
    report.append(f"  Common Countries: {len(consistency['common_countries'])}")
    if consistency['common_countries']:
        common_list = sorted(list(consistency['common_countries']))[:10]  # Show first 10
        report.append(f"    Examples: {', '.join(common_list)}")
    
    report.append(f"  Common Years: {len(consistency['common_years'])}")
    if consistency['common_years']:
        years_list = sorted(list(consistency['common_years']))
        report.append(f"    Range: {min(years_list)} - {max(years_list)}")
    
    # Coverage analysis
    report.append(f"\n📋 COVERAGE ANALYSIS:")
    for dimension, coverage in consistency['coverage_analysis'].items():
        report.append(f"  {dimension}:")
        report.append(f"    Countries: {coverage['country_count']}")
        report.append(f"    Years: {coverage['year_count']}")
        if consistency['common_countries']:
            coverage_pct = (coverage['common_country_coverage'] / len(consistency['common_countries'])) * 100
            report.append(f"    Common Country Coverage: {coverage_pct:.1f}%")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)

def validate_all_files():
    """Validate all data files in the system"""
    
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    logging.info("🔍 Starting comprehensive data validation...")
    
    # Load all data
    data = load_all_data(config)
    
    if not data:
        logging.error("❌ No data loaded - check data directory and files")
        return False
    
    # Print data overview
    print_data_overview(data)
    
    # Validate individual files
    all_valid = True
    total_warnings = 0
    total_errors = 0
    
    logging.info("\n🔎 Validating individual files...")
    
    for dimension, datasets in data.items():
        for file_name, df in datasets.items():
            file_path = f"data/{dimension}/{file_name}.csv"
            validation = validate_csv_structure(df, file_path)
            
            if not validation['valid']:
                logging.error(f"❌ {file_path}: INVALID")
                for error in validation['errors']:
                    logging.error(f"    ERROR: {error}")
                all_valid = False
            else:
                logging.info(f"✅ {file_path}: Valid ({validation['stats']['rows']} rows)")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    logging.warning(f"    ⚠️  {warning}")
                total_warnings += len(validation['warnings'])
            
            total_errors += len(validation['errors'])
    
    # Generate comprehensive report
    report = generate_data_quality_report(data)
    
    # Save report to file
    with open('data_quality_report.txt', 'w') as f:
        f.write(report)
    
    print(report)
    
    # Summary
    logging.info(f"\n📋 VALIDATION SUMMARY:")
    logging.info(f"  Files Validated: {sum(len(datasets) for datasets in data.values())}")
    logging.info(f"  Total Warnings: {total_warnings}")
    logging.info(f"  Total Errors: {total_errors}")
    logging.info(f"  Overall Status: {'✅ VALID' if all_valid else '❌ ISSUES FOUND'}")
    logging.info(f"  Report saved to: data_quality_report.txt")
    
    return all_valid

def main():
    """Main validation function"""
    
    setup_logging()
    
    if not Path('config.yaml').exists():
        logging.error("❌ config.yaml not found - run from FVI system directory")
        sys.exit(1)
    
    if not Path('data').exists():
        logging.error("❌ data directory not found")
        sys.exit(1)
    
    success = validate_all_files()
    
    if success:
        logging.info("🎉 Data validation completed successfully!")
    else:
        logging.error("❌ Data validation found issues - check the log above")
        sys.exit(1)

if __name__ == "__main__":
    main()
