
Short explanation of those three folders:
========================================
docs/ — Project documentation that goes beyond the README. Things like architecture decision records (ADRs), API specs, sequence diagrams, deployment runbooks, model evaluation reports. Tools like MkDocs or Sphinx point at this folder to generate a static documentation site. Empty for now — you fill it as the project grows.

notebooks/ — Jupyter notebooks for experimentation: trying different chunk sizes, comparing retrievers, evaluating answer quality on a test set, debugging a tricky document, prototyping a new chain before promoting it to src/. Notebooks are great for ad-hoc analysis but should never become production code paths — they live separately so they can stay messy.

logs/ — Default destination for application log files when you redirect stdout to a file (e.g., uvicorn ... > logs/app.log) or wire up a RotatingFileHandler. Right now structlog writes to stdout, but in production you'd usually tail this folder with a sidecar (Filebeat, Fluent Bit, CloudWatch agent) that ships logs to your aggregator. The .gitkeep keeps the folder tracked in git while the actual *.log files stay ignored.

In short: docs = written docs, notebooks = experimental Jupyter work, logs = runtime log files. All three are empty placeholders that follow industry convention so contributors immediately know where each kind of artifact belongs.

===================================================================================

Both files in scripts/ are command-line entry points — they let you run the pipeline from a terminal without spinning up the FastAPI server. They are tiny: their only job is to parse CLI arguments and call the same service classes the API uses, so the heavy lifting always happens in the same place.
scripts/ingest.py — adds documents to the knowledge base
What it does: Takes a file, URL, or directory from the command line and pushes it through the ingestion pipeline (load → split → embed → store).
How you run it:
bashpython -m scripts.ingest --file data/raw/handbook.pdf
python -m scripts.ingest --url https://example.com/docs
python -m scripts.ingest --directory data/raw --recursive
Call chain when you run it:
scripts/ingest.py
   │  parses --file / --url / --directory
   ▼
src/services/ingestion_service.py    (IngestionService)
   │  orchestrates the full pipeline
   ├──► src/loaders/document_loader_factory.py
   │       └──► src/loaders/pdf_loader.py / docx_loader.py / web_loader.py / ...
   │              (extracts raw text + metadata as LangChain Documents)
   │
   ├──► src/splitters/text_splitter.py
   │       (RecursiveCharacterTextSplitter — breaks docs into 1000-char chunks
   │        with 200-char overlap, adds chunk_index/total_chunks metadata)
   │
   ├──► src/embeddings/bedrock_embeddings.py
   │       (calls AWS Bedrock Titan to convert each chunk to a vector)
   │
   └──► src/vectorstore/chroma_store.py
           (writes (vector, text, metadata) rows into ./chroma_db)
Real-world example: When you ran POST /api/v1/ingest/files with Solifi_ETU_Award_Agreement.pdf, your log showed exactly this chain:

PDFLoader — pulled out 14 pages
DocumentTextSplitter — split into 52 chunks
BedrockEmbeddingsService — converted to vectors
ChromaVectorStore.add_documents() — persisted to disk

The CLI script does the same thing, just bypassing FastAPI.

scripts/query.py — asks questions against the knowledge base
What it does: Sends a question into the RAG chain and prints the answer + sources.
How you run it:
bash# One-shot question
python -m scripts.query "What are the vesting terms?"

# With retrieval tuning
python -m scripts.query "Summarize section 3" --k 8 --search-type mmr

# Interactive REPL with chat history (multi-turn)
python -m scripts.query --interactive
Call chain when you run it:
scripts/query.py
   │  parses question + --k + --search-type / --interactive
   ▼
src/services/query_service.py    (QueryService.query or .conversational_query)
   │
   ▼
src/chains/rag_chain.py     (or conversational_chain.py for --interactive)
   │  LCEL chain composition
   │
   ├──► src/retrievers/retriever.py
   │       └──► src/vectorstore/chroma_store.py
   │              (top-K similarity / MMR search → returns relevant chunks)
   │
   ├──► src/prompts/templates.py
   │       (RAG_PROMPT — injects retrieved chunks as `{context}`)
   │
   └──► src/llm/bedrock_llm.py
           (Claude on Bedrock generates the answer with citations)
   ▼
prints answer + sources to terminal
For --interactive mode it goes through ConversationalRAGChain instead, which adds a question-rewriting step (so "what about its pricing?" becomes "what is the pricing of product X?") before retrieval.

The big picture
You have three ways to use the pipeline, all sharing the same business logic:
SurfaceFileUse caseHTTP APIsrc/api/routes/ingestion.py & query.pyProduction, frontend integrationCLI scriptsscripts/ingest.py & query.pyLocal dev, batch jobs, cronPython importIngestionService, QueryServiceNotebooks, custom apps
Notice the FastAPI route handlers and the CLI scripts both call IngestionService / QueryService — neither contains business logic of its own. That separation is why you can drop the API entirely and the CLI still works, or replace the CLI with a Streamlit UI without touching the chains. The services are the contract; everything else is just a different way to invoke them.