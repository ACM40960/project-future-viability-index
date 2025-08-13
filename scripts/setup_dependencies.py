#!/usr/bin/env python3
"""
FVI System Dependency Setup and Validation Script
This script ensures all required dependencies are properly installed and configured.
"""

import subprocess
import sys
import os
import importlib
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for the dependency installation process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('setup.log')
        ]
    )

def check_python_version():
    """Check if Python version meets requirements"""
    if sys.version_info < (3, 8):
        logging.error(f"Python 3.8+ required. Current version: {sys.version}")
        return False
    
    logging.info(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        logging.info(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        logging.info(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to install {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    
    # Core dependencies with specific versions
    dependencies = [
        "streamlit>=1.32.0",
        "fastapi>=0.110.0", 
        "uvicorn>=0.29.0",
        "pandas>=2.2.1",
        "numpy>=1.26.4",
        "scipy>=1.12.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.1",
        "langchain>=0.1.17",
        "langchain-community>=0.0.33",
        "langchain-core>=0.1.47",
        "langchain-openai>=0.1.8",
        "openai>=1.30.3",
        "sentence-transformers>=2.5.1",
        "faiss-cpu>=1.8.0",
        "unstructured[all-docs]>=0.10.18",
        "PyPDF2>=3.0.1",
        "tqdm>=4.66.1",
        "matplotlib>=3.8.3",
        "plotly>=5.18.0",
        "streamlit-extras>=0.4.0"
    ]
    
    failed_packages = []
    
    logging.info("🔧 Installing FVI System dependencies...")
    
    for package in dependencies:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        logging.error(f"❌ Failed to install: {', '.join(failed_packages)}")
        return False
    
    logging.info("✅ All dependencies installed successfully!")
    return True

def validate_imports():
    """Validate that all critical modules can be imported"""
    
    critical_modules = [
        'streamlit',
        'fastapi', 
        'pandas',
        'numpy',
        'yaml',
        'langchain',
        'langchain_community',
        'sentence_transformers',
        'faiss',
        'openai',
        'matplotlib',
        'plotly'
    ]
    
    failed_imports = []
    
    logging.info("🔍 Validating module imports...")
    
    for module in critical_modules:
        try:
            importlib.import_module(module)
            logging.info(f"✅ {module}")
        except ImportError as e:
            logging.error(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logging.error(f"❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    logging.info("✅ All critical modules imported successfully!")
    return True

def validate_data_files():
    """Validate that data files are present"""
    
    data_dir = Path("data")
    
    if not data_dir.exists():
        logging.error("❌ Data directory not found")
        return False
    
    # Check for dimension directories
    dimensions = [
        "infrastructure", "necessity", "resource", 
        "artificial_support", "ecological", "economic", "emissions"
    ]
    
    missing_dimensions = []
    total_files = 0
    
    for dimension in dimensions:
        dim_path = data_dir / dimension
        if not dim_path.exists():
            missing_dimensions.append(dimension)
            continue
        
        csv_files = list(dim_path.glob("*.csv"))
        total_files += len(csv_files)
        logging.info(f"✅ {dimension}: {len(csv_files)} CSV files")
    
    if missing_dimensions:
        logging.warning(f"⚠️  Missing dimension directories: {', '.join(missing_dimensions)}")
    
    logging.info(f"📊 Total CSV files found: {total_files}")
    
    if total_files < 10:
        logging.warning("⚠️  Low number of data files - system may not function properly")
    
    return total_files > 0

def create_directory_structure():
    """Create necessary directory structure"""
    
    directories = [
        "data", "guides", "vectorstore", "models", "logs", "assets"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logging.info(f"✅ Directory: {directory}")

def validate_configuration():
    """Validate configuration file"""
    
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        logging.error("❌ config.yaml not found")
        return False
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['llm', 'persona_weights', 'data_processing']
        
        for section in required_sections:
            if section not in config:
                logging.error(f"❌ Missing config section: {section}")
                return False
        
        logging.info("✅ Configuration file validated")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error reading config.yaml: {e}")
        return False

def test_system_components():
    """Test core system components"""
    
    try:
        # Test data loader
        from data_loader import load_all_data
        
        config = {'data_dir': 'data'}
        data = load_all_data(config)
        
        if data:
            logging.info("✅ Data loader working")
        else:
            logging.warning("⚠️  Data loader returned empty data")
        
        # Test FVI aggregator
        from fvi_aggregator import FVI_Aggregator
        
        aggregator = FVI_Aggregator()
        logging.info("✅ FVI Aggregator initialized")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ System component test failed: {e}")
        return False

def main():
    """Main setup function"""
    
    setup_logging()
    
    logging.info("🚀 Starting FVI System Setup...")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create directory structure
    logging.info("📁 Creating directory structure...")
    create_directory_structure()
    
    # Step 3: Install dependencies
    if not check_and_install_dependencies():
        logging.error("❌ Dependency installation failed")
        sys.exit(1)
    
    # Step 4: Validate imports
    if not validate_imports():
        logging.error("❌ Module validation failed")
        sys.exit(1)
    
    # Step 5: Validate configuration
    if not validate_configuration():
        logging.error("❌ Configuration validation failed")
        sys.exit(1)
    
    # Step 6: Validate data files
    if not validate_data_files():
        logging.error("❌ Data validation failed")
        sys.exit(1)
    
    # Step 7: Test system components
    if not test_system_components():
        logging.error("❌ System component test failed")
        sys.exit(1)
    
    logging.info("🎉 FVI System setup completed successfully!")
    logging.info("📝 Next steps:")
    logging.info("   1. Set your API keys in .env file (see .env.example)")
    logging.info("   2. Run: python start_system.py")
    logging.info("   3. Or run: streamlit run main.py")

if __name__ == "__main__":
    main()
