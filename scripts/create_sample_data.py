#!/usr/bin/env python3
"""
Create Sample Data for FVI System
Generates comprehensive sample datasets for all 7 dimensions
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

def create_data_directories():
    """Create data directory structure"""
    base_dir = Path("data")
    dimensions = [
        "infrastructure", "necessity", "resource", 
        "artificial_support", "ecological", "economic", "emissions"
    ]
    
    for dimension in dimensions:
        dim_dir = base_dir / dimension
        dim_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dim_dir}")
    
    return base_dir

def create_sample_data():
    """Create comprehensive sample data for all dimensions"""
    
    # Base countries and years
    countries_data = [
        ("IND", "India", 2023),
        ("CHN", "China", 2023),
        ("DEU", "Germany", 2023),
        ("USA", "United States", 2023),
        ("AUS", "Australia", 2023),
        ("IDN", "Indonesia", 2023),
        ("ZAF", "South Africa", 2023),
        ("POL", "Poland", 2023)
    ]
    
    country_codes, country_names, years = zip(*countries_data)
    base_df = pd.DataFrame({
        'country_code': country_codes,
        'country_name': country_names,
        'year': years
    })
    
    # Create data directory
    base_dir = create_data_directories()
    
    # 1. Infrastructure Data
    infrastructure_df = base_df.copy()
    infrastructure_df.update({
        'electricity_coal_pct': [50.2, 62.8, 24.1, 19.5, 54.3, 65.1, 85.2, 42.7],
        'coal_rents_pct_gdp': [2.1, 0.8, 0.1, 0.3, 3.2, 4.5, 1.8, 0.6],
        'electricity_access_pct': [95.2, 100.0, 100.0, 100.0, 100.0, 98.7, 90.1, 100.0],
        'pm25_exposure': [58.1, 42.3, 11.8, 8.2, 7.1, 15.4, 25.8, 20.1],
        'urban_pop_pct': [35.4, 65.2, 77.5, 82.8, 86.2, 57.3, 68.8, 60.1],
        'control_corruption_index': [0.15, 0.22, 1.85, 1.45, 1.92, 0.35, 0.45, 0.88]
    })
    infrastructure_df.to_csv(base_dir / "infrastructure" / "infrastructure_comprehensive.csv", index=False)
    
    # 2. Necessity Data
    necessity_df = base_df.copy()
    necessity_df.update({
        'energy_security_score': [45.2, 72.8, 85.6, 78.9, 65.3, 52.7, 38.9, 68.4],
        'coal_jobs_thousands': [350.5, 2800.1, 18.2, 42.8, 28.4, 125.6, 85.7, 82.1],
        'industrial_dependence_pct': [68.2, 85.4, 35.1, 25.7, 55.8, 72.3, 78.9, 58.6],
        'electricity_coal_pct': [50.2, 62.8, 24.1, 19.5, 54.3, 65.1, 85.2, 42.7],
        'steel_production_mt': [118.2, 1032.8, 35.7, 72.7, 5.9, 8.8, 6.2, 8.0]
    })
    necessity_df.to_csv(base_dir / "necessity" / "necessity_comprehensive.csv", index=False)
    
    # 3. Resource Data
    resource_df = base_df.copy()
    resource_df.update({
        'coal_reserves_mt': [111068, 143197, 35900, 251500, 149077, 38960, 9893, 23070],
        'coal_production_mt': [957.8, 4132.5, 243.8, 716.2, 543.2, 668.4, 252.1, 115.3],
        'resource_quality_index': [0.65, 0.72, 0.58, 0.78, 0.85, 0.62, 0.68, 0.55],
        'mining_productivity_index': [0.52, 0.68, 0.82, 0.75, 0.89, 0.45, 0.38, 0.65],
        'reserve_to_production_ratio': [115.8, 34.7, 147.3, 351.2, 274.5, 58.3, 39.2, 200.0]
    })
    resource_df.to_csv(base_dir / "resource" / "resource_comprehensive.csv", index=False)
    
    # 4. Artificial Support Data
    support_df = base_df.copy()
    support_df.update({
        'subsidies_usd_billion': [12.5, 8.7, 0.8, 3.2, 2.1, 5.8, 1.9, 1.2],
        'policy_support_index': [0.45, 0.62, 0.15, 0.28, 0.52, 0.48, 0.55, 0.38],
        'transition_investment_billion': [15.2, 85.4, 45.6, 28.9, 8.7, 4.2, 2.8, 6.5],
        'tax_incentives_index': [0.35, 0.45, 0.05, 0.15, 0.25, 0.40, 0.50, 0.20],
        'trade_protection_score': [0.28, 0.35, 0.10, 0.18, 0.22, 0.32, 0.38, 0.25]
    })
    support_df.to_csv(base_dir / "artificial_support" / "support_comprehensive.csv", index=False)
    
    # 5. Ecological Data
    ecological_df = base_df.copy()
    ecological_df.update({
        'biodiversity_impact_score': [0.75, 0.85, 0.35, 0.55, 0.45, 0.68, 0.72, 0.58],
        'water_stress_level': [0.78, 0.65, 0.32, 0.42, 0.68, 0.55, 0.72, 0.38],
        'land_degradation_pct': [25.4, 18.7, 8.2, 12.5, 15.8, 22.1, 28.9, 14.3],
        'forest_cover_loss_pct': [0.8, 0.3, 0.1, 0.2, 0.4, 2.1, 0.6, 0.3],
        'air_quality_index': [58.1, 42.3, 11.8, 8.2, 7.1, 15.4, 25.8, 20.1]
    })
    ecological_df.to_csv(base_dir / "ecological" / "ecological_comprehensive.csv", index=False)
    
    # 6. Economic Data
    economic_df = base_df.copy()
    economic_df.update({
        'coal_gdp_contribution_pct': [3.2, 2.8, 0.5, 0.8, 4.5, 5.2, 6.8, 2.1],
        'transition_cost_billion': [125.8, 285.4, 45.2, 98.7, 28.9, 18.6, 15.4, 25.7],
        'economic_diversification_index': [0.45, 0.62, 0.85, 0.78, 0.55, 0.38, 0.32, 0.58],
        'coal_employment_thousands': [350.5, 2800.1, 18.2, 42.8, 28.4, 125.6, 85.7, 82.1],
        'coal_exports_billion_usd': [2.5, 8.9, 0.1, 12.4, 45.2, 28.7, 18.9, 3.2],
        'energy_cost_competitiveness': [0.62, 0.58, 0.25, 0.45, 0.72, 0.68, 0.75, 0.52]
    })
    economic_df.to_csv(base_dir / "economic" / "economic_comprehensive.csv", index=False)
    
    # 7. Emissions Data
    emissions_df = base_df.copy()
    emissions_df.update({
        'co2_emissions_mt': [2654.8, 11472.4, 675.8, 4713.5, 412.5, 615.7, 448.9, 298.4],
        'methane_emissions_kt': [1856.2, 3245.7, 245.1, 1245.8, 285.4, 425.6, 185.7, 125.3],
        'carbon_intensity_index': [0.68, 0.75, 0.25, 0.32, 0.45, 0.58, 0.72, 0.55],
        'coal_share_emissions_pct': [45.2, 57.8, 18.5, 22.4, 32.1, 42.8, 68.9, 38.7],
        'emissions_trend_pct_annual': [2.1, -0.8, -3.2, -1.5, 1.8, 3.4, 1.2, -0.9],
        'co2_per_gdp': [0.85, 0.92, 0.28, 0.45, 0.52, 0.78, 1.15, 0.68]
    })
    emissions_df.to_csv(base_dir / "emissions" / "emissions_comprehensive.csv", index=False)
    
    print(f"\\n✅ Sample data created successfully!")
    print(f"📁 Data files saved in: {base_dir.absolute()}")
    print(f"🌍 Countries included: {', '.join(country_names)}")
    print(f"📊 Dimensions covered: 7 (Infrastructure, Necessity, Resource, Artificial Support, Ecological, Economic, Emissions)")

def create_additional_directories():
    """Create additional required directories"""
    directories = [
        "logs",
        "guides", 
        "vectorstore",
        "models",
        "assets"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create placeholder files
    with open("assets/logo_placeholder.txt", "w") as f:
        f.write("Place your FVI system logo here (logo.png)")
    
    with open("guides/README.md", "w") as f:
        f.write("""# FVI Guides Directory

Place your PDF documents here for RAG (Retrieval-Augmented Generation) functionality.

Supported formats:
- PDF files (.pdf)
- Text files (.txt)
- Markdown files (.md)

The RAG system will automatically process these documents to provide intelligent responses to user queries about coal industry viability.

## Recommended Documents:
- Coal industry reports
- Energy transition studies
- Climate policy documents
- Economic impact assessments
- Environmental impact studies
""")

if __name__ == "__main__":
    print("🚀 Creating FVI System Sample Data...")
    print("=" * 50)
    
    create_sample_data()
    create_additional_directories()
    
    print("\\n" + "=" * 50)
    print("✅ FVI System setup complete!")
    print("\\n📋 Next steps:")
    print("   1. Review the generated sample data")
    print("   2. Add your own data files to replace samples")
    print("   3. Configure API keys in .env file")
    print("   4. Run: python start_system.py")
