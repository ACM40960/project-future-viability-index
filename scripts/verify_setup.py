"""
FVI System Setup Verification Script
Checks if all dependencies and requirements are properly installed.
"""

import sys
import importlib
import subprocess
import platform

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.11+ required")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - Not installed")
        return False

def check_required_packages():
    """Check all required packages"""
    packages = [
        ("streamlit", "streamlit"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("python-multipart", "multipart"),
        ("faiss-cpu", "faiss"),
        ("sentence-transformers", "sentence_transformers"),
        ("chromadb", "chromadb"),
        ("langchain", "langchain"),
        ("langchain-community", "langchain_community"),
        ("pyyaml", "yaml"),
        ("plotly", "plotly"),
        ("openpyxl", "openpyxl")
    ]
    
    print("\n📦 Checking Required Packages:")
    print("-" * 40)
    
    all_installed = True
    missing_packages = []
    
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            all_installed = False
            missing_packages.append(package_name)
    
    return all_installed, missing_packages

def check_system_info():
    """Display system information"""
    print("\n💻 System Information:")
    print("-" * 40)
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🏗️  Architecture: {platform.architecture()[0]}")
    print(f"🐍 Python Executable: {sys.executable}")

def check_ports():
    """Check if required ports are available"""
    import socket
    
    print("\n🌐 Port Availability:")
    print("-" * 40)
    
    ports = [8089, 8502]
    available_ports = []
    
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result != 0:
                    print(f"✅ Port {port} is available")
                    available_ports.append(port)
                else:
                    print(f"⚠️  Port {port} is in use")
        except Exception as e:
            print(f"🔍 Port {port} - Could not check ({e})")
    
    return available_ports

def main():
    """Main verification function"""
    print("🔍 FVI System Setup Verification")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check packages
    packages_ok, missing = check_required_packages()
    
    # Check system info
    check_system_info()
    
    # Check ports
    available_ports = check_ports()
    
    # Final summary
    print("\n📋 Verification Summary:")
    print("=" * 50)
    
    if python_ok and packages_ok:
        print("✅ All checks passed! System is ready to run.")
        print("\n🚀 To start the system:")
        print("   Option 1: Run quick_start.bat (Windows)")
        print("   Option 2: Run quick_start.ps1 (PowerShell)")
        print("   Option 3: Manual start:")
        print("      Terminal 1: python backend\\main.py --port 8089")
        print("      Terminal 2: streamlit run main.py --server.port 8502")
    else:
        print("❌ Setup verification failed!")
        
        if not python_ok:
            print("   • Update Python to version 3.11 or higher")
        
        if missing:
            print("   • Install missing packages:")
            print(f"     pip install {' '.join(missing)}")
    
    print(f"\n🌐 Access points (when running):")
    print(f"   Frontend: http://localhost:8502")
    print(f"   API Docs: http://localhost:8089/docs")

if __name__ == "__main__":
    main()
