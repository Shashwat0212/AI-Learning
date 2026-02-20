# AskMyDocs — Hybrid Retrieval Design Blueprint → Modular Implementation Plan (v0)

> Goal: build **modules from scratch** so we can (a) **measure per-stage SLA compliance** (process-level, not end-to-end) and (b) implement **doc loading → chunking → indexing → retrieval patterns A/B/C/D → fusion → reranking → context building**, with **each pattern runnable in isolation** and comparable under varying load and constraints.

This document is intentionally **implementation-oriented** and lays out:

1. A **stage-level SLA measurement module** (first deliverable)
2. A **module-by-module architecture** that supports A/B/C/D retrieval patterns
3. **Isolated pattern pipelines** and a **permutation runner** for tradeoff experiments
4. A **project structure** and **interfaces** to keep everything swappable

---

## 0) SLA Targets (p95)

| Stage           | Budget (p95) |
| --------------- | -----------: |
| Query Embedding |        50 ms |
| Vector Search   |        40 ms |
| BM25            |        40 ms |
| Fusion          |        10 ms |
| Reranking       |       250 ms |
| Context Builder |       100 ms |

**Scope note:** This plan focuses on *process* instrumentation (module-stage timings) and functional correctness. **End-to-end load testing** will be done with tools like **JMeter** externally.

---

## 1) Deliverable #1 — SLA Measurement Module (Stage-Level)

### 1.1 Requirements

The SLA measurement module must:

* Measure **p50/p95/p99** per stage **independently**.
* Capture **timing breakdown** per request:

  * stage name
  * start/end monotonic timestamps
  * duration
  * tags: `pattern`, `tenant`, `index`, `query_type`, `cache_hit`, etc.
* Support **nested spans** (e.g., Pattern C has parallel stages).
* Support **async + parallel** execution measurement.
* Produce **structured logs** + optional export to:

  * Prometheus format (later)
  * OpenTelemetry (later)
* Provide **SLA assertions**:

  * fail-fast in tests
  * warning thresholds in dev
* Provide **overhead budget**: instrumentation should add ≤ ~1–2 ms p95.

### 1.2 Minimal API

#### Concepts

* **Trace**: one request’s timeline
* **Span**: one timed stage
* **StageSLA**: SLA budgets for stages
* **Report**: aggregated distribution stats per stage

#### Interfaces (Python-first)

* `Tracer.start_trace(request_id, tags) -> Trace`
* `Trace.span(name, tags=None)` context manager / async context manager
* `Trace.mark(name, tags=None, duration_ms=None)` for externally-measured stages
* `SLARegistry.check(report) -> SLAResult`
* `StatsAggregator.add(trace)`
* `StatsAggregator.report(window=None) -> Report`

### 1.3 Output Artifacts

* `trace.jsonl` (one line per trace, spans included)
* `metrics.json` (periodic aggregation snapshot)
* Console summary:

  * stage p50/p95/p99
  * SLA pass/fail
  * top offenders

### 1.4 Measurement Semantics

* Use **monotonic clock** for durations.
* For parallel execution:

  * Each parallel branch has its own span.
  * Also measure a parent span to capture wall-time.
* Store both:

  * wall time per stage
  * optional CPU time (later)

### 1.5 Acceptance Criteria

* Given N traces, module can compute correct percentiles.
* Given SLA targets, module flags violations.
* Works for:

  * sequential pipeline
  * parallel hybrid pipeline
  * cached stages (record `cache_hit=true` and duration)

---

## 2) Core System Modules (for AskMyDocs)

> The design is intentionally **interface-first** so patterns A/B/C/D are just *different compositions*.

### 2.1 Project Structure (suggested)

