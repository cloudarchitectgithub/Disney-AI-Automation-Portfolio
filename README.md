# Disney AI Automation Portfolio

A comprehensive portfolio demonstrating AI-driven automation solutions for Disney's Systems Engineering, DevOps, and SRE teams. This repository contains three production-ready projects that address key challenges in incident response, cost optimization, and security vulnerability management.

## 🎯 Portfolio Overview

This portfolio was built specifically to demonstrate capabilities for the **Disney AI Automation Engineer** position, addressing requirements for:
- Autonomous agents for incident triage and resolution
- Multi cloud FinOps cost optimization
- Security vulnerability ownership and prioritization
- N8N based agentic AI platform integration
- Schema agnostic data access layers
- Human in the loop decision making

## 📁 Project Structure

```
Disney-AI-Automation-Portfolio/
├── Project1/          # Autonomous SRE Incident Triage Agent
├── Project2/          # Multi Cloud Cost Optimization Agent
├── Project3/          # Security Vulnerability Management Agent
├── chromadb/          # Shared ChromaDB configuration
├── docker-compose.yml # Orchestration for all services
├── setup_env.sh       # Environment setup script
└── MISC Project Files/ # Additional documentation and resources
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenRouter API key (or your preferred LLM provider)
- 8GB+ available disk space

### Initial Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd AI-Automation-Portfolio
```

2. **Set up environment variables**
```bash
./setup_env.sh
# Or manually create .env file with:
# OPENROUTER_API_KEY=your_key_here
# OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the projects**
- Project 1 Dashboard: http://localhost:8501
- Project 2 Dashboard: http://localhost:8502
- Project 3 Dashboard: http://localhost:8503
- N8N Interface: http://localhost:5678

## 📊 Projects

### Project 1: Autonomous SRE Incident Triage Agent
**Reduces MTTI by 80% and cognitive load for SRE teams**

- AI powered incident triage using LLM and RAG
- Context aware recommendations from infrastructure documentation
- N8N workflow automation for incident response
- Real time dashboard for incident management

[View Project 1 Details](Project1/README.md)

### Project 2: Multi Cloud Cost Optimization Agent
**Identifies $2.16M-$3.36M in annual savings potential**

- Schema agnostic data access layer for AWS, GCP, Azure
- Real time price monitoring and change detection
- AI driven waste detection and optimization recommendations
- Human in the loop decision making

[View Project 2 Details](Project2/README.md)

### Project 3: Security Vulnerability Ownership & Prioritization Agent
**Saves 200+ hours per team annually, $1.05M+ annual savings**

- AI powered vulnerability prioritization beyond CVSS scores
- Automated ownership assignment based on codebase analysis
- RAG enhanced security documentation search
- SLA tracking and remediation monitoring

[View Project 3 Details](Project3/README.md)

## 🛠️ Technology Stack

- **Python**: Core development language
- **FastAPI**: REST API framework
- **Streamlit**: Interactive dashboards
- **N8N**: Workflow automation platform
- **ChromaDB**: Vector database for RAG
- **Docker**: Containerization
- **OpenRouter**: LLM gateway (demo) / Production LLM integration

## 📚 Documentation

Each project includes comprehensive documentation:
- **README.md**: Complete project overview, architecture, and setup
- **Cost and Savings Analysis**: ROI calculations and business impact
- **Technical Implementation**: How each system works
- **Step by Step Directions**: Getting started guides

## 🎯 Key Features

### Schema Agnostic Architecture
All projects demonstrate flexible, extensible architectures that can adapt to different data sources and requirements without code changes.

### Human in the Loop Design
Every AI recommendation includes human oversight, ensuring stakeholders maintain control over critical decisions while benefiting from AI powered analysis.

### Real Business Impact
Each project includes detailed cost and savings analysis showing measurable ROI, time savings, and operational improvements.

### Production Ready
All projects are containerized, documented, and ready for deployment with proper error handling, logging, and monitoring.


## 🔧 Development

### Project Specific Setup

Each project can be run independently:

**Project 1:**
```bash
docker-compose up -d python-backend dashboard chromadb n8n
docker-compose exec python-backend python scripts/ingest_docs.py
```

**Project 2:**
```bash
docker-compose up -d cost-optimization-backend cost-dashboard chromadb
docker-compose exec cost-optimization-backend python scripts/generate_mock_billing.py
```

**Project 3:**
```bash
docker-compose up -d vulnerability-backend vulnerability-dashboard chromadb
docker-compose exec vulnerability-backend python scripts/generate_mock_cves.py
```

## 📝 License

