# FVI System - Future Viability Index

A comprehensive coal industry viability assessment platform with intelligent RAG capabilities.

## 🚀 Quick Start

### Option 1: Batch File (Recommended for Windows)
```cmd
# Double-click or run from command prompt:
launch_fvi.bat
```

### Option 2: PowerShell Script (Advanced Users)
```powershell
# Open PowerShell in the FVI directory and run:
.\launch_fvi.ps1

# Or with custom ports:
.\launch_fvi.ps1 -BackendPort 8090 -FrontendPort 8503
```

### Option 3: Manual Launch
```cmd
# Terminal 1 - Backend API:
cd backend
python main.py --port 8089

# Terminal 2 - Frontend UI:
python -m streamlit run main.py --server.port 8502
```

## 📋 System Requirements

### Required
- **Python 3.8+** (3.9+ recommended)
- **4GB RAM minimum** (8GB+ recommended)
- **2GB free disk space**
- **Internet connection** (for initial package installation)

### Supported Operating Systems
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+, CentOS 7+)

## 🛠️ Installation

### Automatic Setup (Windows)
The launcher scripts handle everything automatically:

1. **Download/Clone** the FVI system files
2. **Run** `launch_fvi.bat` or `launch_fvi.ps1`
3. The script will:
   - Check Python installation
   - Install all dependencies
   - Set up directories and configuration
   - Launch both backend and frontend

### Manual Setup
If you prefer manual installation:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create necessary directories
mkdir data logs vectorstore assets

# 3. Copy config files (if not present)
# config.yaml and .env will be created automatically

# 4. Run the system
# See "Manual Launch" section above
```

## 🔧 Configuration

### Environment Variables (.env)
```env
DEBUG=True
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=8089
FRONTEND_PORT=8502

# Optional: Add API keys for external LLM services
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### System Configuration (config.yaml)
The system uses persona-based weighted scoring. Default personas:

- **Analyst**: Balanced weights across all dimensions
- **Investor**: Focus on economic returns and artificial support
- **Policy Maker**: Emphasis on necessity, economics, and emissions
- **NGO**: Priority on emissions and ecological impact
- **Citizen**: Focus on necessity and local environmental impact

## 📊 Features

### Core Capabilities
- **Multi-dimensional Analysis**: 7 key dimensions of coal viability
- **Persona-based Weighting**: Different perspectives for different stakeholders
- **Interactive Dashboard**: Real-time data visualization
- **RAG-powered Chat**: Intelligent Q&A system with context
- **Country Comparisons**: Side-by-side analysis
- **API Integration**: RESTful backend for data access

### FVI Dimensions
1. **Infrastructure** - Coal dependency and transition readiness
2. **Necessity** - Energy security and essential needs
3. **Resource** - Coal reserves and production capacity
4. **Artificial Support** - Government subsidies and policy support
5. **Ecological** - Environmental impact and sustainability
6. **Economic** - Market viability and financial risks
7. **Emissions** - Carbon footprint and climate compliance

## 🌐 Usage

### Web Interface
Once launched, access the application at:
- **Frontend**: http://localhost:8502
- **Backend API**: http://localhost:8089

### Key Features
1. **Select Persona**: Choose your analysis perspective in the sidebar
2. **View Rankings**: See FVI rankings with interactive charts
3. **Detailed Scores**: Examine dimension-by-dimension breakdowns
4. **Country Comparison**: Compare multiple countries side-by-side
5. **AI Chat**: Ask questions about coal industry viability
6. **Export Data**: Download results for further analysis

### API Endpoints
- `GET /api/countries?persona=<persona>` - Get country FVI scores
- `POST /api/chat` - Interactive chat with RAG system
- `GET /api/system/info` - System health and information
- `GET /docs` - Interactive API documentation

## 🔍 Troubleshooting

### Common Issues

#### "Python not found"
- **Solution**: Install Python from [python.org](https://python.org)
- **Windows**: Make sure "Add Python to PATH" is checked during installation

#### "Failed to install dependencies"
- **Solution**: Check internet connection and try again
- **Alternative**: Install manually: `pip install streamlit fastapi uvicorn pandas numpy`

#### "Port already in use"
- **Solution**: Use custom ports: `.\launch_fvi.ps1 -BackendPort 8090 -FrontendPort 8503`
- **Alternative**: Kill existing processes: `taskkill /f /im python.exe`

#### "Backend not responding"
- **Solution**: Wait 10-15 seconds for startup, then refresh browser
- **Check**: Ensure no firewall is blocking ports 8089/8502

#### "ModuleNotFoundError"
- **Solution**: Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Performance Optimization

#### For Low-Memory Systems
- Close other applications before running
- Use single-persona analysis instead of switching frequently
- Reduce browser tabs

#### For Slow Systems
- Allow extra time for initial startup (1-2 minutes)
- Use local deployment instead of cloud instances
- Consider upgrading to Python 3.9+ for better performance

## 📁 Directory Structure

```
fvi_system/
├── launch_fvi.bat          # Windows batch launcher
├── launch_fvi.ps1          # PowerShell launcher
├── main.py                 # Streamlit frontend
├── requirements.txt        # Python dependencies
├── config.yaml            # System configuration
├── .env                   # Environment variables
├── backend/
│   └── main.py            # FastAPI backend
├── data/                  # Data files (auto-created)
├── logs/                  # System logs (auto-created)
├── vectorstore/           # RAG knowledge base (auto-created)
├── assets/                # Static assets (auto-created)
└── scores/                # Scoring modules
```

## 🔒 Security Notes

- The system runs locally by default (localhost only)
- No external data transmission unless API keys are configured
- Log files may contain usage patterns - review logs/fvi.log periodically
- For production deployment, configure proper authentication and HTTPS

## 📈 Data Sources

The FVI system analyzes multiple data sources:
- **Government databases**: Energy statistics, policy documents
- **International organizations**: IEA, World Bank, IPCC reports
- **Industry data**: Coal production, pricing, technology trends
- **Environmental data**: Emissions, pollution metrics
- **Economic indicators**: Market trends, investment flows

## 🤝 Support

### Getting Help
1. **Check this README** for common issues
2. **Review logs**: Check `logs/fvi.log` for error details
3. **API Documentation**: Visit http://localhost:8089/docs when running
4. **System Info**: Check the sidebar in the web interface

### System Health
The system provides health monitoring:
- Component status in the web interface
- API health endpoint: http://localhost:8089/api/health
- Log file monitoring in `logs/fvi.log`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔄 Updates

To update the system:
1. **Backup** your data and configuration files
2. **Download** the latest version
3. **Run** the launcher script to update dependencies
4. **Restore** your custom configurations if needed

---

**Version**: 2.0  
**Last Updated**: August 2025  
**Minimum Python**: 3.8  
**Recommended Python**: 3.9+