```
askmydocs/
  core/
    config.py
    types.py
    errors.py
    tracing/
      tracer.py
      stats.py
      sla.py
  ingest/
    loaders/
      text_loader.py
    splitters/
      base.py
      fixed_token.py
      sentence_aware.py
      structure_aware.py
    enrich/
      metadata.py
      hash_fingerprint.py
      summaries.py   # later: hierarchical summaries
  index/
    dense/
      embeddings.py
      hnsw.py
      ivfpq.py
      partitioning.py
    sparse/
      bm25.py
      fielded_bm25.py
    store/
      docstore.py
  retrieve/
    patterns/
      sparse_first.py
      dense_first.py
      parallel_hybrid.py
      multivector_fielded.py
    fusion/
      rrf.py
      weighted_sum.py
    rerank/
      cross_encoder.py
      heuristics.py
    context/
      builder.py
      dedupe.py
      stitching.py
    routing/
      rules.py
      router.py
  experiments/
    permutations.py
    datasets.py
    eval.py
  service/
    api.py
    cli.py
```

### 2.2 Data Types

#### Document

* `doc_id: str`
* `tenant_id: str`
* `source_uri: str`
* `text: str`
* `metadata: dict`

#### Chunk

* `chunk_id: str`
* `doc_id: str`
* `tenant_id: str`
* `text: str`
* `token_count: int`
* `span: {start, end}` offsets
* `metadata: dict` (section heading, page, etc.)
* `fingerprint: str` (hash)

#### Candidate

* `chunk_id: str`
* `score: float`
* `source: {dense|bm25|fused|reranked}`
* `metadata: dict`

---

## 3) Ingestion Modules (Text-only for now)

### 3.1 Document Loader

**Module:** `ingest/loaders/text_loader.py`

* Input: path(s) to `.txt`, `.md`, `.jsonl` (configurable)
* Output: `Iterable[Document]`
* Responsibilities:

  * detect encoding
  * normalize unicode
  * attach base metadata

### 3.2 Chunker / Splitter Variants

**Module family:** `ingest/splitters/*`

#### Baseline Interface

* `Splitter.split(doc: Document) -> list[Chunk]`

#### Implementations

1. **Fixed-size token splitter**

   * chunk sizes: 200 / 400 / 800 tokens
   * overlap: 10% / 20%

2. **Sentence-aware splitter**

   * uses sentence boundaries
   * tries to hit target token size

3. **Structure-aware splitter**

   * splits by headings/sections where possible
   * falls back to sentence-aware

> Recommended default baseline: **400–600 tokens**, **15–20% overlap**, **structure-aware**.

### 3.3 Enrichment

* `metadata.py`: extract title/heading hints, section labels
* `hash_fingerprint.py`: content hash for dedupe + caching keys
* `summaries.py` (Phase 2): hierarchical summary per section (routing/preview)

---

## 4) Index Modules

### 4.1 Dense Index

**Requirements**

* Vector search p95 ≤ 40ms
* Efficient metadata filtering
* Predictable p95

**Baseline:** HNSW + partitioning

#### Modules

* `index/dense/embeddings.py`

  * local embedder
  * query embedding cache

* `index/dense/partitioning.py`

  * index per tenant/workspace
  * resolves shard from request metadata

* `index/dense/hnsw.py`

  * ANN search
  * insertion/update

* `index/dense/ivfpq.py` (optional)

  * memory-optimized alternative

### 4.2 Sparse Index (BM25)

* `index/sparse/bm25.py`: baseline BM25
* `index/sparse/fielded_bm25.py`: separate fields (title, heading, body, code)

### 4.3 DocStore

* `index/store/docstore.py`

  * `get_chunk(chunk_id)`
  * `get_adjacent(chunk_id, window)`
  * `get_metadata(chunk_id)`

---

## 5) Retrieval Modules (Patterns A/B/C/D)

Each pattern is a **composition** of smaller modules.

### 5.1 Common Interfaces

* `Retriever.retrieve(query, filters, k) -> list[Candidate]`
* `Fusion.fuse(dense_candidates, sparse_candidates, m) -> list[Candidate]`
* `Reranker.rerank(query, candidates, n) -> list[Candidate]`
* `ContextBuilder.build(reranked, token_budget, rules) -> Context`

### 5.2 Pattern A — Sparse-First

**Pipeline**

1. BM25 retrieve top `K_s`
2. Apply metadata filter
3. (optional) Dense scoring on reduced set
4. (optional) Rerank
5. Context build

