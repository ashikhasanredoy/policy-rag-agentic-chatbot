# 🛡️ Enterprise Policy RAG + Agentic AI Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://www.langchain.com/langgraph)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red.svg)](https://qdrant.tech/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb.svg)](https://react.dev/)

An enterprise-grade, production-style **Company Policy Assistant** powered by **LangGraph Agentic Orchestration**, **OLMo Language Model**, **Hybrid Retrieval (Qdrant Vector DB + BM25 Lexical Index)**, **Reciprocal Rank Fusion (RRF)**, **Cross-Encoder Reranking**, and strict **Answerability & Faithfulness Guardrails**.

---

## 🌟 Core Philosophy: *"No Evidence → No Answer"*

Unlike generic chatbots that hallucinate plausible answers when documents lack explicit facts, this system enforces multi-stage deterministic and neural guardrails:
1. **Semantic Intent Routing**: Distinguishes general chat, small talk, broad policy overviews, and policy listings before triggering RAG retrieval.
2. **Topical Relevance Grader**: Filters out irrelevant noise from retrieved candidate chunks.
3. **Answerability Guardrail**: Checks whether facts directly address the inquiry before calling the LLM. If ungrounded or absent, it **safely abstains without hallucinating**.
4. **OLMo Grounded Synthesis**: Generates clean, point-wise structured responses based strictly on verified context.
5. **Faithfulness Verifier**: Verifies every claim against source policy context.

---

## 🔄 End-to-End Agentic Pipeline Flow

```
                                  USER INPUT
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    Semantic Intent Router     │
                      └───────────────┬───────────────┘
                                      │
          ┌─────────────────┬─────────┴─────────┬─────────────────┐
          ▼                 ▼                   ▼                 ▼
   GENERAL_CHAT      POLICY_CATEGORY       POLICY_LIST       OUT_OF_SCOPE
   (Hello, Help,     (Overview of HR,      (List all         (Weather, Code,
   Sample Questions)  Benefits, Travel)     active policies)  General Trivia)
          │                 │                   │                 │
          ▼                 ▼                   ▼                 ▼
     Direct Chat      Category Brief +     Active Policy     Polite Scope
      Response        Sample Questions        Summary         Redirect
          │                 │                   │                 │
          └─────────────────┴─────────┬─────────┴─────────────────┘
                                      │
                                      ▼
                              [ USER INTERFACE ]
                                      ▲
                                      │ (When Intent == POLICY_QUERY)
                                      │
┌─────────────────────────────────────┴───────────────────────────────────────┐
│                           AGENTIC RAG PIPELINE                              │
│                                                                             │
│  1. Query Analysis & Semantic Expansion                                     │
│     ├── Extracts domain keywords & normalizes synonyms                      │
│     └── Builds expanded query vector representation                         │
│                                                                             │
│  2. Hybrid Retrieval                                                        │
│     ├── Dense Semantic Retrieval: Qdrant Vector DB (Cosine Similarity)      │
│     └── Lexical Keyword Retrieval: Okapi BM25 Index                         │
│                                                                             │
│  3. Reciprocal Rank Fusion (RRF, k=60)                                      │
│     └── Fuses dense + sparse ranked lists: RRF(d) = Σ 1 / (k + rank_i(d))   │
│                                                                             │
│  4. Cross-Encoder Reranking                                                 │
│     └── Scores and selects top candidate context passages                   │
│                                                                             │
│  5. Relevance Grader Node                                                   │
│     └── Filters chunks below 0.60 relevance threshold                       │
│                                                                             │
│  6. Answerability Guardrail Node                                            │
│     ├── Checks explicit concept match and negative query signals            │
│     ├── [Ungrounded / Missing Evidence] ──► ABSTAIN NODE (Safe Refusal)    │
│     └── [Verified Facts Present]        ──► GENERATE NODE                   │
│                                                                             │
│  7. OLMo Synthesis Node                                                     │
│     └── Point-wise bullet synthesis strictly grounded in evidence           │
│                                                                             │
│  8. Faithfulness Verifier Node                                              │
│     ├── [Hallucination Detected] ──► Self-Correction / Retry Loop           │
│     └── [Faithful]               ──► CITATION & METADATA MAPPER             │
│                                                                             │
│  9. Citation Mapper Node                                                    │
│     └── Maps Policy Name, Section, Page, and Snippet to response            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ System Architecture

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                                 FRONTEND                                  │
│                     (React 18 + Vite, Minimalist White UI)                │
│                                                                           │
│   • Chat View with Point-wise Markdown Formatting                         │
│   • Slide-down Toggle Button for Policy Sources & Citations               │
│   • Conversation History Sidebar with on-hover Delete                     │
│   • Policy Help Modal for real-time catalog discovery                     │
│   • Real-time Verification Trace (Latency, Scores, Guardrail Status)      │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ HTTP / JSON API
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                                 BACKEND                                   │
│                           (FastAPI + Python 3.11+)                        │
│                                                                           │
│   • /api/v1/chat/                  : Multi-turn agentic chat endpoint     │
│   • /api/v1/chat/conversations     : Conversation history & deletion      │
│   • /api/v1/policies               : Policy catalog & metadata CRUD       │
│   • /api/v1/admin/                 : Analytics, index rebuild & eval      │
│   • /api/v1/health                 : Health checks & system telemetry     │
└───────────────────┬───────────────────────────────────┬───────────────────┘
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────────────┐ ┌──────────────────────────────────┐
│          RAG / VECTOR STORE          │ │             DATABASE             │
│                                      │ │                                  │
│  • Qdrant Vector Store (Dense)       │ │  • SQLite / PostgreSQL           │
│  • BM25 In-Memory Index (Sparse)     │ │  • Conversations & Messages      │
│  • HuggingFace BGE Embeddings        │ │  • Policies & Version History    │
│  • BGE Cross-Encoder Reranker        │ │  • Audit & Retrieval Logs        │
└──────────────────────────────────────┘ └──────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
policy-rag-chatbot/
│
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI endpoints (chat, policies, admin, health)
│   │   ├── core/                # Configuration, logging, security, exceptions
│   │   ├── database/            # SQLAlchemy models, SQLite/PG connection, repositories
│   │   ├── graders/             # Relevance, Answerability, Faithfulness, Citation graders
│   │   ├── graph/               # LangGraph state, nodes, conditional edges, workflow
│   │   ├── llm/                 # OLMo model pipeline & deterministic grounded engine
│   │   ├── rag/                 # Chunker, embeddings, Qdrant store, BM25, RRF, reranker
│   │   ├── router/              # Multi-intent semantic query router & classifiers
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Chat service & orchestration
│   │   └── main.py              # Application entrypoint & auto-seeding
│   ├── tests/                   # Pytest unit & integration test suites
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/          # AIMessage (with Slide Sources), UserMessage, HelpModal, etc.
│   │   ├── pages/               # Chat (Sidebar history + on-hover delete), Admin
│   │   ├── services/            # Frontend API client
│   │   ├── index.css            # Minimalist white theme styling
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── policies/                # Markdown corporate policies (HR, Remote Work, Benefits, etc.)
│   └── evaluation/              # Benchmark questions & No-Answer evaluation set
│
├── scripts/
│   ├── seed_database.py         # Ingests policy corpus into database & vector store
│   └── evaluate_rag.py          # Benchmark runner computing accuracy & recall metrics
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+
- **npm** or **yarn**

### 2. Backend Setup

```bash
# Clone the repository
git clone <repo-url>
cd policy-rag-chatbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 3. Seed Database & Vector Store

