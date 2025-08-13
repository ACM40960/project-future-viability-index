# 🌍 Future Viability Index (FVI) System v2.0

A comprehensive coal industry viability assessment platform with advanced AI-powered analytics and intelligent RAG (Retrieval-Augmented Generation) capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Structure](#data-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

The FVI System evaluates coal industry viability across multiple dimensions using advanced data analytics and AI. It provides stakeholder-specific insights through persona-based analysis and intelligent document retrieval.

### Key Capabilities

- **Multi-dimensional Analysis**: 7 core dimensions of coal industry assessment
- **Persona-based Insights**: Tailored analysis for investors, policymakers, NGOs, analysts, and citizens
- **Intelligent RAG**: AI-powered document retrieval and question answering
- **Comprehensive Data Loading**: Support for 40+ datasets with automatic validation
- **Interactive Visualizations**: Dynamic charts and country comparisons
- **RESTful API**: Programmatic access to all functionality

## ✨ Features

### 🔍 Analysis Dimensions

1. **Infrastructure**: Coal dependency, transition readiness, cleanup costs
2. **Necessity**: Energy security, employment, industrial dependence
3. **Resource**: Coal reserves, production capacity, quality metrics
4. **Artificial Support**: Subsidies, tax privileges, trade protection
5. **Ecological**: Environmental impact, biodiversity, air quality
6. **Economic**: Market viability, stranded assets, investment risks
7. **Emissions**: Carbon footprint, climate compliance, abatement costs

### 🎭 Stakeholder Personas

- **Investor**: Focus on financial returns and market risks
- **Policy Maker**: Emphasis on energy security and public benefits
- **NGO**: Environmental and social impact prioritization
- **Analyst**: Balanced, objective assessment across all dimensions
- **Citizen**: Local impact and community welfare focus

### 🤖 AI-Powered Features

- Intelligent document search across policy papers and reports
- Persona detection from user queries
- Context-aware responses with real FVI data integration
- Natural language query processing
- Automated insights generation

## 🏗️ System Architecture

```
FVI System v2.0
├── Frontend (Streamlit)
│   ├── Multi-page interface
│   ├── Interactive visualizations
│   └── Real-time data updates
├── Backend (FastAPI)
│   ├── RESTful API endpoints
│   ├── Data processing pipeline
│   └── Score calculation engine
├── AI Layer (LangChain)
│   ├── RAG implementation
│   ├── Vector document storage
│   └── LLM integration (OpenAI/Gemini/Local)
└── Data Layer
    ├── 40+ CSV datasets
    ├── Validation system
    └── Automated loading
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- 4GB+ RAM recommended
- Internet connection for AI features

### Automated Setup

1. **Extract the system**:
```bash
unzip fvi_system_fixed.zip
cd fvi_system_fixed
```

2. **Run the automated setup**:
```bash
python setup_dependencies.py
```

This will:
- Verify Python version
- Install all required dependencies
- Validate system configuration
- Test data loading
- Create necessary directories

### Manual Setup (Alternative)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Validate installation**:
```bash
python validate_data.py
```

## ⚙️ Configuration

### 1. API Keys Setup

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
# Required for AI features
OPENAI_API_KEY=your_openai_api_key_here

# Optional alternatives
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 2. System Configuration

Edit `config.yaml` to customize:

```yaml
# LLM Configuration
llm:
  type: "openai"                    # "openai", "gemini", "anthropic", "local"
  model_name: "gpt-3.5-turbo"       
  temperature: 0.4                   
  max_tokens: 1000                   

# Persona Weights (customize priorities)
persona_weights:
  investor:
    economic: 0.25
    artificial_support: 0.20
    # ... other dimensions
```

## 🎮 Usage

### Web Interface (Recommended)

Start the full system:
```bash
python start_system.py
```

Or start Streamlit directly:
```bash
streamlit run main.py
```

Access at: `http://localhost:8501`

### API Server

Start the FastAPI backend:
```bash
python backend/main.py
```

API documentation: `http://localhost:8000/docs`

### Command Line Tools

**Validate data**:
```bash
python validate_data.py
```

**Test system components**:
```bash
python -c "from data_loader import load_all_data; print('Data loading works!')"
```

## 📊 Data Structure

### Dataset Organization

```
data/
├── infrastructure/
│   ├── score1_coal_dependency.csv
│   ├── score2_transition_history.csv
│   ├── infrastructure_comprehensive.csv
│   └── ...
├── necessity/
│   ├── necessity_score1_coal.csv
│   ├── necessity_comprehensive.csv
│   └── ...
├── resource/
├── artificial_support/
├── ecological/
├── economic/
└── emissions/
```

### Data Format Standards

Each CSV file should contain:
- `country_name`: Full country name
- `country_code`: ISO 3-letter code (optional)
- `year`: Data year
- Score columns: Numeric values (0-100 scale recommended)

Example:
```csv
country_name,country_code,year,coal_dependency_score,transition_readiness
India,IND,2023,75.2,25.8
China,CHN,2023,82.1,35.4
```

## 📡 API Documentation

### Key Endpoints

```bash
# Get country scores
GET /api/scores/{country}

# Calculate FVI for persona
POST /api/calculate
{
  "countries": ["India", "China"],
  "persona": "investor"
}

# RAG query
POST /api/rag/query
{
  "question": "What are India's coal transition risks?",
  "persona": "policy_maker"
}

# Data validation
GET /api/data/validate
```

### Response Format

```json
{
  "status": "success",
  "data": {
    "country": "India",
    "fvi_score": 62.5,
    "dimension_scores": {
      "infrastructure": 75.2,
      "necessity": 68.9,
      ...
    }
  },
  "metadata": {
    "persona": "investor",
    "timestamp": "2025-08-04T19:58:55Z"
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check Python version
python --version  # Should be 3.8+
```

**2. Data Loading Issues**
```bash
# Validate data files
python validate_data.py

# Check data directory
ls -la data/*/
```

**3. AI Features Not Working**
```bash
# Check API keys
python -c "import os; print('OPENAI_API_KEY' in os.environ)"

# Test LangChain
python -c "from langchain_openai import OpenAI; print('LangChain OK')"
```

**4. Performance Issues**
- Reduce `max_workers` in config.yaml
- Use smaller embedding models
- Enable caching in configuration

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.10+ |
| RAM | 2GB | 4GB+ |
| Storage | 1GB | 2GB+ |
| CPU | 2 cores | 4+ cores |

### Validation Commands

```bash
# Full system validation
python setup_dependencies.py

# Data validation only
python validate_data.py

# Component testing
python -m pytest tests/ --verbose  # If tests available

# Check configuration
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## 📈 Advanced Usage

### Custom Personas

Add new personas in `config.yaml`:

```yaml
persona_weights:
  my_custom_persona:
    infrastructure: 0.20
    necessity: 0.15
    resource: 0.15
    artificial_support: 0.15
    ecological: 0.15
    economic: 0.10
    emissions: 0.10
```

### Batch Processing

```python
from fvi_aggregator import FVI_Aggregator
from data_loader import load_all_data

# Load data
config = yaml.safe_load(open('config.yaml'))
data = load_all_data(config)

# Initialize aggregator
aggregator = FVI_Aggregator(data=data)

# Batch calculate scores
countries = ["India", "China", "Germany", "USA"]
results = {}

for country in countries:
    results[country] = aggregator.calculate_fvi_score(
        country=country,
        persona="analyst"
    )
```

### Custom Data Integration

```python
# Add custom data source
def load_custom_data(data_dir):
    custom_df = pd.read_csv("my_custom_data.csv")
    return {"custom_metric": custom_df}

# Register in data_loader.py
```

## 🛠️ Development

### Project Structure

```
fvi_system_fixed/
├── main.py                 # Main Streamlit interface
├── start_system.py         # System startup script
├── data_loader.py          # Data loading and validation
├── fvi_aggregator.py       # Score calculation engine
├── rag_agent.py           # AI/RAG implementation
├── config.yaml            # System configuration
├── requirements.txt       # Python dependencies
├── setup_dependencies.py  # Setup automation
├── validate_data.py       # Data validation
├── backend/               # FastAPI backend
├── scores/               # Score calculation modules
├── data/                 # Dataset storage
├── guides/               # Document storage
└── assets/               # Static assets
```

### Adding New Features

1. **New Score Calculation**:
   - Add module in `scores/`
   - Update `fvi_aggregator.py`
   - Add tests

2. **New Data Source**:
   - Add CSV files to appropriate `data/` subdirectory
   - Update validation in `validate_data.py`

3. **New API Endpoint**:
   - Add route in `backend/main.py`
   - Update documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check this README and troubleshooting section
2. Run `python validate_data.py` for data issues
3. Check logs in `logs/` directory
4. Create an issue with system information:

```bash
# System info for bug reports
python --version
pip list | grep -E "(streamlit|langchain|pandas|openai)"
python validate_data.py 2>&1 | head -20
```

---

**🌍 FVI System v2.0** - Empowering informed decisions on coal industry transition through comprehensive data analysis and AI-powered insights.