**Modules**

* `patterns/sparse_first.py`

  * `SparseRetriever` (BM25)
  * `MetadataFilter`
  * `OptionalDenseRescorer`

**Use when**

* exact string, code, logs, quoted text

### 5.3 Pattern B — Dense-First

**Pipeline**

1. ANN retrieve top `K_d`
2. Apply metadata filter
3. (optional) sparse rescoring
4. (optional) Rerank
5. Context build

**Modules**

* `patterns/dense_first.py`

  * `DenseRetriever` (partition-aware)
  * `MetadataFilter`
  * `OptionalSparseRescorer`

**Risk**

* post-filter rejection → oversample → latency spikes

### 5.4 Pattern C — Parallel Hybrid (Baseline)

**Pipeline**

1. Dense ANN: top `K_d`
2. BM25: top `K_s`
3. Fuse via RRF → keep top `M`
4. Rerank top `N`
5. Context build

**Modules**

* `patterns/parallel_hybrid.py`

  * `DenseRetriever` (async)
  * `SparseRetriever` (async)
  * `fusion/rrf.py`
  * `rerank/cross_encoder.py`

**Notes**

* Designed for parallel execution to fit SLA.

### 5.5 Pattern D — Fielded / Multi-Vector Retrieval

**Pipeline**

1. Query router predicts weights over fields
2. Retrieve per-field (title/heading/body/code)
3. Fuse field-wise + modality-wise
4. Rerank
5. Context build

**Modules**

* `patterns/multivector_fielded.py`

  * `QueryRouter`
  * `FieldedBM25` and/or multi-vector dense

**Tradeoff**

* higher precision, higher complexity

---

## 6) Fusion + Reranking + Context Builder

### 6.1 Fusion

* `fusion/rrf.py` (baseline)
* `fusion/weighted_sum.py` (alternative)

### 6.2 Conditional Reranking

* `rerank/heuristics.py`

  * agreement heuristics
  * if dense + sparse agree → rerank fewer
  * if disagree → rerank more

### 6.3 Context Builder

**Rules**

* token budget cap
* diversity constraint (avoid same source dominance)
* adjacent stitching
* redundancy removal (hash + embedding sim)

Modules

* `context/builder.py`
* `context/dedupe.py`
* `context/stitching.py`

---

## 7) Experiment Harness (Patterns in Isolation + Permutations)

### 7.1 Goals

* Run each pattern A/B/C/D standalone.
* Run permutations:

  * chunk sizes × overlaps × boundary strategies
  * retrieval K_d/K_s/M/N
  * fusion strategy
  * filtering strategy
* Under varying constraints:

  * tenant partition sizes
  * metadata selectivity
  * concurrency (externally via JMeter)

### 7.2 Runner

* `experiments/permutations.py`

  * defines permutations grid
  * runs pipeline
  * collects `Trace` outputs
  * outputs SLA compliance + IR metrics

### 7.3 Metrics

* IR: Recall@K, nDCG@10
* System: stage p50/p95/p99, throughput under concurrency (external)

---

## 8) Phase Ordering (What we build first)

### Phase 0 — SLA measurement module (now)

1. `core/tracing/tracer.py`
2. `core/tracing/stats.py`
3. `core/tracing/sla.py`
4. Minimal example pipeline with synthetic stages

### Phase 1 — Text ingestion + chunking + indexing

* loader → splitter variants → docstore
* BM25 baseline + Dense HNSW baseline

### Phase 2 — Retrieval patterns + fusion + reranking

* implement A/B/C/D in isolation
* add routing rules

### Phase 3 — Experiment harness + load testing integration

* permutations runner
* JMeter scripts and deployment harness

---

## 9) Next: Write the modules down (code-first)

The next step is to implement **Phase 0** (SLA measurement module) with a minimal runnable example that:

* executes a fake Pattern C pipeline (dense + sparse in parallel)
* emits traces
* prints stage p95s
* asserts against the given SLA budgets

Then we’ll implement ingestion + chunking and move outward.
