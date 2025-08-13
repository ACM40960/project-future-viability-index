# FVI System - Developer Guide

## 🛠️ Development Setup

### Quick Development Start
```bash
# 1. Clone and setup
git clone <repository>
cd fvi_system_fixed

# 2. Run verification
python scripts/verify_setup.py

# 3. Quick start (Windows)
scripts/quick_start.bat
# OR PowerShell
scripts/quick_start.ps1
```

## 🏗️ Architecture Overview

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Engine    │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (RAG/FAISS)  │
│   Port: 8502    │    │   Port: 8089    │    │   Vectorstore   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **User Input** → Frontend (Streamlit)
2. **API Calls** → Backend (FastAPI)
3. **Data Processing** → FVI Aggregator
4. **AI Analysis** → RAG Agent + Enhanced Vectorstore
5. **Response** → Frontend Display

## 📁 Code Organization

### Core Modules
```
fvi_system_fixed/
├── 🎯 User Interface
│   ├── main.py                    # Streamlit frontend
│   └── backend/main.py           # FastAPI backend
├── 🧠 AI & Analytics
│   ├── fvi_aggregator.py         # FVI calculation engine
│   ├── rag_agent.py              # RAG chat functionality
│   ├── enhanced_rag_integration.py # Advanced vectorstore
│   └── data_loader.py            # Data processing utilities
├── 📊 Scoring System
│   └── scores/
│       ├── infrastructure.py      # Infrastructure dimension
│       ├── economic.py           # Economic analysis
│       ├── emissions.py          # Carbon footprint
│       └── ...                   # Other dimensions
└── 📈 Data Pipeline
    └── data/                     # Structured datasets
```

### Key Classes & Functions

#### FVI Aggregator (`fvi_aggregator.py`)
```python
class FVIAggregator:
    def calculate_fvi_score(country, persona)
    def get_investment_recommendation(fvi_score, persona)
    def compare_countries(countries, persona)
```

#### RAG Agent (`rag_agent.py`)
```python
class RAGAgent:
    def process_query(query, persona, country)
    def get_context_documents(query)
    def generate_response(query, context, persona)
```

#### Enhanced Integration (`enhanced_rag_integration.py`)
```python
class EnhancedRAGIntegration:
    def enhance_query_response(query, context)
    def _structure_context(context_chunks)  # 7-category organization
    def _extract_key_insight(context)       # Auto insight extraction
```

## 🔧 Development Workflow

### Setting Up Development Environment
```bash
# 1. Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install development tools
pip install pytest black flake8 mypy

# 4. Verify setup
python scripts/verify_setup.py
```

### Running in Development Mode
```bash
# Backend with auto-reload
uvicorn backend.main:app --reload --port 8089

# Frontend with auto-reload (runs automatically)
streamlit run main.py --server.port 8502
```

### Code Standards
```bash
# Format code
black *.py scores/*.py

# Check linting
flake8 *.py --max-line-length=88

# Type checking
mypy main.py backend/main.py
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_fvi_aggregator.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### API Testing
```bash
# Test backend endpoints
curl http://localhost:8089/api/countries
curl -X POST http://localhost:8089/api/chat -H "Content-Type: application/json" -d '{"query":"coal viability", "persona":"investor"}'
```

### Frontend Testing
- Access http://localhost:8502
- Test all personas (Investor, Policy Maker, NGO, Analyst, Citizen)
- Verify FVI calculations
- Test chat functionality
- Check country comparisons

## 🚀 Deployment

### Production Checklist
- [ ] All tests pass
- [ ] Code formatted and linted
- [ ] Dependencies updated
- [ ] Configuration reviewed
- [ ] Logs properly configured
- [ ] Environment variables set

### Docker Deployment (Future)
```dockerfile
# Example Dockerfile structure
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8089 8502
CMD ["python", "start_system.py"]
```

## 📊 Data Management

### Adding New Data
1. Place CSV files in appropriate `data/` subdirectory
2. Update data loading scripts
3. Regenerate vectorstore if needed
4. Test FVI calculations

### Vectorstore Updates
```python
# Rebuild vectorstore with new documents
from enhanced_rag_integration import EnhancedRAGIntegration
rag = EnhancedRAGIntegration()
rag.rebuild_vectorstore()
```

### Score Calculation Updates
- Modify scoring modules in `scores/` directory
- Update weights in `config.yaml`
- Test with different personas
- Validate against expected outcomes

## 🐛 Debugging

### Common Issues
1. **Port conflicts**: Use `netstat -ano | findstr :8089` to check
2. **Module imports**: Ensure virtual environment is activated
3. **FAISS issues**: Install `faiss-cpu` specifically
4. **Memory issues**: Monitor RAM usage during vectorstore operations

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In code
logger.info("Processing FVI calculation")
logger.error(f"Error in calculation: {error}")
```

### Performance Monitoring
- Check `logs/fvi.log` for application logs
- Monitor API response times in backend terminal
- Use browser dev tools for frontend performance

## 🔄 Contributing

### Branch Strategy
```bash
# Create feature branch
git checkout -b feature/new-functionality

# Make changes and commit
git add .
git commit -m "Add new functionality"

# Push and create PR
git push origin feature/new-functionality
```

### Code Review Checklist
- [ ] Functionality works as expected
- [ ] Code follows Python conventions
- [ ] Tests added for new features
- [ ] Documentation updated
- [ ] No breaking changes to API
- [ ] Performance impact considered

### Release Process
1. Update version numbers
2. Update CHANGELOG.md
3. Create release tag
4. Update deployment documentation
5. Notify stakeholders

## 📚 Additional Resources

### Key Dependencies Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [FAISS Documentation](https://faiss.ai/)
- [LangChain Docs](https://docs.langchain.com/)

### FVI System Specific
- System architecture diagrams
- API endpoint documentation
- Scoring methodology papers
- Coal industry data sources

---

**Happy Coding! 🚀**

For questions or support, check the main README.md or create an issue in the repository.