```bash
# Ingests corporate policies (HR, Benefits, IT, Travel, Remote Work, Ethics)
python3 -m scripts.seed_database
```

### 4. Run Test Suite

```bash
PYTHONPATH=. pytest backend/tests/ -v
```

### 5. Start Backend Server

```bash
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger documentation available at: `http://127.0.0.1:8000/docs`

### 6. Start Frontend Server

```bash
cd frontend
npm install
npm run dev
```
Open `http://127.0.0.1:5173` in your browser.

---

## 🧪 Testing Benchmark & Examples

### Sample Supported Queries (Returns Point-wise Answer + Citations):
- `"How many days of paid annual leave do full-time employees accrue per year?"` *(HR Policy)*
- `"What is the daily meal per diem for business travel?"` *(Travel & Expense Policy)*
- `"What is the company matching percentage for the 401(k) retirement plan?"` *(Benefits Policy)*
- `"What is the minimum character length and complexity requirement for corporate passwords?"` *(InfoSec Policy)*
- `"What is the threshold for gifts and hospitality that requires compliance approval?"` *(Ethics Policy)*

### Sample Guardrail Abstention (Zero-Hallucination):
- `"Does the company provide a monthly personal housing allowance?"`
  - **Output**: `ℹ️ I couldn't find information regarding your request in the active company policies. (Reason: Concept 'housing' not found)`
- `"Can employees bring pet dogs or cats into the office?"`
  - **Output**: `ℹ️ I couldn't find information regarding your request in the active company policies.`

---

## 🐳 Docker Deployment

Run the complete multi-service stack with a single command:

```bash
docker-compose up --build
```
