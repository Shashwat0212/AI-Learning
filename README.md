# RAG Engineering Execution Plan (Current Status + March Roadmap)

## Progress Status (Based on Original 24-Week Plan)

The following components from the original 24-week roadmap have already been completed:

### Completed (Old Plan Weeks 1–5)

* Transformer fundamentals (attention, GPT internals)
* LLM training concepts (pretraining, fine-tuning, RLHF – conceptual)
* Prompt engineering and LLM control
* Embeddings and vector similarity fundamentals
* Lightweight RAG v1 implementation (basic embedding search + context injection)

Outcome of Weeks 1–5:

* Clear understanding that context quality > model size for local systems
* Initial lightweight RAG prototype built
* Conceptual clarity on retrieval vs generation trade-offs

---

## Execution Plan Until End of March (6-Week Intensive Build)

Time Remaining: 6 Weeks
Goal: Move from architecture definition → production-hardened, load-tested RAG backend

Scope Compression Strategy:

* Combine logically related modules per week
* Parallelize evaluation + instrumentation early
* Defer non-critical optimizations
* Focus strictly on production-grade RAG (no agent features)

---

# 6-WEEK EXECUTION ROADMAP

---

# WEEK 1 — ARCHITECTURE + INGESTION + INDEXING

Study (6–8 hrs)

* Hybrid retrieval design patterns
* FAISS (HNSW vs Flat)
* Structure-aware chunking

Build Objectives

* Finalize ARCHITECTURE.md
* Define strict latency budget allocation
* Implement document loader
* Implement structure-aware chunking
* Generate embeddings
* Build vector index (FAISS/HNSW)
* Build BM25 index

Deliverables

* ARCHITECTURE.md
* LATENCY_BUDGET.md
* ingestion/loader.py
* ingestion/chunker.py
* retrieval/vector_index.py
* retrieval/bm25_index.py
* Index benchmark script (records build time + retrieval latency)

Branch: week01-architecture-indexing

Prompt
"I have finalized architecture and latency budgets. I want to implement ingestion, structure-aware chunking, and dual indexing (FAISS + BM25) with benchmarking instrumentation included from day one."

---

# WEEK 2 — HYBRID RETRIEVAL + METADATA FILTERING + BASIC EVAL

Study (6–8 hrs)

* Reciprocal Rank Fusion (RRF)
* Retrieval metrics (Recall@k, MRR)

Build Objectives

* Implement metadata filtering
* Implement RRF-based hybrid retrieval
* Build retrieval evaluation harness
* Create 20–30 golden retrieval queries

Deliverables

* retrieval/metadata_filter.py
* retrieval/fusion.py
* evaluation/retrieval_eval.py
* evaluation/golden_queries.json
* Recall@5 and Recall@10 report

Branch: week02-hybrid-retrieval

Prompt
"Vector and BM25 indexes are implemented. I want to add metadata filtering, hybrid retrieval with RRF, and measure Recall@k using a golden dataset."

---

# WEEK 3 — RERANKING + CONTEXT BUILDER + TOKEN CONTROL

Study (6–8 hrs)

* Cross-encoder reranking
* Extractive compression techniques
* Token budgeting strategies

Build Objectives

* Integrate cross-encoder reranker
* Implement conditional gating based on score gap
* Implement deduplication
* Implement clustering by section
* Implement extractive compression
* Enforce strict token limits

Deliverables

* reranker/cross_encoder.py
* reranker/gating.py
* context/deduplicate.py
* context/cluster.py
* context/compress.py
* context/pack.py
* nDCG comparison + latency impact report

Branch: week03-rerank-context

Prompt
"Hybrid retrieval is working. I want to add selective reranking and a context builder that deduplicates, clusters, compresses, and respects strict token budgets while tracking latency overhead."

---

# WEEK 4 — LOCAL LLM INFERENCE + FULL PIPELINE INTEGRATION

Study (6–8 hrs)

* llama.cpp integration
* Quantization trade-offs
* Tokens/sec benchmarking

Build Objectives

* Integrate GGUF inference runtime
* Benchmark 3–5 small models
* Select baseline model
* Integrate full RAG pipeline end-to-end
* Add stage-level timing hooks

Deliverables

* llm/runner.py
* model_benchmark.py
* Full pipeline script (query → answer)
* Model comparison table

Branch: week04-llm-integration

Prompt
"Retrieval, reranking, and context builder are implemented. I want to integrate a quantized local LLM, benchmark small models, and run the full pipeline end-to-end with stage timing."

---

# WEEK 5 — OBSERVABILITY + REGRESSION EVALUATION + CACHING

Study (6–8 hrs)

* p50 vs p95 measurement
* Structured logging
* LRU caching strategies

Build Objectives

* Implement stage-level timers
* Track rolling p50/p95
* Implement structured JSON logging
* Expand golden queries to 30–50
* Add answer-level evaluation (citation checks)
* Implement retrieval-level cache
* Implement optional answer cache

Deliverables

* observability/timers.py
* observability/metrics.py
* evaluation/answer_eval.py
* cache/query_cache.py
* cache/answer_cache.py
* Regression gating script (fails if p95 > 1.5s)

Branch: week05-observability-eval

Prompt
"The full RAG pipeline works. I want to add structured observability, latency percentiles, regression gating, and a two-level caching system while preserving evaluation rigor."

---

# WEEK 6 — API + DOCKER + AWS DEPLOYMENT + LOAD TESTING

Study (6–8 hrs)

* FastAPI production patterns
* Docker optimization for ML services
* EC2 deployment basics
* Load testing with Locust

Build Objectives

* Build /query endpoint
* Build /metrics endpoint
* Dockerize application
* Deploy to EC2 (CPU optimized instance)
* Configure IAM + CloudWatch logging
* Perform load testing (simulate concurrent users)
* Optimize bottlenecks until p95 ≤ 1.5s

Deliverables

* api/server.py
* Dockerfile
* docker-compose.yml
* deployment/aws_architecture.md
* deployment/load_test.py
* Final latency + load report

Branch: week06-deployment-loadtest

Prompt
"The RAG backend is production-ready locally. I want to containerize it, deploy on AWS EC2, run load tests, and optimize until p95 latency remains under 1.5 seconds under realistic concurrent load."

---

# END OF MARCH STATE

At the end of 6 weeks:

* Fully engineered hybrid RAG backend
* Selective reranking + context optimization
* Strict latency instrumentation (p95 ≤ 1.5s)
* Regression-gated evaluation framework
* Two-level caching
* Dockerized deployment
* AWS-hosted service
* Load-tested and performance-validated system

This represents a production-grade RAG system suitable for internal transfer discussions and external demonstration.
