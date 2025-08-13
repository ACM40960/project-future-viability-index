# FVI System Deployment Guide

Complete deployment guide for the Future Viability Index (FVI) System.

## 🚀 Quick Start

### 1. System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: At least 2GB free space

### 2. Installation & Setup

```bash
# Clone or extract the FVI system
cd fvi_system_updated

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# (Optional) Edit .env to add your API keys
nano .env

# Create sample data and start system
python start_system.py
```

### 3. Access the System
- **Main UI (Streamlit)**: http://localhost:8501
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 System Architecture

### Directory Structure
```
fvi_system_updated/
├── main.py                    # Streamlit frontend application
├── start_system.py           # System startup manager
├── config.yaml              # System configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # Main documentation
├── DEPLOYMENT.md            # This deployment guide
├── backend/                 # FastAPI backend
│   └── main.py
├── scores/                  # Scoring calculation modules
│   ├── __init__.py
│   ├── utils.py
│   ├── infrastructure.py
│   ├── necessity.py
│   ├── resource.py
│   ├── artificial_support.py
│   ├── ecological.py
│   ├── economic.py
│   └── emissions.py
├── data/                    # CSV datasets (7 dimensions)
│   ├── infrastructure/
│   ├── necessity/
│   ├── resource/
│   ├── artificial_support/
│   ├── ecological/
│   ├── economic/
│   └── emissions/
├── guides/                  # PDF documents for RAG
├── logs/                    # System logs
├── vectorstore/             # RAG embeddings storage
├── models/                  # Local LLM models (if used)
└── assets/                  # Static assets (logos, etc.)
```

### Core Components
1. **Frontend (Streamlit)**: Interactive dashboard with charts and chat
2. **Backend (FastAPI)**: RESTful API with CORS support
3. **Scoring System**: 7-dimensional coal viability assessment
4. **FVI Aggregator**: Persona-based weighting and calculation
5. **RAG Agent**: AI-powered chat with document retrieval
6. **Data Loader**: CSV processing and validation

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# LLM API Keys (optional - for enhanced chat)
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Database (optional)
DATABASE_URL=sqlite:///fvi_system.db

# Development Settings
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8501
```

### System Configuration (config.yaml)
Key configuration sections:
- **LLM Settings**: Model selection and API configuration
- **RAG Settings**: Embedding model and retrieval parameters
- **Persona Weights**: Weighting schemes for different perspectives
- **Data Processing**: Validation and scoring parameters

## 🐳 Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs vectorstore models

# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Default command
CMD ["python", "start_system.py", "fullstack"]
```

### 2. Create docker-compose.yml
```yaml
version: '3.8'

services:
  fvi-system:
    build: .
    ports:
      - "8501:8501"  # Streamlit
      - "8000:8000"  # FastAPI
    environment:
      - ENVIRONMENT=production
      - API_HOST=0.0.0.0
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    volumes:
      - ./data:/app/data
      - ./guides:/app/guides
      - ./logs:/app/logs
      - ./.env:/app/.env
    restart: unless-stopped

  # Optional: Add Redis for caching
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### 3. Deploy with Docker
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ Cloud Deployment

### AWS Deployment
1. **EC2 Instance**: Use Ubuntu 20.04+ with at least 4GB RAM
2. **Security Groups**: Open ports 8000, 8501, and 22 (SSH)
3. **Elastic IP**: Assign static IP for consistent access

```bash
# On EC2 instance
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv git -y

# Clone and setup
git clone <your-fvi-repo>
cd fvi_system_updated
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run system
python start_system.py fullstack
```

### Google Cloud Platform
1. **Compute Engine**: n1-standard-2 instance (2 vCPU, 7.5GB RAM)
2. **Firewall Rules**: Allow ports 8000 and 8501
3. **Cloud Storage**: For data backup and sharing

### Railway/Heroku
1. **Procfile**:
```
web: python start_system.py fullstack
```

2. **Environment Variables**: Set in platform dashboard
3. **Buildpacks**: Python

## 🔧 Production Optimizations

### 1. Performance
```python
# In config.yaml
performance:
  enable_parallel_processing: true
  max_workers: 4
  memory_limit_mb: 2048

# Enable caching
api:
  enable_caching: true
  cache_ttl: 300
```

### 2. Security
- Use HTTPS in production
- Set secure API keys
- Enable rate limiting
- Regular security updates

### 3. Monitoring
```python
# Add to requirements.txt
prometheus-client
structlog

# System health monitoring
# Endpoint: /api/health
```

### 4. Backup Strategy
```bash
# Data backup
tar -czf fvi_backup_$(date +%Y%m%d).tar.gz data/ guides/ logs/

# Database backup (if using)
sqlite3 fvi_system.db ".backup fvi_backup.db"
```

## 🧪 Testing

### Unit Tests
```bash
# Test individual components
python -m pytest tests/

# Test specific module
python -c "from scores import calculate_infrastructure_score; print('✅ Infrastructure scoring works')"
```

### System Tests
```bash
# Full system test
python start_system.py test

# API tests
curl http://localhost:8000/api/health
curl http://localhost:8000/api/countries?persona=investor
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoints
ab -n 100 -c 10 http://localhost:8000/api/countries
```

## 🔄 Updates & Maintenance

### 1. Data Updates
```bash
# Replace CSV files in data/ directories
cp new_data.csv data/infrastructure/

# Restart system to reload data
python start_system.py fullstack
```

### 2. System Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update configuration
nano config.yaml

# Restart system
```

### 3. Log Management
```bash
# View logs
tail -f logs/fvi.log

# Rotate logs (add to crontab)
find logs/ -name "*.log" -mtime +30 -delete
```

## 🆘 Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :8501

# Kill process
sudo kill -9 <PID>
```

2. **Import Errors**
```bash
# Check Python path
echo $PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

3. **Data Loading Issues**
```bash
# Regenerate sample data
python create_sample_data.py

# Check data directory permissions
ls -la data/
```

4. **Memory Issues**
```bash
# Monitor memory usage
htop

# Reduce cache size in config.yaml
performance:
  memory_limit_mb: 1024
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=True python start_system.py

# Check system status
python start_system.py test
```

## 📞 Support

### Documentation
- **Main README**: System overview and features
- **API Docs**: http://localhost:8000/docs (when running)
- **Configuration**: Detailed config.yaml comments

### Getting Help
1. Check the logs: `tail -f logs/fvi.log`
2. Run system tests: `python start_system.py test`
3. Review configuration: Ensure all required fields are set
4. Check data: Verify CSV files are properly formatted

---

**Version**: 2.0.0  
**Last Updated**: August 2025  
**Status**: Production Ready ✅
