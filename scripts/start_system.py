#!/usr/bin/env python3
"""
FVI System Startup Script
Comprehensive startup and management for the FVI System
"""

import sys
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import argparse

def print_banner():
    """Print system banner"""
    banner = """
🌍 ================================================= 🌍
    Future Viability Index (FVI) System v2.0
    Coal Industry Viability Assessment Platform
🌍 ================================================= 🌍
"""
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit', 'fastapi', 'uvicorn', 'pandas', 'numpy', 
        'pyyaml', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages installed")
        return True

def test_core_system():
    """Test core FVI system components"""
    print("🧪 Testing FVI System components...")
    
    try:
        from fvi_aggregator import FVI_Aggregator
        print("  ✅ FVI Aggregator")
        
        from data_loader import load_all_data
        print("  ✅ Data Loader")
        
        from scores import calculate_infrastructure_score
        print("  ✅ Scoring System")
        
        import yaml
        if os.path.exists("config.yaml"):
            with open("config.yaml") as f:
                config = yaml.safe_load(f)
            print("  ✅ Configuration")
        else:
            print("  ⚠️  Configuration file missing")
        
        # Test data loading
        if os.path.exists("data"):
            data = load_all_data(config if 'config' in locals() else {})
            if data:
                print(f"  ✅ Data loading ({len(data)} dimensions)")
            else:
                print("  ⚠️  No data found - will create sample data")
        else:
            print("  ⚠️  Data directory missing - will create sample data")
        
        # Test FVI calculation
        agg = FVI_Aggregator()
        print("  ✅ FVI calculation system")
        
        return True
        
    except Exception as e:
        print(f"  ❌ System test failed: {e}")
        return False

def create_sample_data():
    """Create sample data if needed"""
    if not os.path.exists("data") or not os.listdir("data"):
        print("📊 Creating sample data...")
        try:
            from create_sample_data import create_sample_data, create_additional_directories
            create_sample_data()
            create_additional_directories()
            print("✅ Sample data created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create sample data: {e}")
            return False
    else:
        print("✅ Data directory exists")
        return True

def setup_environment():
    """Setup environment files if needed"""
    if not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        try:
            if os.path.exists(".env.example"):
                import shutil
                shutil.copy(".env.example", ".env")
                print("✅ .env file created from .env.example")
                print("💡 Please edit .env file to add your API keys")
            else:
                # Create basic .env file
                with open(".env", "w") as f:
                    f.write("""# FVI System Environment Variables
# Add your API keys here

OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=True
ENVIRONMENT=development
""")
                print("✅ Basic .env file created")
                print("💡 Please edit .env file to add your API keys")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")
    else:
        print("✅ .env file exists")

def start_streamlit(port=8501):
    """Start Streamlit application"""
    print(f"🎨 Starting Streamlit UI on port {port}...")
    try:
        env = os.environ.copy()
        env['STREAMLIT_SERVER_PORT'] = str(port)
        
        result = subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'main.py',
            '--server.port', str(port),
            '--server.address', '0.0.0.0',
            '--server.headless', 'true'
        ], env=env, capture_output=False)
        
    except KeyboardInterrupt:
        print("\\n⏹️  Streamlit stopped by user")
    except Exception as e:
        print(f"❌ Streamlit failed: {e}")

def start_backend(port=8000):
    """Start FastAPI backend"""
    print(f"🔧 Starting FastAPI backend on port {port}...")
    try:
        os.chdir("backend")
        subprocess.run([sys.executable, "main.py"], capture_output=False)
    except KeyboardInterrupt:
        print("\\n⏹️  Backend stopped by user")
    except Exception as e:
        print(f"❌ Backend failed: {e}")
    finally:
        os.chdir("..")

