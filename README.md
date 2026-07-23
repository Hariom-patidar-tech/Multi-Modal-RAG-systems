#  Enterprise Multi-Modal-RAG-Systems

> A Production-Ready, Enterprise-Grade Retrieval-Augmented Generation (RAG) Platform built with FastAPI, ChromaDB, Hybrid Search, Reranking, and Multiple Data Source Integration.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![LangChain](https://img.shields.io/badge/LangChain-AI-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

# 📌 Overview

This project is an advanced Retrieval-Augmented Generation (RAG) system designed for enterprise-level AI applications.

Instead of relying solely on an LLM, the platform retrieves relevant information from multiple structured and unstructured sources, reranks the retrieved results, and generates accurate, context-aware responses.

The architecture is fully modular, scalable, and production-ready.

---

# ✨ Features

-  Enterprise Grade Architecture
-  FastAPI REST APIs
-  Multi-Source Document Ingestion
-  Hybrid Search (Vector + BM25)
-  ChromaDB Vector Database
-  Advanced Reranking Pipeline
-  Semantic Search
-  Modular Folder Structure
-  Multiple File Format Support
   REST API Documentation (Swagger)
-  Configurable LLM Integration
-  Logging & Monitoring
-  Production Ready APIs

---

#  Images
<img width="259" height="449" alt="image" src="https://github.com/user-attachments/assets/d10494e8-4a9e-4807-8a0b-998badd97706" />
<img width="949" height="445" alt="image" src="https://github.com/user-attachments/assets/76b7152d-3797-430b-8b0d-b389e80fb676" />
<img width="728" height="302" alt="image" src="https://github.com/user-attachments/assets/ccda21bf-568d-418f-b90a-9629eb9a2e69" />


---

#  Project Architecture

```
                +----------------------+
                |   User Query         |
                +----------+-----------+
                           |
                           ▼
                Query Processing Layer
                           |
          +----------------+----------------+
          |                                 |
          ▼                                 ▼
   Hybrid Retriever                 BM25 Search
          |                                 |
          +----------------+----------------+
                           |
                           ▼
                    ChromaDB Search
                           |
                           ▼
                    Reranker Engine
                           |
                           ▼
                     Context Builder
                           |
                           ▼
                     Large Language Model
                           |
                           ▼
                    Final AI Response
```

---

# 📂 Project Structure

```
Multi-Source-RAG/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── rag/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   └── utils/
│
├── uploads/
├── vector_store/
├── logs/
├── tests/
│
├── main.py
├── requirements.txt
└── README.md
```

---

# ⚙ Tech Stack

## Backend

- FastAPI
- Python
- Uvicorn

## AI & NLP

- LangChain
- HuggingFace Transformers
- Sentence Transformers
- Groq LLM
- Hybrid Retrieval
- BM25

## Vector Database

- ChromaDB

## Database

- SQLAlchemy
- MySQL

## Other Tools

- Pydantic
- Docker Ready
- Logging
- REST APIs

---

# 🔄 Workflow

1. Upload Documents
2. Text Extraction
3. Chunk Generation
4. Embedding Creation
5. Store Embeddings in ChromaDB
6. User Query Processing
7. Hybrid Retrieval
8. Reranking
9. Context Generation
10. LLM Response Generation

---

# 📚 Supported Sources

- PDF
- DOCX
- TXT
- Web URLs
- Youtube url
- github url
- Knowledge Base
- Custom Documents

---

# 📡 API Endpoints

## Health

```
GET /api/v1/health
```

Check application health.

---

## Upload Documents

```
POST /api/v1/document
```

Upload and index documents.

---

## Query

```
POST /api/v1/query
```

Ask questions using Retrieval-Augmented Generation.

---

## Sources

```
GET /api/v1/source
```

Manage available data sources.

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/Hariom-patidar-tech/Multi-Modal-RAG-Systems.git

cd Multi-Modal-RAG-Systems
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
uvicorn app.main:app --reload
```

---

## Open API Docs

```
http://127.0.0.1:8000/docs
```

---

# 🔍 Retrieval Pipeline

```
User Query
      │
      ▼
Hybrid Retriever
      │
      ▼
Vector Search (ChromaDB)
      │
      ▼
BM25 Search
      │
      ▼
Merge Results
      │
      ▼
Reranker
      │
      ▼
LLM
      │
      ▼
Final Response
```

---

# 📈 Future Enhancements

- Authentication & Authorization
- Role-Based Access Control
- Streaming Responses
- Multi-Agent RAG
- Graph RAG
- Voice Query Support
- Image Retrieval
- Redis Cache
- Kubernetes Deployment

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Push to GitHub
5. Create a Pull Request

---


---

# 👨‍💻 Author

**Hariom Patidar**

AI/ML Engineer | FastAPI Developer | RAG Systems | NLP | Vector Databases

GitHub: https://github.com/Hariom-patidar-tech

LinkedIn: https://www.linkedin.com/in/hariom-patidar-6574ba290/

---

⭐ If you found this project useful, don't forget to star the repository!
