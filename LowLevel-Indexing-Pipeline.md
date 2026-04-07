# Indexing Pipeline — HLD + LLD

This document focuses exclusively on the indexing pipeline (HLD + LLD), which transforms chunks into efficient retrieval-ready structures. The ingestion module is defined separately and provides chunk-level inputs to this pipeline.

---

## 1) Role of Indexing in the System

Indexing sits between ingestion and retrieval:

```
ingestion → indexing → retrieval
```

Responsibilities:

```
chunks → representations → searchable structures
```

Indexing enables:

• fast similarity search (dense)
• keyword-based retrieval (sparse)
• hybrid retrieval (combined later)

---

## 2) Core Indexing Components

Dense Index (Vector Index)

```
index/dense/vector_index.py
```

Responsibilities:

• generate embeddings
• store vectors
• support nearest neighbor search

Initial implementation:

• FAISS
• HNSW vs Flat index comparison

---

Sparse Index (BM25)

```
index/sparse/bm25.py
```

Responsibilities:

• keyword-based retrieval
• scoring based on term frequency

---

Chunk ID Strategy

```
chunk_id = fingerprint (sha256)
```

Rules:

• must be deterministic across runs
• must be shared across dense and sparse index
• used as primary key in doc_map

---

```
askmydocs/

  index/

    pipeline.py              # indexing orchestrator

    dense/
      embeddings.py          # embedding generation
      base.py                # abstract interface
      in_memory.py           # simple vector store (v1)
      hnsw.py                # future (faiss/hnsw)

    sparse/
      bm25.py                # BM25 implementation
      base.py                # abstract interface

    store/
      doc_map.py             # chunk_id → chunk mapping
      metadata_store.py      # optional metadata lookup

    incremental/
      index_diff.py          # compare indexed vs new chunks
      index_updater.py       # apply add/remove updates

    utils/
      similarity.py          # cosine similarity etc.

    __init__.py
```

• pipeline.py → coordinates indexing stages
• dense/ → vector representations and search
• sparse/ → keyword-based retrieval
• store/ → mapping layer between index and actual chunk
• incremental/ → update logic aligned with ingestion
• utils/ → shared math and helpers

Note:

All components listed here belong strictly to the indexing pipeline. Retrieval and inference components must not be implemented in this layer.

---

## 4) Indexing Pipeline Flow

```
chunks
  ↓
validate chunk_id (fingerprint)
  ↓
embedding generation (batch)
  ↓
dense index insertion
  ↓
sparse index insertion
  ↓
doc_map update (id → chunk)
```

Incremental behavior:

```
if incremental mode:
  compute diff
  add new chunks
  remove stale chunks
```

• embedding must be batched for efficiency
• chunk_id must remain deterministic

---

## 4.1 Indexing Pipeline (LLD Behavior)

```
for chunk in chunks:
    id = chunk.fingerprint

    vector = embedder.encode(chunk.text)

    dense_index.add(id, vector)
    sparse_index.add(id, chunk.text)

    doc_map.store(id, chunk)
```

• doc_map is required to reconstruct chunks after retrieval

• doc_map is the source of truth for reconstructing chunks

---

## 4.2 Responsibility Separation (Critical)

This separation is strict and must be enforced in implementation:

Indexing Pipeline Responsibilities:

• embedding generation
• dense index construction
• sparse index construction
• chunk_id mapping (doc_map)
• incremental index updates

Retrieval Pipeline Responsibilities:

• query embedding
• nearest neighbor search
• BM25 search
• hybrid fusion (RRF)
• metadata filtering

Inference Pipeline Responsibilities:

• reranking (cross-encoder)
• context building (deduplication, compression)
• prompt construction
• LLM response generation

Design Principle:

• indexing prepares data
• retrieval selects candidates
• inference generates answers

---

## 5) Benchmarking and Observability Strategy

Indexing performance will be evaluated using the tracing system already integrated into the project.

Approach:

• instrument indexing pipeline stages using tracing spans
• run controlled experiments across multiple dataset sizes
• generate structured JSON reports for each run

