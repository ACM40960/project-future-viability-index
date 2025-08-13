# Future Viability Index (FVI) – RAG-Enhanced Coal Industry Assessment

> **Version:** FVI_V2 – with Retrieval-Augmented Generation (RAG) Agent, OpenAI GPT-4o-mini integration, and updated project structure.

---

## 📑 Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Directory Structure](#directory-structure)
5. [Installation & Setup](#installation--setup)
6. [Usage](#usage)
7. [Development Notes](#development-notes)
8. [License](#license)
9. [Authors](#authors)

---

## 📌 Project Overview
The **Future Viability Index (FVI)** is a decision-support framework designed to assess the sustainability, resilience, and long-term viability of coal-dependent economies.

This tool combines:
- **Data ingestion & scoring models** across economic, ecological, infrastructure, and social dimensions.
- **Retrieval-Augmented Generation (RAG)** with **OpenAI GPT-4o-mini** to provide contextual, knowledge-backed insights.
- **Interactive UI** for investors, policymakers, and researchers.

---

## ✨ Features
- **Modular Scoring** – Individual Python modules for different sustainability dimensions.
- **RAG Agent** – Retrieves relevant knowledge from `fvi_knowledge.txt` in `vectorstore/` before answering.
- **ChromaDB & FAISS** – Efficient semantic search over embedded domain knowledge.
- **Streamlit Frontend** – User-friendly interactive interface.
- **FastAPI Backend** – High-performance API for chat and data processing.
- **Extensible Knowledge Base** – Easily update domain-specific content.

---

## 🏗 Architecture

```
[Frontend (Streamlit)] ⇄ [FastAPI Backend] ⇄ [RAG Agent] ⇄ [Vectorstore (FAISS/ChromaDB)]
                                     ⇓
                               [Scoring Modules]
                                     ⇓
                          [Coal Viability Insights]
```

---

## 📂 Directory Structure

```
FVI/
│── assets/                  # Static assets (logo, etc.)
│── backend/                 # Backend FastAPI app & RAG agent
│── data/                    # Raw and processed data folders
│── docs/                    # Documentation and system guides
│── guides/                  # How-to guides
│── logs/                    # Log files
│── old_version_files/       # Deprecated scripts & older versions
│── scores/                  # Scoring modules for FVI
│── scripts/                 # Helper scripts (build vectorstore, validation, etc.)
│── vectorstore/             # Knowledge base and embeddings
│── .env.template            # Environment variable template
│── config.yaml              # Configuration file
│── main.py                  # Streamlit frontend entry point
│── requirements.txt         # Python dependencies
│── README.md                # Project documentation
```

---

## ⚙ Installation & Setup

### 1️⃣ Clone Repository
```bash
git clone <your-repo-url>
cd FVI
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate     # Mac/Linux
.venv\Scripts\activate        # Windows (PowerShell)
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment
Copy `.env.template` to `.env` and fill in:
```ini
OPENAI_API_KEY=your_openai_api_key
```

### 5️⃣ Build Vectorstore
```bash
python scripts/build_vectorstore.py
```

---

## 🚀 Usage

### Run Backend
```bash
uvicorn backend.main:app --reload --port 8080
```

**Health Check**
```bash
curl http://localhost:8080/healthz
```

**Test Chat API**
```bash
curl -X POST "http://localhost:8080/api/chat"   -H "Content-Type: application/json"   -d '{"message":"Coal outlook for India in the next 5 years","persona":"investor"}'
```

### Run Frontend
```bash
streamlit run main.py
```

---

## 🛠 Development Notes
- Always rebuild vectorstore after updating `fvi_knowledge.txt`.
- Keep `.venv` and `.env` out of Git (`.gitignore` already configured).
- Use `FVI_V2` branch for latest RAG-integrated development.

---

## 📜 License
© 2025 Darwin & Goliath Ltd. All rights reserved.  
This work was developed as part of an academic–industry collaboration with the MSc Data and Computational Science programme, University College Dublin.  
Any reproduction, distribution, or use of the material without prior written permission is prohibited.

---

## 👥 Authors

| Name | Student ID | Email |
|------|------------|-------|
| Rahul Babu | 24203075 | *email_here* |
| Ujwal Mojidra | 24214941 | *email_here* |
| Anshu Kumar | 24203717 | *email_here* |
| Rudra Nirmal Rawat | 24205441 | *email_here* |
| Sharvari Khatavkar | 24203968 | *email_here* |

---
