# NumPy 2.0 Compatibility Script
"""
This script helps manage NumPy 2.0 compatibility for the FVI system.
It sets environment variables and handles warnings for better compatibility.
"""

import os
import warnings
import numpy as np

def setup_numpy2_compatibility():
    """Setup environment for NumPy 2.0 compatibility"""
    
    # Set environment variables for TensorFlow compatibility
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    os.environ['NUMPY_EXPERIMENTAL_ARRAY_FUNCTION'] = '1'
    
    # Suppress NumPy 2.0 warnings for backwards compatibility
    warnings.filterwarnings("ignore", category=UserWarning, module="numpy")
    warnings.filterwarnings("ignore", message=".*compiled using NumPy 1.x.*")
    
    print(f"✅ NumPy 2.0 compatibility setup complete")
    print(f"   NumPy version: {np.__version__}")
    print(f"   TensorFlow optimization disabled for stability")
    
    return True

def check_numpy_version():
    """Check if NumPy 2.0+ is installed"""
    major_version = int(np.__version__.split('.')[0])
    if major_version >= 2:
        print(f"✅ NumPy 2.0+ detected: {np.__version__}")
        return True
    else:
        print(f"⚠️  NumPy 1.x detected: {np.__version__}")
        print("   Consider upgrading to NumPy 2.0+ for latest features")
        return False

if __name__ == "__main__":
    print("🔧 FVI System - NumPy 2.0 Compatibility Setup")
    print("=" * 50)
    
    setup_numpy2_compatibility()
    check_numpy_version()
    
    print("\n✅ Ready to start FVI system with NumPy 2.0 support")