def start_fullstack():
    """Start both backend and frontend"""
    print("🚀 Starting Full Stack Application...")
    print("   Backend API: http://localhost:8000")
    print("   Frontend UI: http://localhost:8501")
    print("\\n   Press Ctrl+C to stop all servers\\n")
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, args=(8000,), daemon=True)
        backend_thread.start()
        
        # Wait for backend to start
        print("⏳ Waiting for backend to start...")
        time.sleep(3)
        
        # Open browser
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open("http://localhost:8501")
                print("🌐 Browser opened to http://localhost:8501")
            except:
                print("💡 Please open http://localhost:8501 in your browser")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start frontend in main thread
        start_streamlit(8501)
        
    except KeyboardInterrupt:
        print("\\n\\n⏹️  Shutting down FVI System...")
        print("   All servers stopped.")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try: pip install streamlit fastapi uvicorn pandas numpy pyyaml python-dotenv")
        return False

def run_tests():
    """Run system tests"""
    print("🧪 Running comprehensive system tests...")
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Python version
    if check_python_version():
        tests_passed += 1
    
    # Test 2: Dependencies
    if check_dependencies():
        tests_passed += 1
    
    # Test 3: Core system
    if test_core_system():
        tests_passed += 1
    
    # Test 4: Data availability
    if os.path.exists("data") and os.listdir("data"):
        print("✅ Data availability")
        tests_passed += 1
    else:
        print("⚠️  Data directory missing or empty")
    
    # Test 5: Configuration
    if os.path.exists("config.yaml"):
        print("✅ Configuration file")
        tests_passed += 1
    else:
        print("❌ Configuration file missing")
    
    print(f"\\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready.")
        return True
    elif tests_passed >= 3:
        print("⚠️  System partially ready. Some issues detected.")
        return True
    else:
        print("❌ System not ready. Please fix the issues above.")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="FVI System Startup Manager")
    parser.add_argument('mode', nargs='?', default='interactive',
                       choices=['test', 'install', 'setup', 'streamlit', 'backend', 'fullstack', 'interactive'],
                       help='Startup mode')
    parser.add_argument('--port', type=int, default=8501, help='Port for Streamlit')
    parser.add_argument('--backend-port', type=int, default=8000, help='Port for backend API')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    print_banner()
    
    if args.mode == 'test':
        run_tests()
        return
    
    elif args.mode == 'install':
        if not install_dependencies():
            return
        setup_environment()
        create_sample_data()
        print("\\n✅ Installation complete!")
        return
    
    elif args.mode == 'setup':
        setup_environment()
        create_sample_data()
        print("\\n✅ Setup complete!")
        return
    
    elif args.mode == 'streamlit':
        if run_tests():
            start_streamlit(args.port)
        return
    
    elif args.mode == 'backend':
        if run_tests():
            start_backend(args.backend_port)
        return
    
    elif args.mode == 'fullstack':
        if run_tests():
            start_fullstack()
        return
    
    # Interactive mode (default)
    print("🔍 Running system diagnostics...")
    
    # Check and setup system
    if not check_python_version():
        return
    
    if not check_dependencies():
        install = input("\\n📦 Install missing dependencies? (y/N): ").lower().strip()
        if install == 'y':
            if not install_dependencies():
                return
        else:
            print("❌ Cannot proceed without dependencies")
            return
    
    # Setup environment and data
    setup_environment()
    create_sample_data()
    
    # Test system
    if not test_core_system():
        print("❌ System tests failed. Please check the configuration.")
        return
    
    print("\\n🎯 System is ready!")
    print("\\nSelect startup mode:")
    print("  1. 🎨 Streamlit UI only (http://localhost:8501)")
    print("  2. 🔧 Backend API only (http://localhost:8000)")
    print("  3. 🚀 Full Stack (both frontend and backend)")
    print("  4. 🧪 Run tests only")
    print("  5. ❌ Exit")
    
    while True:
        try:
            choice = input("\\nChoice [3]: ").strip() or "3"
            
            if choice == "1":
                start_streamlit(args.port)
                break
            elif choice == "2":
                start_backend(args.backend_port)
                break
            elif choice == "3":
                start_fullstack()
                break
            elif choice == "4":
                run_tests()
                break
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\\n\\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