Analysis:

• compare latency across input sizes
• identify bottlenecks (embedding vs index insertion)
• compute throughput (chunks/sec)

# TODO

• build automated benchmarking harness
• generate comparative reports across configurations
• use results to guide optimization decisions

---

## 6) Evaluation Hooks (Forward Integration)

Indexing must integrate with evaluation layer:

• Recall@k
• MRR

Implication:

• index must support deterministic retrieval
• results must be reproducible

---

## 7) Future Extensions

• reranking (cross-encoder)
• caching (query-level, embedding-level)
• observability (p50/p95 tracking)

Indexing must be designed to:

• plug into reranking stage
• support caching keys (fingerprint-based)
• expose latency metrics

---

## 8) Engineering Constraints
Indexing must:

• support incremental updates (from ingestion)
• avoid full rebuilds
• maintain consistent IDs across runs
• indexing must align with ingestion incremental mode (reuse fingerprints)
• avoid duplicate vector insertions
• skip insertion if fingerprint already exists (deduplication)

---

## 9) Deliverables

• vector_index.py
• bm25_index.py
• embedding generation
• benchmark script

• hybrid retrieval compatibility

---

## 10) Key Design Principles

```
1. Decouple ingestion and indexing
2. Use fingerprint as primary key
3. Support both dense and sparse retrieval
4. Design for hybrid retrieval from day one
5. Instrument indexing with latency tracking
```

---

## 11) Open Questions (To Be Filled Later)

• exact embedding model choice
• in-memory vs persistent index
• batching strategy for embeddings
• index update vs rebuild strategy

---

End of indexing HLD extraction.

---


---

## 12) Implementation Roadmap

The indexing module will be implemented step-by-step.

---

# Step A — Embedder

File:

```
index/dense/embeddings.py
```

Responsibilities:

```
text → vector
batch encoding
consistent vector dimension
```

---

# Step B — Dense Index Interface

File:

```
index/dense/base.py
```

Define:

```
add(id, vector)
remove(id)
search(query_vector, k)
```

---

# Step C — In-Memory Dense Index

File:

```
index/dense/in_memory.py
```

Implement:

```
vector storage
cosine similarity search
top-k retrieval
```

---

# Step D — Sparse Index Interface

File:

```
index/sparse/base.py
```

Define:

```
add(id, text)
remove(id)
search(query, k)
```

---

# Step E — BM25 (v1 simplified)

File:

```
index/sparse/bm25.py
```

Implement:

```
inverted index
basic term frequency scoring
```

---

# Step F — Doc Map

File:

```
index/store/doc_map.py
```

Responsibilities:

```
store(id, chunk)
get(id)
delete(id)
```

---

# Step G — Similarity Utilities

File:

```
index/utils/similarity.py
```

Implement:

```
cosine similarity
vector normalization
```

---

# Step H — Indexing Pipeline

File:

```
index/pipeline.py
```

Responsibilities:

```
coordinate indexing stages
handle batching
integrate tracing
support incremental mode
```

---

# Step I — Incremental Indexing

Files:

```
index/incremental/index_diff.py
index/incremental/index_updater.py
```

Responsibilities:

```
identify added / removed chunks
update dense index
update sparse index
update doc_map
```

---

## 13) Definition of Done (Indexing v1)

The module is complete when:

✔ embeddings generated correctly

✔ dense index stores and retrieves vectors

✔ sparse index retrieves based on keywords

✔ doc_map reconstructs chunks accurately

✔ indexing pipeline runs end-to-end

✔ incremental indexing updates correctly

✔ duplicate chunks are not re-indexed

✔ tracing captures indexing latency across stages

✔ batching is implemented for embedding generation

---

## 14) Next Implementation Step

Next code step:

```
Step A — implement embeddings.py
```

Then implement the dense index interface, followed by the in-memory index.

---

Embedding Generation

Input:

```
Chunk.text
```

Output:

```
vector representation
```

Used by:

• dense index

Embedding MUST be batched to avoid per-chunk overhead.
