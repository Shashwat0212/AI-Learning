# AskMyDocs — Ingest Module (Text-only v1)

This document describes the **final ingestion architecture and implementation plan** aligned with the overall AskMyDocs project structure.

The goal of this document is to explain:

• the **ingestion folder structure**
• the **flow of data through the pipeline**
• the **engineering constraints (document limits, SLAs)**
• the **incremental ingestion module**
• the **fast token estimation trick used in production systems**

---

# 0) Global Project Structure (for context)

The ingestion module sits inside the larger system:

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

  index/
  retrieve/
  experiments/
  service/
```

Important design rule:

```
core/ = shared primitives used by all modules
```

Therefore **Document, Chunk, Candidate types remain in `core/types.py`**.

The ingestion module only **uses them**, it does not redefine them.

---

# 1) Final Ingestion Folder Structure

Updated ingestion structure based on the overall system layout.

```
askmydocs/

  ingest/

    pipeline.py                 # ingestion orchestrator

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
      summaries.py

    incremental/
      diff_engine.py
      chunk_cache.py
      delta_indexer.py

    utils/
      token_estimator.py
      chunk_builder.py

    __init__.py
```

Explanation of new components:

| Component          | Purpose                              |
| ------------------ | ------------------------------------ |
| pipeline.py        | orchestrates ingestion stages        |
| token_estimator.py | fast token estimation (no tokenizer) |
| chunk_builder.py   | safe chunk construction abstraction  |
| incremental/       | optional delta indexing system       |

---

# 2) Ingestion Strategy Modes

The ingestion system supports **two interchangeable modes**.

## Mode 1 — Baseline ingestion

Pipeline:

```
load
split
enrich
embed
index
```

This processes every document fully.

---

## Mode 2 — Incremental ingestion

Pipeline:

```
load
split
fingerprint
compare fingerprints
embed changed chunks only
update index
```

Example improvement:

| Scenario     | Embeddings  |
| ------------ | ----------- |
| Full reindex | 1000 chunks |
| Incremental  | 5 chunks    |

Speed improvement:

```
20x – 200x
```

The ingestion pipeline will allow switching between these modes.

---

# 3) End‑to‑End Ingestion Flow

```
file(s)
   ↓
Loader
   ↓
Document
   ↓
Splitter
   ↓
Chunk
   ↓
Enrichment
   ↓
Embedding
   ↓
Index
```

Key idea:

```
Ingestion prepares chunks
Indexing stores them
Retrieval later consumes them
```

---

# 4) System Guardrails

To prevent unstable ingestion behaviour.

## Maximum document size

```
MAX_DOCUMENT_SIZE_MB = 10
```

Approx scale:

| metric     | value |
| ---------- | ----- |
| characters | ~2M   |
| tokens     | ~350k |
| chunks     | ~700  |

---

## Maximum characters

```
MAX_DOCUMENT_CHARS = 2_000_000
```

---

## Maximum chunks per document

```
MAX_CHUNKS_PER_DOCUMENT = 2000
```

Prevents chunk explosion.

---

# 5) Chunking Configuration

Baseline values:

```
TARGET_CHUNK_TOKENS = 500
CHUNK_OVERLAP = 0.15
```

Meaning:

| property   | value          |
| ---------- | -------------- |
| chunk size | 400–600 tokens |
| overlap    | 15–20%         |

---

# 6) Token Estimation Optimization

Running a tokenizer during chunking is expensive.

Example cost:

| Method           | Time     |
| ---------------- | -------- |
| Tokenizer encode | ~6–8 ms  |
| Regex estimate   | ~0.05 ms |

If a document produces **700 chunks**, tokenization alone could cost several seconds.

Production RAG systems therefore use **fast token estimation**.

Approximation:

```
tokens ≈ characters / 4
```

Implementation location:

```
ingest/utils/token_estimator.py
```

Example:

```
def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
```

Tokenizer is only used later when constructing the **final LLM prompt**.

---

# 7) Chunk Builder Abstraction

Chunk span calculation is error‑prone.

To avoid bugs we introduce a **ChunkBuilder helper**.

Location:

```
ingest/utils/chunk_builder.py
```

Responsibilities:

```
track span offsets
calculate token counts
apply overlap
construct Chunk objects safely
```

Splitters should use ChunkBuilder instead of constructing chunks manually.

---

# 8) Data Types Used by Ingestion

Defined in:

```
core/types.py
```

Types used:

```
Document
Chunk
Candidate
```

Pipeline usage:

```
Loader → Document → Splitter → Chunk
```

---

# 9) Implementation Roadmap

The ingestion module will be implemented step‑by‑step.

---

# Step A — Document Loader

File:

```
ingest/loaders/text_loader.py
```

Responsibilities:

```
read files
encoding detection
unicode normalization
create Document
```

Output:

```
Iterable[Document]
```

---

# Step B — Token Estimator

File:

```
ingest/utils/token_estimator.py
```

Purpose:

```
fast token count approximation
used by splitters
```

---

# Step C — Chunk Builder

File:

```
ingest/utils/chunk_builder.py
```

Responsibilities:

```
build Chunk objects
manage offsets
handle overlap
```

---

# Step D — Splitter Interface

File:

```
ingest/splitters/base.py
```

Interface:

```
split(doc: Document) -> list[Chunk]
```

---

# Step E — Fixed Token Splitter

File:

```
ingest/splitters/fixed_token.py
```

Strategy:

```
sliding token window
fixed chunk size
overlap
```

---

# Step F — Sentence Aware Splitter

File:

```
ingest/splitters/sentence_aware.py
```

Strategy:

```
sentence segmentation
pack sentences until token target
```

---

# Step G — Structure Aware Splitter

File:

```
ingest/splitters/structure_aware.py
```

Strategy:

```
detect headings
split sections
fallback to sentence-aware
```

---

# Step H — Metadata Enrichment

File:

```
ingest/enrich/metadata.py
```

Adds metadata such as:

```
title
section headings
source uri
```

---

# Step I — Fingerprint Hashing

File:

```
ingest/enrich/hash_fingerprint.py
```

Rule:

```
sha256(chunk_text)
```

Used for:

```
dedupe
embedding cache keys
incremental ingestion
```

---

# Step J — Ingestion Pipeline

File:

```
ingest/pipeline.py
```

Responsibilities:

```
coordinate ingestion stages
switch between baseline and incremental modes
call tracing spans
```

---

# Step K — Incremental Ingestion Module

Location:

```
ingest/incremental/
```

Components:

```
diff_engine.py
chunk_cache.py
delta_indexer.py
```

Purpose:

```
detect changed chunks
skip unchanged embeddings
update index incrementally
```

---

# 10) Definition of Done (Ingest v1)

The module is complete when:

✔ documents load successfully

✔ chunking works with at least one splitter

✔ metadata enrichment works

✔ fingerprints generated

✔ chunks ready for embedding

✔ ingestion guardrails enforced

✔ baseline ingestion pipeline functional

Incremental ingestion will be validated through **experiments module** later.

---

# 11) Next Implementation Step

Next code step:

```
Step B — implement token_estimator.py
```

Then implement **ChunkBuilder**, followed by the **splitter interface**.
