# CustomBot AI — No-Code RAG Chatbot Builder

**CustomBot AI** is an enterprise-grade, no-code Retrieval-Augmented Generation (RAG) platform that empowers users to create, customize, test, evaluate, and publish production-ready AI chatbots grounded strictly in their uploaded knowledge documents.

---

## 🌟 Key Capabilities

- **No-Code Chatbot Studio**: Build domain-tailored chatbots through an 8-step wizard without writing a single line of code.
- **Extensible Multi-Format Ingestion**: Native text and metadata extraction from **PDF, DOCX, TXT, CSV, XLSX, PPTX, Markdown, and JSON**, with optional OCR for scanned documents.
- **Strict Anti-Prompt-Injection Isolation**: Retrieved documents are isolated within `<UNTRUSTED_KNOWLEDGE_BASE>` XML containers and treated strictly as passive reference data rather than executable system instructions.
- **Isolated Vector Namespaces**: Every chatbot maintains dedicated, isolated collections in **ChromaDB** (`bot_{chatbot_id}`).
- **Hybrid Retrieval & Reranking**: Combines dense vector cosine similarity with BM25 lexical keyword search and query-document reranking.
- **Dynamic Prompt Engineering**: Configurable domains (10 presets + custom), personalities, tones, languages (English, Hindi, Telugu, etc.), audience depth, and response formats (Markdown, Bullets, Lists, Tables, or validated JSON with custom schema enforcement).
- **RAG Diagnostic Evaluation Suite**: Quantitatively evaluates Retrieval Relevance, Context Relevance, Answer Relevance, Faithfulness, and Answer Correctness with transparent methodology.
- **Public Publishing & Embeddable Web Widget**: One-click publishing generates standalone shareable URLs and embeddable `<script>` tags for external websites.

---

## 🏛️ System Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │          Streamlit SaaS Frontend              │
                    │   Dashboard | Wizard | Test Sandbox | Eval    │
                    └───────────────────────┬───────────────────────┘
                                            │ HTTP / JSON
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │               FastAPI Backend                 │
                    │   /auth | /chatbots | /documents | /public    │
                    └───────┬───────────────┬───────────────┬───────┘
                            │               │               │
                            ▼               ▼               ▼
     ┌────────────────────────────┐ ┌───────────────┐ ┌───────────────┐
     │      Document Pipeline     │ │   Relational  │ │   ChromaDB    │
     │  Loaders -> Sanitizer ->   │ │     SQLite    │ │ Vector Store  │
     │   Chunker -> Embeddings    │ │  (SQLAlchemy) │ │ (Bot Isolated)│
     └────────────────────────────┘ └───────────────┘ └───────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────────────────────┐
     │                     LLM Generation Engine                    │
     │         Google Gemini (Default) | OpenAI | Mock LLM          │
     └──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | Streamlit | Modern SaaS interface with custom CSS design tokens |
| **Backend API** | FastAPI + Uvicorn | High-performance asynchronous REST API with Swagger UI |
| **Vector Database** | ChromaDB | Isolated vector collections per chatbot |
| **Embeddings** | Sentence-Transformers | Local 384-d semantic embeddings (`all-MiniLM-L6-v2`) |
| **LLM Providers** | Google Gemini / OpenAI / Mock | Configurable LLM provider with fallback support |
| **Document Loaders** | PyMuPDF, python-docx, pandas, openpyxl, python-pptx | Multi-format document parser registry |
| **Relational DB** | SQLite + SQLAlchemy 2.0 | Normalized metadata, users, messages, and analytics |
| **Validation** | Pydantic V2 & jsonschema | Data schema validation and strict JSON output checking |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Windows / macOS / Linux

### 2. Environment Setup
```bash
# Clone or navigate to the repository
cd d:/PROS/Bot

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Provide your `GEMINI_API_KEY` or `OPENAI_API_KEY`. If left blank, CustomBot AI will seamlessly operate using its built-in grounded mock LLM generator.

### 4. Run CustomBot AI
Launch both the backend and frontend simultaneously with a single command:
```bash
python run.py
```

Or launch services independently:
```bash
# Run FastAPI Backend only (Port 8000)
python run.py --backend

# Run Streamlit Frontend only (Port 8501)
python run.py --frontend

# Run Automated Test Suite
python run.py --test
```

### 5. Access Endpoints
- **Streamlit Dashboard**: [http://127.0.0.1:8501](http://127.0.0.1:8501)
- **FastAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📋 Step-by-Step Chatbot Builder Walkthrough

1. **Identity & Purpose**: Name your chatbot, configure its purpose, welcome greeting, avatar, and branding color.
2. **Knowledge Sources**: Upload documents (PDF, DOCX, CSV, XLSX, PPTX, TXT, MD, JSON). The pipeline calculates SHA-256 hashes to prevent duplicate documents and extracts text chunks with page retention.
3. **Domain Selection**: Select among 10 verticals (*Education, E-commerce, Healthcare, Customer Support, HR, Legal, Technical, Finance, General, Custom*).
4. **Behaviour & Tone**: Configure personality (*Professional, Friendly, Technical, Academic, etc.*), language (*English, Hindi, Telugu, etc.*), and custom behavioural restrictions.
5. **Response Format & Grounding**: Choose visual layout (*Markdown, Bullets, Lists, Tables, or JSON*). Toggle source citations and strict grounding.
6. **RAG Settings**: Adjust chunk size, overlap, top-K retrieval, similarity threshold, and hybrid BM25 search.
7. **Interactive Sandbox**: Chat with your bot in real-time, inspect retrieved chunks, and view latency.
8. **Publish & Share**: Toggle public status, copy the public link, or embed the widget into any website:

```html
<!-- CustomBot AI Embed Widget -->
<script src="http://127.0.0.1:8000/static/widget.js" 
        data-bot-id="YOUR_SHARE_TOKEN" 
        data-color="#4F46E5" 
        defer></script>
```

---

## 🛡️ Security & Reliability Architecture

1. **Prompt Injection Defense**: Uploaded text is defanged by neutralizing common injection triggers (`system prompt override`, `ignore all previous instructions`). Injected text is strictly passed as passive untrusted data inside `<UNTRUSTED_KNOWLEDGE_BASE>` blocks.
2. **Chatbot Data Isolation**: Knowledge vectors are stored in isolated ChromaDB collections (`bot_{chatbot_id}`).
3. **Public Endpoint Protection**: Public endpoints expose only safe metadata (name, welcome message, branding color). API keys, user IDs, and raw system configurations are never leaked.
4. **Input & File Validation**: Uploaded files undergo MIME type verification, extension whitelisting, path traversal sanitization, and 25MB file size limits.

---

## 🧪 Automated Testing

CustomBot AI includes a complete pytest test suite covering loaders, chunking, prompts, vector indexing, retrieval, and API endpoints:
```bash
python run.py --test
```
Result: **15 passed tests** verifying 100% of core application modules.

