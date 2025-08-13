# FVI System - Future Viability Index for Coal Industry

A comprehensive system for analyzing coal industry viability across multiple dimensions using AI-powered insights and RAG (Retrieval-Augmented Generation) technology.

## 🚀 Qui├── 📊 Data & Scoring
│   ├── data/                     # Coal industry datasets
│   │   ├── infrastructure/       # Infrastructure metrics
│   │   ├── economic/             # Economic indicators
│   │   ├── emissions/            # Carbon footprint data
│   │   ├── ecological/           # Environmental impact data
│   │   ├── artificial_support/   # Government policy data
│   │   ├── necessity/            # Energy security data
│   │   └── resource/             # Coal reserves and quality data
│   ├── scores/                   # Scoring algorithm modules
│   └── vectorstore/              # AI knowledge base (FAISS + metadata)
├── 📚 Documentation & Resources
│   ├── docs/                     # Technical documentation
│   │   └── DEVELOPER_GUIDE.md    # Complete development guide
│   ├── scripts/                  # Setup and utility scripts
│   │   ├── quick_start.bat       # Windows batch launcher
│   │   ├── quick_start.ps1       # PowerShell launcher
│   │   └── verify_setup.py       # System verification script
│   ├── guides/                   # User guides and tutorials
│   └── assets/                   # Static assets and resources
└── ⚙️ Configuration
    ├── .env.template             # Environment configuration template
    ├── .gitignore               # Git ignore patterns
    ├── logs/                     # Application logs
    └── temp/                     # Temporary files
```

### 🚀 Super Quick Start Options

**Option 1: One-Click Launcher (Windows)**
```bash
# Double-click or run:
scripts\quick_start.bat
```

**Option 2: PowerShell Launcher**
```bash
# Right-click and "Run with PowerShell":
scripts\quick_start.ps1
```

**Option 3: Verify First, Then Launch**
```bash
# Check if everything is ready:
python scripts\verify_setup.py

# Then start manually:
python backend\main.py --port 8089     # Terminal 1
streamlit run main.py --server.port 8502   # Terminal 2
```

### Prerequisites
- Python 3.11+ installed
- Git (optional, for cloning)

### Step 1: Setup Environment
```bash
# Clone or download the project
# Navigate to the project directory
cd fvi_system_fixed

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the Application
Open **TWO** terminal windows and run these commands:

**Terminal 1 - Backend API:**
```bash
cd fvi_system_fixed; python backend\main.py --port 8089
```

**Terminal 2 - Frontend Interface:**
```bash
cd fvi_system_fixed; streamlit run main.py --server.port 8502
```

### Step 3: Access the Application
- **🌐 Frontend**: Open http://localhost:8502 in your browser
- **🔧 API Docs**: Visit http://localhost:8089/docs for API documentation

## 📋 Complete Setup Guide

### System Requirements
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Detailed Installation

1. **Download/Clone Project**
   ```bash
   git clone <repository-url>
   # OR download and extract ZIP file
   ```

2. **Environment Setup**
   ```bash
   cd fvi_system_fixed
   
   # Create virtual environment
   python -m venv .venv
   
   # Activate (choose your platform)
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Windows Command Prompt:
   .venv\Scripts\activate.bat
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Upgrade pip first
   python -m pip install --upgrade pip
   
   # Install all requirements
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   # Check if key packages are installed
   python -c "import streamlit, fastapi, pandas, numpy; print('✅ All packages installed successfully!')"
   ```

5. **Start Services**
   
   **Option A: Manual Start (Recommended for Development)**
   ```bash
   # Terminal 1 - Backend
   cd fvi_system_fixed
   python backend\main.py --port 8089
   
   # Terminal 2 - Frontend (new terminal)
   cd fvi_system_fixed
   streamlit run main.py --server.port 8502
   ```
   
   **Option B: Using Scripts**
   ```bash
   # Windows:
   .\scripts\launch_fvi.ps1
   
   # macOS/Linux: (if available)
   bash scripts/launch_fvi.sh
   ```

## 🔧 Configuration

### Environment Variables (.env file)
Create a `.env` file in the root directory:
```env
# Optional: Customize these settings
DATA_DIR=data
VECTORSTORE_DIR=vectorstore
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8089
FRONTEND_PORT=8502
```

### Port Configuration
- **Backend API**: Port 8089 (configurable)
- **Frontend**: Port 8502 (configurable)
- **Alternative Ports**: If ports are busy, use 8091, 8503, etc.

## 🎯 Usage Guide

### For Investors
1. Select "Investor" persona in the sidebar
2. Ask questions like: "What are the investment risks for coal in China?"
3. Review FVI scores and investment recommendations

### For Policy Makers
1. Select "Policy Maker" persona
2. Ask: "What policies affect coal industry viability in Germany?"
3. Analyze regulatory impact across dimensions

