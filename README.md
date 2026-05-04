# RAG Pipeline — Production-Ready Retrieval-Augmented Generation

A production-grade Retrieval-Augmented Generation (RAG) pipeline built with **LangChain**, powered by **AWS Bedrock** for both LLM inference and embeddings, and backed by a persistent **ChromaDB** vector store. The system ingests PDFs, Word documents, plain text, Markdown, CSV, HTML, PowerPoint, Excel, and live web pages, then answers natural-language questions grounded in that knowledge base — with citations.

---

## Table of Contents

1. [What is RAG?](#what-is-rag)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Project Structure](#project-structure)
5. [Quickstart](#quickstart)
6. [Configuration](#configuration)
7. [Document Ingestion](#document-ingestion)
8. [Querying the Pipeline](#querying-the-pipeline)
9. [API Reference](#api-reference)
10. [Concept Deep-Dive](#concept-deep-dive)
11. [Production Deployment](#production-deployment)
12. [Testing](#testing)
13. [Observability](#observability)
14. [Security Considerations](#security-considerations)
15. [Troubleshooting](#troubleshooting)
16. [Roadmap](#roadmap)

---

## What is RAG?

Large Language Models are trained on data with a fixed cutoff date and have no awareness of your private documents. **Retrieval-Augmented Generation** solves this by:

1. **Indexing** your documents into a vector database after converting them to numeric embeddings.
2. **Retrieving** the most relevant chunks for each user question via semantic search.
3. **Generating** an answer with the LLM, conditioned on the retrieved chunks as grounded context.

The result is an assistant that can answer questions about *your* data, cite its sources, and avoid hallucinations on factual topics.

```
                    ┌─────────────────────────────────────┐
                    │         INGESTION PIPELINE          │
 docs/urls ──►  Loader ──► Splitter ──► Embedder ──► Vector Store (Chroma)
                    └─────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │           QUERY PIPELINE            │
   question ──► Retriever ──► Prompt builder ──► LLM ──► Answer + Sources
                    └─────────────────────────────────────┘
```

---

## Architecture

The pipeline is organized into composable layers, each with a single responsibility. The **factory pattern** is used for routing inputs to the right loader, and the **service layer** isolates business logic from the API surface.

```
┌────────────────────────────────────────────────────────────────────┐
│                           FastAPI Layer                            │
│   /ingest/files  /ingest/urls  /ingest/directory  /query  /chat    │
└────────────────────────┬──────────────────────┬────────────────────┘
                         │                      │
              ┌──────────▼──────────┐  ┌────────▼─────────┐
              │ IngestionService    │  │ QueryService     │
              └──────────┬──────────┘  └────────┬─────────┘
                         │                      │
        ┌────────────────┼──────────┐    ┌──────┴──────────┐
        │                │          │    │                 │
   ┌────▼─────┐  ┌───────▼──────┐ ┌─▼────▼───┐    ┌────────▼────────┐
   │ Loader   │  │  Splitter    │ │ Vector   │    │  RAG Chains     │
   │ Factory  │─►│ (Recursive   │►│  Store   │◄───│  (LCEL)         │
   │ (PDF,    │  │  Character)  │ │ (Chroma) │    │  rag/conv chain │
   │  DOCX,   │  └──────────────┘ └────┬─────┘    └────────┬────────┘
   │  WEB...) │                        │                   │
   └──────────┘                        │                   │
                                  ┌────▼─────┐      ┌──────▼──────┐
                                  │ Bedrock  │      │   Bedrock   │
                                  │Embeddings│      │     LLM     │
                                  └──────────┘      └─────────────┘
```

---

## Key Features

- **Multi-format ingestion** — PDF, DOCX, DOC, TXT, MD, CSV, HTML, PPTX, XLSX, and web URLs.
- **AWS Bedrock** — Use any Bedrock-hosted model (Anthropic Claude, Amazon Titan, Llama, Mistral) for both generation and embeddings.
- **ChromaDB persistence** — Disk-backed vector index that survives restarts; configurable distance metric.
- **LangChain LCEL chains** — Composable, type-safe pipelines with both sync and async invocation.
- **MMR retrieval** — Maximal Marginal Relevance for diverse, non-redundant context.
- **Conversational RAG** — Multi-turn chat with automatic question rewriting.
- **Production hardening** — Structured logging, retry/backoff on Bedrock, custom exceptions, input validation, and health/readiness endpoints.
- **Containerised** — Multi-stage Dockerfile + Docker Compose with optional Redis cache.
- **Tested** — Unit + integration test scaffolding with pytest fixtures.
- **CLI tools** — Standalone scripts to ingest and query without spinning up the API.

---

## Project Structure

```
rag_pipeline/
├── README.md                  ← You are here
├── requirements.txt           ← Pinned dependencies
├── pyproject.toml             ← Tooling config (black, mypy, pytest)
├── Makefile                   ← Common dev commands
├── Dockerfile                 ← Multi-stage production image
├── docker-compose.yml         ← Local stack incl. optional Redis
├── .env.example               ← Template environment configuration
├── .gitignore
│
├── config/                    ← Application configuration
│   ├── settings.py            ← Pydantic Settings - single source of truth
│   └── logging_config.py      ← Structlog setup (JSON in prod, color in dev)
│
├── src/                       ← Application code
│   ├── main.py                ← Uvicorn entrypoint
│   │
│   ├── core/                  ← Cross-cutting primitives
│   │   ├── exceptions.py      ← Domain exceptions
│   │   └── constants.py       ← Enums, metadata keys
│   │
│   ├── loaders/               ← Document ingestion
│   │   ├── base_loader.py             ← ABC for loaders
│   │   ├── pdf_loader.py
│   │   ├── docx_loader.py
│   │   ├── text_loader.py             ← txt + markdown
│   │   ├── csv_loader.py              ← csv, html, pptx, xlsx
│   │   ├── web_loader.py
│   │   └── document_loader_factory.py ← Routes source -> loader
│   │
│   ├── splitters/             ← Chunking
│   │   └── text_splitter.py   ← RecursiveCharacterTextSplitter wrapper
│   │
│   ├── embeddings/            ← Embedding model
│   │   └── bedrock_embeddings.py
│   │
│   ├── llm/                   ← LLM client
│   │   └── bedrock_llm.py     ← ChatBedrock wrapper
│   │
│   ├── vectorstore/           ← Vector DB
│   │   └── chroma_store.py    ← Chroma wrapper
│   │
│   ├── retrievers/
│   │   └── retriever.py       ← Builds similarity / MMR / threshold retrievers
│   │
│   ├── prompts/
│   │   └── templates.py       ← System and chat prompts
│   │
│   ├── chains/                ← LangChain LCEL chains
│   │   ├── rag_chain.py             ← One-shot Q&A
│   │   └── conversational_chain.py  ← Multi-turn with rewrite
│   │
│   ├── services/              ← Application services
│   │   ├── ingestion_service.py
│   │   └── query_service.py
│   │
│   ├── utils/                 ← Logger, helpers, validators
│   │
│   └── api/                   ← FastAPI surface
│       ├── app.py             ← Application factory
│       ├── models/            ← Request / response schemas
│       ├── routes/            ← health, ingestion, query
│       └── middleware/        ← Centralized error handler
│
├── scripts/                   ← Operational CLIs
│   ├── ingest.py
│   └── query.py
│
├── tests/                     ← Pytest suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── data/                      ← Local data dirs (git-ignored)
│   ├── raw/
│   └── processed/
│
├── chroma_db/                 ← Persistent ChromaDB (git-ignored)
└── logs/
```

---

## Quickstart

### 1. Prerequisites

- Python **3.10+**
- AWS account with **Bedrock model access** enabled in the chosen region
- (Optional) Docker & Docker Compose

### 2. Clone & install

```bash
git clone <your-repo> rag_pipeline
cd rag_pipeline

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set AWS credentials and BEDROCK_*_MODEL_ID
```

### 4. Run the API

```bash
make run
# or:
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

Browse the interactive docs at **http://localhost:8000/api/v1/docs**.

### 5. Ingest a document and query it

```bash
# Drop a file into data/raw/ then:
python -m scripts.ingest --directory data/raw

# Ask a question
python -m scripts.query "Summarize the main points of the document"

# Or interactive chat
python -m scripts.query --interactive
```

---

## Configuration

All configuration lives in `.env` and is loaded by `config/settings.py` via **pydantic-settings**, with type validation. Below are the most important variables — see `.env.example` for the full list.

| Variable                           | Purpose                                            | Default                                          |
|------------------------------------|----------------------------------------------------|--------------------------------------------------|
| `ENVIRONMENT`                      | `development` \| `staging` \| `production`         | `development`                                    |
| `LOG_LEVEL`                        | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`        | `INFO`                                           |
| `AWS_REGION`                       | Region where Bedrock is enabled                    | `us-east-1`                                      |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credentials (or use `AWS_PROFILE`)      | —                                                |
| `BEDROCK_LLM_MODEL_ID`             | Generation model                                   | `anthropic.claude-3-5-sonnet-20240620-v1:0`      |
| `BEDROCK_EMBEDDING_MODEL_ID`       | Embedding model                                    | `amazon.titan-embed-text-v2:0`                   |
| `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` | Generation sampling                              | `0.0` / `4096`                                   |
| `CHROMA_PERSIST_DIRECTORY`         | On-disk path for the index                         | `./chroma_db`                                    |
| `CHROMA_COLLECTION_NAME`           | Collection name                                    | `rag_documents`                                  |
| `CHUNK_SIZE` / `CHUNK_OVERLAP`     | Splitter parameters (chars)                        | `1000` / `200`                                   |
| `RETRIEVER_K` / `RETRIEVER_SEARCH_TYPE` | Top-K and `similarity` \| `mmr` \| `similarity_score_threshold` | `5` / `mmr`                |
| `RETRIEVER_FETCH_K` / `RETRIEVER_LAMBDA_MULT` | MMR diversity controls                  | `20` / `0.5`                                     |

### Choosing models

Open the [Bedrock console](https://console.aws.amazon.com/bedrock/) → **Model access** → request access to:
- An Anthropic Claude model (recommended for generation)
- `amazon.titan-embed-text-v2:0` (recommended for embeddings)

Pricing differs per model — check the [AWS pricing page](https://aws.amazon.com/bedrock/pricing/) before deploying at scale.

---

## Document Ingestion

The ingestion pipeline can take three kinds of inputs: **a single file**, **a URL**, or **an entire directory**.

### From the CLI

```bash
# Single file
python -m scripts.ingest --file data/raw/handbook.pdf

# URL
python -m scripts.ingest --url https://docs.python.org/3/tutorial/index.html

# Whole directory (recursive by default)
python -m scripts.ingest --directory data/raw
```

### Programmatically

```python
from src.services.ingestion_service import IngestionService

svc = IngestionService()
svc.ingest_source("data/raw/spec.docx")
svc.ingest_source("https://en.wikipedia.org/wiki/Retrieval-augmented_generation")
svc.ingest_directory("data/raw", recursive=True)

print(svc.stats())
# {'collection': 'rag_documents', 'persist_directory': './chroma_db', 'vector_count': 142}
```

### Supported formats

| Extension | Loader                         | Notes                                       |
|-----------|--------------------------------|---------------------------------------------|
| `.pdf`    | `PyPDFLoader` (pypdf)          | One Document per page, page metadata kept   |
| `.docx`   | `Docx2txtLoader`               | Fast plain-text extraction                  |
| `.doc`    | `UnstructuredWordDocumentLoader` | Requires libreoffice/antiword             |
| `.txt`    | `TextLoader`                   | Auto-detects encoding                       |
| `.md`     | `UnstructuredMarkdownLoader`   | Preserves heading hierarchy                 |
| `.csv`    | `CSVLoader`                    | One Document per row                        |
| `.html`   | `BSHTMLLoader`                 | BeautifulSoup-based                         |
| `.pptx`   | `UnstructuredPowerPointLoader` | Per-slide content                           |
| `.xlsx`   | `UnstructuredExcelLoader`      | Element mode for cell-level granularity     |
| URL       | `WebBaseLoader`                | HTTP(S) only, 30s timeout                   |

---

## Querying the Pipeline

### One-shot query

```python
from src.services.query_service import QueryService

result = QueryService().query("What is MMR retrieval?")
print(result["answer"])
for src in result["sources"]:
    print("-", src["metadata"]["file_name"])
```

### Conversational query (multi-turn)

```python
svc = QueryService()
history = []

q1 = "What is the company's vacation policy?"
r1 = svc.conversational_query(q1, history)
history += [{"role": "user", "content": q1},
            {"role": "assistant", "content": r1["answer"]}]

q2 = "How does it differ from sick leave?"
r2 = svc.conversational_query(q2, history)
print(r2["answer"])
print("Standalone form:", r2["standalone_question"])
```

The conversational chain rewrites follow-ups (`"How does it differ from sick leave?"`) into self-contained queries (`"How does the vacation policy differ from sick leave?"`) before retrieval, dramatically improving retrieval recall on multi-turn conversations.

---

## API Reference

All endpoints are mounted at the configured `API_PREFIX` (default `/api/v1`).

### Health

| Method | Path        | Purpose                                 |
|--------|-------------|-----------------------------------------|
| GET    | `/health`   | Lightweight liveness probe              |
| GET    | `/ready`    | Readiness — also pings the vector store |
| GET    | `/stats`    | Vector count and collection metadata    |

### Ingestion

```http
POST /api/v1/ingest/files           # multipart upload, multiple files
POST /api/v1/ingest/urls            # JSON: { "urls": ["..."] }
POST /api/v1/ingest/directory       # JSON: { "directory": "/path", "recursive": true }
DELETE /api/v1/ingest/document      # JSON: { "document_id": "..." }
DELETE /api/v1/ingest/source        # JSON: { "source": "/path/or/url" }
```

### Query

```http
POST /api/v1/query                  # JSON: { "question": "...", "k": 5, "search_type": "mmr" }
POST /api/v1/query/chat             # JSON: { "question": "...", "chat_history": [...] }
```

### Example — curl

```bash
# Ingest URLs
curl -X POST http://localhost:8000/api/v1/ingest/urls \
     -H "Content-Type: application/json" \
     -d '{"urls":["https://example.com/article"]}'

# Upload files
curl -X POST http://localhost:8000/api/v1/ingest/files \
     -F "files=@data/raw/handbook.pdf" \
     -F "files=@data/raw/spec.docx"

# Query
curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"question":"What is RAG?","k":5,"search_type":"mmr"}'
```

---

## Concept Deep-Dive

### 1. Loaders

A loader's only job is to turn a source (file path or URL) into a list of `langchain_core.documents.Document` instances. Every loader inherits from `BaseDocumentLoader`, which adds **uniform metadata** (`source`, `file_name`, `file_type`, `document_id`, `ingested_at`) to every chunk.

The **`DocumentLoaderFactory`** routes a source to the right concrete loader using the file extension or by detecting an `http(s)://` URL — callers never instantiate loaders directly.

### 2. Splitting (Chunking)

LLMs and embedding models have a maximum context length, and even within that limit, smaller chunks improve retrieval precision. We use LangChain's **`RecursiveCharacterTextSplitter`** which prefers semantically meaningful boundaries (paragraphs → lines → sentences → words → characters).

Two key parameters:
- **`chunk_size`** (default 1000 chars) — target chunk size.
- **`chunk_overlap`** (default 200 chars) — overlap between consecutive chunks so concepts spanning the boundary aren't lost.

Each chunk inherits its parent document's metadata and is enriched with `chunk_index` / `total_chunks` for traceability.

### 3. Embeddings

Embeddings are dense numeric vectors that capture semantic meaning. Two pieces of text with similar meaning will have vectors close together in the high-dimensional embedding space. We use **Amazon Titan Embeddings v2** by default, but any Bedrock-supported embedding model works by changing `BEDROCK_EMBEDDING_MODEL_ID`.

The `BedrockEmbeddingsService` wraps `langchain_aws.BedrockEmbeddings` with:
- A configured `boto3` client with adaptive retries.
- `tenacity`-driven retry/backoff on transient `ClientError` / `BotoCoreError`.
- Domain-specific exceptions so callers can react cleanly to embedding failures.

### 4. Vector store (ChromaDB)

ChromaDB stores `(vector, document, metadata)` triples and supports approximate nearest-neighbour search. We use it in **persistent mode** — the index is written to `CHROMA_PERSIST_DIRECTORY` and survives restarts.

Distance metrics supported: `cosine` (default — recommended for normalized text embeddings), `l2`, and `ip` (inner product).

### 5. Retrieval strategies

The retriever decides which chunks are sent to the LLM as context. We support three strategies:

- **`similarity`** — Plain cosine top-K. Fast and simple.
- **`mmr` (Maximal Marginal Relevance)** — Iteratively selects chunks that are *both* relevant to the query *and* diverse from already-selected chunks. Use this when documents contain a lot of repeated content. Tune with `lambda_mult`: `0.0` = max diversity, `1.0` = max relevance (≈ similarity).
- **`similarity_score_threshold`** — Returns only chunks whose similarity exceeds `RETRIEVER_SCORE_THRESHOLD`. Use when you'd rather return *nothing* than low-quality context.

### 6. Prompting

Prompts are stored in `src/prompts/templates.py`. The system prompt:

- Forbids the LLM from using prior knowledge.
- Asks for `[source: filename]` citations on every fact.
- Tells the model to admit ignorance instead of hallucinating.

A second prompt — `QUESTION_REWRITE_PROMPT` — converts conversational follow-ups into standalone questions before retrieval.

### 7. Chains (LCEL)

We compose pipelines with the **LangChain Expression Language**. Composition is type-safe, supports `.invoke()` / `.ainvoke()` / `.batch()` / `.stream()` uniformly, and produces inspectable graph structures.

The one-shot RAG chain:

```python
question
  └─► RunnableParallel({"docs": retriever, "question": passthrough})
        └─► format_docs_as_context
              └─► RunnableParallel({
                    "answer":  RAG_PROMPT | LLM | StrOutputParser(),
                    "sources": pass docs through,
                    "question": pass question through,
                  })
```

The conversational chain adds a **rewrite step** before retrieval and threads `chat_history` into the final prompt via `MessagesPlaceholder`.

### 8. Services

The `IngestionService` and `QueryService` are the *only* layer the API/CLI talk to. This isolation means you can swap FastAPI for gRPC, or add a Streamlit front-end, without touching the chains.

### 9. Error handling

Every domain failure raises a typed `RAGPipelineException` subclass with a machine-readable `error_code` and HTTP `status_code`. The FastAPI middleware in `src/api/middleware/error_handler.py` catches them and returns clean JSON envelopes — stack traces never leak to the client.

### 10. Logging

`structlog` produces colored human output in development and JSON in production, ready for ingestion into CloudWatch / Loki / Datadog. Log lines include `request_path`, `error_code`, `model_id`, etc.

---

## Production Deployment

### Docker Compose (single host)

```bash
cp .env.example .env
# fill in AWS_* values

docker-compose up -d --build
docker-compose logs -f rag-api
```

The Compose file mounts `./data`, `./chroma_db`, and `./logs` so state persists across container restarts. An optional Redis service is included for future query caching.

### Kubernetes

The same image runs on Kubernetes. Recommended deployment:
- 2+ replicas of the API behind a Service / Ingress.
- A **PersistentVolumeClaim** mounted at `/app/chroma_db` with `ReadWriteOnce` (or use a managed vector DB such as Pinecone/Weaviate/OpenSearch for multi-replica).
- Liveness probe: `GET /api/v1/health` ; readiness probe: `GET /api/v1/ready`.
- Resource requests: 1 CPU / 1 GiB RAM per replica baseline; scale based on document corpus size.
- IRSA (IAM Roles for Service Accounts) — mount AWS credentials via a service account rather than env vars.

### Scaling notes

- **ChromaDB single-writer constraint** — Chroma's persistent client is process-local. For horizontal scale, either run **Chroma in server mode** (`chromadb run`) and point all replicas at it, or migrate to a managed vector DB such as **Pinecone**, **Weaviate**, **Qdrant**, or **Amazon OpenSearch with k-NN**.
- **Throughput** — Bedrock has per-account rate limits; request quota increases for production workloads.
- **Caching** — Add a Redis layer in front of `BedrockEmbeddingsService` to deduplicate embedding calls for repeated queries.

---

## Testing

```bash
# Run the suite with coverage
make test

# Or directly
pytest -v --cov=src tests/
```

Tests are organized into `tests/unit/` (no AWS calls) and `tests/integration/` (FastAPI test client). The autouse `_isolate_env` fixture in `conftest.py` redirects ChromaDB and data dirs to a per-test tmp folder, ensuring tests do not pollute your real index.

---

## Observability

- **Structured logs** — `LOG_LEVEL=DEBUG` for verbose tracing of retrieval and chain execution.
- **OpenAPI / Swagger** — Live API docs at `/api/v1/docs` (Swagger) and `/api/v1/redoc` (ReDoc).
- **Health checks** — `/health` (liveness) and `/ready` (readiness, exercises the vector store).
- **Recommended additions for production**:
  - Wire up `prometheus-client` (already in `requirements.txt`) and expose a `/metrics` endpoint.
  - Add OpenTelemetry traces around retriever and LLM calls (`opentelemetry-instrumentation-fastapi`).
  - Track per-query token usage by inspecting the LLM response metadata.

---

## Security Considerations

- **Never commit `.env`** — it contains AWS credentials. Use IAM Roles for Service Accounts on EKS or instance profiles on EC2.
- **Input size limits** — `MAX_UPLOAD_SIZE_MB` caps single-file uploads; tune for your environment.
- **CORS** — Defaults to `*` in development; set `CORS_ORIGINS` to a specific allowlist in production.
- **PII** — The pipeline embeds raw text by default. If your corpus contains personally identifiable information, consider redacting it before ingestion.
- **Auth** — This template ships without auth. Add an API-key middleware or fronted with an authenticating reverse proxy (e.g., Cognito + API Gateway, OAuth2-Proxy, AWS WAF) before exposing it to the internet.
- **Rate limiting** — Add `slowapi` or fronting with an API gateway to protect against runaway costs from abusive queries.

---

## Troubleshooting

**`AccessDeniedException` from Bedrock**
You haven't enabled access to the model. Visit *Bedrock console → Model access → Manage model access*.

**`ValidationException: ... model identifier is invalid`**
The model ID isn't available in the configured `AWS_REGION`. Cross-check on the [supported models page](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html).

**Empty answers / "I don't have enough information"**
Either nothing relevant was retrieved (try smaller `CHUNK_SIZE`, larger `RETRIEVER_K`, or `search_type=similarity`) or the corpus genuinely doesn't cover the question.

**ChromaDB metadata filter errors**
Chroma metadata values must be `str | int | float | bool`. Avoid lists/dicts in metadata.

**Legacy `.doc` extraction fails**
`UnstructuredWordDocumentLoader` shells out to `libreoffice` or `antiword` for binary `.doc`. Install one (`apt install libreoffice`) or convert to `.docx` first.

**Latency seems high**
Most latency comes from Bedrock — generation typically dominates. Reduce `LLM_MAX_TOKENS`, lower `RETRIEVER_K`, or pick a faster model (e.g. Claude Haiku).

---

## Roadmap

- Streaming responses via Server-Sent Events.
- Hybrid search (BM25 + dense) using `EnsembleRetriever`.
- Reranking with a cross-encoder for a final precision boost.
- Per-user / per-tenant collection isolation.
- Async ingestion via a Celery / RQ worker queue.
- Evaluation harness with `ragas` for retrieval and answer quality metrics.

---

## License

MIT

---

*Built with LangChain, AWS Bedrock, and ChromaDB. Designed for production.*
