# data_loader.py - Data Loading and Processing Module
import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional, List

# ---------- NEW: Robust path resolution ----------
def _project_root() -> Path:
    """
    Returns the project root assuming this file lives in project_root/ or project_root/<package>/.
    Adjust parents[...] if you relocate this module in the future.
    """
    # If this file is at repo root -> parent is root
    # If this file is in a package under root -> parents[1] is root
    here = Path(__file__).resolve()
    # Try to detect 'frontend' or 'backend' neighbors; default to parent
    # You can tweak this if your structure changes again.
    if (here.parent / "frontend").exists() or (here.parent / "Backend").exists() or (here.parent / "backend").exists():
        return here.parent
    return here.parent  # fallback (current parent is the repo root in your current structure)

def _resolve_data_dir(config: Optional[Dict]) -> Path:
    """
    Resolve data directory robustly:
    1) config['data_dir'] if set (relative to project root unless absolute)
    2) DATA_DIR env var
    3) fallbacks: 'data/', 'frontend/data/'
    """
    root = _project_root()

    # 1) config
    if isinstance(config, dict):
        cfg_val = config.get("data_dir")
        if cfg_val:
            p = Path(cfg_val)
            data_path = p if p.is_absolute() else (root / p)
            return data_path

    # 2) env
    env_val = os.getenv("DATA_DIR")
    if env_val:
        p = Path(env_val)
        data_path = p if p.is_absolute() else (root / p)
        return data_path

    # 3) fallbacks
    for candidate in ["data", "frontend/data"]:
        p = root / candidate
        if p.exists():
            return p

    # default fallback
    return root / "data"