### For Analysts
1. Use "Analyst" persona for comprehensive analysis
2. Compare multiple countries: "Compare coal viability between India and Australia"
3. Export data for further analysis

## 📊 Key Features

### 🧠 AI-Powered Analysis
- **RAG Technology**: Retrieval-Augmented Generation for contextual responses
- **Enhanced Vectorstore**: FAISS + ChromaDB integration with 59+ documents
- **Smart Categorization**: Automatic organization into 7 contextual categories
- **Key Insights Extraction**: Automatic identification of critical information

### 📈 Multi-Dimensional Scoring
1. **Infrastructure**: Physical and digital readiness
2. **Necessity**: Energy security requirements  
3. **Resource**: Coal reserves and quality
4. **Artificial Support**: Government policies
5. **Ecological**: Environmental impact
6. **Economic**: Market dynamics
7. **Emissions**: Carbon footprint

### 👥 Persona-Based Analysis
- **Investor**: Focus on ROI and financial metrics (25% economic weight)
- **Policy Maker**: Emphasis on regulations and social impact
- **NGO**: Environmental and social considerations priority
- **Analyst**: Balanced view across all dimensions
- **Citizen**: Local impact and energy costs focus

### 🎛️ Interactive Features
- **Real-time FVI Calculation**: Dynamic scoring based on latest data
- **Country Comparison**: Side-by-side analysis of multiple markets
- **Investment Recommendations**: Clear Buy/Hold/Avoid guidance
- **Risk Assessment**: Comprehensive viability scoring (0-100 scale)
- **Enhanced Context Display**: Organized, categorized information

## 🛠️ Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find and kill process using port
netstat -ano | findstr :8089
taskkill /PID <process-id> /F

# Or use different ports
python backend\main.py --port 8091
streamlit run main.py --server.port 8503
```

**Module Not Found:**
```bash
# Ensure virtual environment is activated
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

**FAISS Installation Issues (Windows):**
```bash
# Install CPU version explicitly
pip install faiss-cpu
```

**Streamlit Not Starting:**
```bash
# Clear Streamlit cache
streamlit cache clear
# Or restart with clean state
streamlit run main.py --server.port 8502 --server.headless true
```

### Logs and Debugging
- **Application Logs**: Check `logs/fvi.log`
- **Streamlit Logs**: Available in terminal output
- **API Logs**: Backend terminal shows detailed API calls

## 📁 Project Structure

```
fvi_system_fixed/
├── 🎯 Core Application
│   ├── main.py                    # Streamlit frontend interface
│   ├── backend/main.py           # FastAPI backend server
│   ├── config.yaml               # System configuration
│   └── requirements.txt          # Python dependencies
├── 🧠 AI & Analytics
│   ├── fvi_aggregator.py         # FVI calculation engine
│   ├── rag_agent.py              # RAG chat agent
│   ├── enhanced_rag_integration.py # Enhanced vectorstore integration
│   ├── data_loader.py            # Data processing utilities
│   └── numpy2_compatibility.py   # NumPy 2.0 compatibility layer
├── � Data & Scoring
│   ├── data/                     # Coal industry datasets
│   │   ├── infrastructure/       # Infrastructure metrics
│   │   ├── economic/             # Economic indicators
│   │   ├── emissions/            # Carbon footprint data
│   │   └── ...                   # Other dimension data
│   ├── scores/                   # Scoring algorithm modules
│   └── vectorstore/              # AI knowledge base (FAISS + metadata)
├── 📚 Documentation & Resources
│   ├── docs/                     # Technical documentation
│   ├── scripts/                  # Setup and utility scripts
│   ├── guides/                   # User guides and tutorials
│   └── assets/                   # Static assets and resources
└── ⚙️ Configuration
    ├── .env                      # Environment variables
    ├── .gitignore               # Git ignore patterns
    └── logs/                     # Application logs
```

## 🔗 API Endpoints

### Key Backend Routes
- `GET /api/countries` - List all countries with FVI scores
- `POST /api/chat` - Chat with RAG agent
- `GET /api/country/{name}` - Detailed country analysis
- `GET /api/system-info` - System status and configuration

### Frontend Features
- **Dashboard**: Overview of all country FVI scores
- **Chat Interface**: AI-powered analysis and Q&A
- **Country Comparison**: Detailed comparative analysis
- **Export Options**: Download data in various formats

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit: `git commit -m "Add feature description"`
5. Push: `git push origin feature-name`
6. Create Pull Request

## 📧 Support

For issues, questions, or contributions:
- Check troubleshooting section above
- Review logs in `logs/fvi.log`
- Create an issue in the repository
- Ensure all dependencies are correctly installed

## 🏷️ Version Info

- **Python**: 3.11+ required
- **Key Dependencies**: Streamlit, FastAPI, FAISS, ChromaDB, LangChain
- **AI Models**: SentenceTransformers (all-MiniLM-L6-v2)
- **Database**: FAISS vector store + ChromaDB integration