# ---------- Existing helpers (unchanged, with extra logs) ----------
def load_csv_safe(file_path: Path, required_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Safely load CSV file with error handling
    """
    if not file_path.exists():
        logging.warning(f"[data_loader] File not found: {file_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Validate required columns
        if required_cols:
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logging.warning(f"[data_loader] Missing columns in {file_path}: {missing_cols}")
        
        # Standardize column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        logging.info(f"[data_loader] Loaded {file_path} with {len(df)} rows")
        return df
        
    except Exception as e:
        logging.error(f"[data_loader] Failed to load {file_path}: {e}")
        return pd.DataFrame()

def load_dimension_data(data_dir: Path, dimension: str) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV files for a specific dimension
    """
    dimension_dir = data_dir / dimension
    data_dict = {}
    
    if not dimension_dir.exists():
        logging.warning(f"[data_loader] Dimension directory not found: {dimension_dir}")
        return data_dict
    
    # Load all CSV files in the dimension directory
    for csv_file in dimension_dir.glob("*.csv"):
        try:
            df = load_csv_safe(csv_file)
            if not df.empty:
                # Use filename (without extension) as key
                key = csv_file.stem
                data_dict[key] = df
                logging.info(f"[data_loader] Loaded {dimension}/{key}: {len(df)} rows")
        except Exception as e:
            logging.error(f"[data_loader] Error loading {csv_file}: {e}")
    
    return data_dict

def load_all_data(config: Dict) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Load all data for FVI system
    """
    data_dir = _resolve_data_dir(config)
    logging.info(f"[data_loader] Using data_dir: {data_dir}")

    if not data_dir.exists():
        logging.error(f"[data_loader] Data directory not found: {data_dir}")
        return {}
    
    # Define all FVI dimensions
    dimensions = [
        "infrastructure",
        "necessity", 
        "resource",
        "artificial_support",
        "ecological",
        "economic",
        "emissions"
    ]
    
    all_data = {}
    
    for dimension in dimensions:
        try:
            dimension_data = load_dimension_data(data_dir, dimension)
            all_data[dimension] = dimension_data
            
            if dimension_data:
                logging.info(f"[data_loader] Loaded {dimension}: {len(dimension_data)} datasets")
                # Log specific files loaded for transparency
                for file_key in dimension_data.keys():
                    rows = len(dimension_data[file_key])
                    logging.info(f"  - {file_key}: {rows} rows")
            else:
                logging.warning(f"[data_loader] No data found for {dimension}")
                
        except Exception as e:
            logging.error(f"[data_loader] Error loading {dimension} data: {e}")
            all_data[dimension] = {}
    
    total_files = sum(len(dim_data) for dim_data in all_data.values())
    total_rows = sum(len(df) for dim_data in all_data.values() for df in dim_data.values())
    
    logging.info(f"[data_loader] Loaded {total_files} datasets, {total_rows} total rows across {len(dimensions)} dimensions")
    
    # Validate data completeness
    validation_results = validate_data_completeness(all_data)
    failed_dimensions = [dim for dim, valid in validation_results.items() if not valid]
    if failed_dimensions:
        logging.warning(f"[data_loader] Dimensions with data issues: {failed_dimensions}")
    
    return all_data

def validate_data_completeness(data: Dict, min_coverage: float = 0.6) -> Dict[str, bool]:
    """
    Validate data completeness across dimensions
    """
    validation_results = {}
    
    for dimension, datasets in data.items():
        if not datasets:
            validation_results[dimension] = False
            continue
        
        # Check if we have at least one non-empty dataset
        has_data = any(not df.empty for df in datasets.values())
        validation_results[dimension] = has_data
        
        if not has_data:
            logging.warning(f"[data_loader] Dimension {dimension} has no valid data")
    
    coverage = sum(validation_results.values()) / len(validation_results) if validation_results else 0.0
    
    if coverage < min_coverage:
        logging.warning(f"[data_loader] Data coverage ({coverage:.1%}) below threshold ({min_coverage:.1%})")
    else:
        logging.info(f"[data_loader] Data coverage acceptable: {coverage:.1%}")
    
    return validation_results

def get_available_countries(data: Dict) -> List[str]:
    """
    Get list of countries available across all dimensions
    """
    all_countries = set()
    
    for dimension, datasets in data.items():
        for dataset_name, df in datasets.items():
            if not df.empty:
                # Look for country columns
                country_cols = [col for col in df.columns if 'country' in col.lower()]
                if country_cols:
                    countries = df[country_cols[0]].dropna().unique()
                    all_countries.update(countries)
    
    return sorted(list(all_countries))

def get_data_summary(data: Dict) -> Dict[str, Dict[str, int]]:
    """
    Get summary statistics for loaded data
    """
    summary = {}
    
    for dimension, datasets in data.items():
        summary[dimension] = {}
        
        for dataset_name, df in datasets.items():
            summary[dimension][dataset_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'countries': len(df['country_name'].unique()) if 'country_name' in df.columns else 0,
                'years': len(df['year'].unique()) if 'year' in df.columns else 0
            }
    
    return summary

def print_data_overview(data: Dict):
    """
    Print comprehensive overview of loaded data
    """
    print("\n" + "="*60)
    print("FVI SYSTEM DATA OVERVIEW")
    print("="*60)
    
    summary = get_data_summary(data)
    total_files = 0
    total_rows = 0
    
    for dimension, datasets in summary.items():
        if datasets:
            print(f"\n📊 {dimension.upper()}:")
            for dataset_name, stats in datasets.items():
                print(f"  ✓ {dataset_name}")
                print(f"    - Rows: {stats['rows']}")
                print(f"    - Columns: {stats['columns']}")
                if stats['countries'] > 0:
                    print(f"    - Countries: {stats['countries']}")
                if stats['years'] > 0:
                    print(f"    - Years: {stats['years']}")
                total_files += 1
                total_rows += stats['rows']
        else:
            print(f"\n❌ {dimension.upper()}: No data loaded")
    
    print(f"\n📈 SUMMARY:")
    print(f"  Total Files: {total_files}")
    print(f"  Total Rows: {total_rows}")
    print("="*60)

def create_sample_data_files(data_dir: Path):
    """
    Create sample data files for testing if they don't exist
    """
    sample_countries = ["India", "China", "Germany", "USA", "Australia", "Indonesia", "South Africa", "Poland"]
    
    # Sample data templates
    sample_data = {
        "infrastructure": {
            "infrastructure_sample.csv": pd.DataFrame({
                'country_code': ['IND', 'CHN', 'DEU', 'USA', 'AUS', 'IDN', 'ZAF', 'POL'],
                'country_name': sample_countries,
                'year': [2023] * 8,
                'electricity_coal_pct': [50.2, 62.8, 24.1, 19.5, 54.3, 65.1, 85.2, 42.7],
                'coal_rents_pct_gdp': [2.1, 0.8, 0.1, 0.3, 3.2, 4.5, 1.8, 0.6],
                'electricity_access_pct': [95.2, 100.0, 100.0, 100.0, 100.0, 98.7, 90.1, 100.0],
                'pm25_exposure': [58.1, 42.3, 11.8, 8.2, 7.1, 15.4, 25.8, 20.1],
                'urban_pop_pct': [35.4, 65.2, 77.5, 82.8, 86.2, 57.3, 68.8, 60.1],
                'control_corruption_index': [0.15, 0.22, 1.85, 1.45, 1.92, 0.35, 0.45, 0.88]
            })
        },
        "necessity": {
            "necessity_sample.csv": pd.DataFrame({
                'country_code': ['IND', 'CHN', 'DEU', 'USA', 'AUS', 'IDN', 'ZAF', 'POL'],
                'country_name': sample_countries,
                'year': [2023] * 8,
                'energy_security_score': [45.2, 72.8, 85.6, 78.9, 65.3, 52.7, 38.9, 68.4],
                'coal_jobs_thousands': [350.5, 2800.1, 18.2, 42.8, 28.4, 125.6, 85.7, 82.1],
                'industrial_dependence_pct': [68.2, 85.4, 35.1, 25.7, 55.8, 72.3, 78.9, 58.6]
            })
        },
        "resource": {
            "resource_sample.csv": pd.DataFrame({
                'country_code': ['IND', 'CHN', 'DEU', 'USA', 'AUS', 'IDN', 'ZAF', 'POL'],
                'country_name': sample_countries,
                'year': [2023] * 8,
                'coal_reserves_mt': [111068, 143197, 35900, 251500, 149077, 38960, 9893, 23070],
                'coal_production_mt': [957.8, 4132.5, 243.8, 716.2, 543.2, 668.4, 252.1, 115.3],
                'resource_quality_index': [0.65, 0.72, 0.58, 0.78, 0.85, 0.62, 0.68, 0.55]
            })
        }
    }
    
    # Create directories and files
    for dimension, files in sample_data.items():
        dim_dir = data_dir / dimension
        dim_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, df in files.items():
            file_path = dim_dir / filename
            if not file_path.exists():
                df.to_csv(file_path, index=False)
                logging.info(f"[data_loader] Created sample data file: {file_path}")

if __name__ == "__main__":
    # Test data loading
    logging.basicConfig(level=logging.INFO)
    config = {'data_dir': 'data'}
    data_dir_resolved = _resolve_data_dir(config)
    print(f"[data_loader] Detected project root: {_project_root()}")
    print(f"[data_loader] Resolved data_dir: {data_dir_resolved}")
    data = load_all_data(config)
    print(f"Loaded data for {len(data)} dimensions")
    for dim, datasets in data.items():
        print(f"  {dim}: {len(datasets)} datasets")
    countries = get_available_countries(data)
    print(f"Available countries: {countries}")
