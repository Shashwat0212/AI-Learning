# AskMyDocs — Ingest Module (Text-only v1)

This document is the **design + implementation guide** for the Ingest module. It captures both the **coding steps** and the **system design constraints** we discussed (document size limits, ingestion SLAs, and future incremental ingestion support).

---

# 0) End-to-end pipeline mental model

The ingestion pipeline converts **raw files → searchable chunks**.

Pipeline flow:

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

Important distinction:

| Pipeline           | Type          | SLA philosophy         |
| ------------------ | ------------- | ---------------------- |
| Query pipeline     | Online        | strict latency budget  |
| Ingestion pipeline | Offline/async | throughput + freshness |

Your existing **tracing + SLA system** will still monitor ingestion stages but failures should generally **alert rather than fail-fast**.

---

# 1) Definition of a "Document"

For **AskMyDocs v1**:

```
One file = one document
```

Supported formats initially:

```
.txt
.md
.jsonl
```

Future formats:

```
PDF
HTML
DOCX
CSV
```

Examples of documents in real systems:

| Source       | Document unit  |
| ------------ | -------------- |
| PDF          | whole file     |
| Confluence   | page           |
| GitHub repo  | many documents |
| Slack thread | document       |

---

# 2) System guardrails (very important)

To keep ingestion predictable we define **hard limits**.

## Maximum document size

```
MAX_DOCUMENT_SIZE_MB = 10
```

Rough scale:

| Metric               | Approx     |
| -------------------- | ---------- |
| characters           | ~2 million |
| tokens               | ~350k      |
| chunks (~500 tokens) | ~700       |

This size is large enough for most documentation but still safe for memory.

---

## Maximum characters

```
MAX_DOCUMENT_CHARS = 2_000_000
```

Prevents extremely large files from entering the pipeline.

---

## Maximum chunks per document

```
MAX_CHUNKS_PER_DOCUMENT = 2000
```

This protects against **chunk explosion** from logs or machine generated text.

---

# 3) Chunking configuration

Recommended baseline:

```
TARGET_CHUNK_TOKENS = 500
CHUNK_OVERLAP = 0.15
```

Meaning:

| parameter  | value          |
| ---------- | -------------- |
| chunk size | 400–600 tokens |
| overlap    | 15–20%         |

This is widely used in production retrieval systems.

---

# 4) Ingestion SLA philosophy

Unlike query SLAs, ingestion SLAs focus on **index freshness**.

Key metric:

```
time(upload → searchable)
```

### Target SLA (AskMyDocs dev environment)

| Document Size | SLA      |
| ------------- | -------- |
| < 500 KB      | < 5 sec  |
| 500 KB – 5 MB | < 15 sec |
| 5 MB – 10 MB  | < 30 sec |

---

# 5) Stage-level monitoring (for tracing system)

Even though ingestion is async, we track stage timings.

Example stage budgets:

| Stage                     | Target p95 |
| ------------------------- | ---------- |
| ingest.load               | 50 ms      |
| ingest.split              | 50 ms      |
| ingest.enrich.metadata    | 10 ms      |
| ingest.enrich.fingerprint | 5 ms       |
| ingest.embed              | 200 ms     |
| ingest.index              | 50 ms      |

These values help detect bottlenecks.

---

# 6) Data Types (core primitives)

## Document

Represents normalized source text.

Fields:

```
doc_id: str
tenant_id: str
source_uri: str
text: str
metadata: dict
```

Role in pipeline:

```
Loader → Document → Splitter
```

---

## Chunk

Represents an **indexable unit of text**.

Fields:

```
chunk_id: str
doc_id: str
tenant_id: str
text: str
token_count: int
span: (start, end)
metadata: dict
fingerprint: str
```

Role:

```
Splitter → Chunk → Enrichment → Embedding → Index
```

---

## Candidate

Used during retrieval (not ingestion).

Fields:

```
chunk_id
score
source
metadata
```

---

# 7) Implementation roadmap (step-by-step)

We implement the ingestion pipeline in the following order.

---

# Step A — Data types

File:

```
askmydocs/ingest/types.py
```

Define:

```
Document
Chunk
Candidate
```

Reason:

All modules depend on these shapes.

---

# Step B — Document loader

File:

```
ingest/loaders/text_loader.py
```

Responsibilities:

```
read file
encoding detection
unicode normalization
attach metadata
create doc_id
```

Output:

```
Iterable[Document]
```

Checkpoint:

```
file → Document
```

---

# Step C — Splitter interface

File:

```
ingest/splitters/base.py
```

Interface:

```
split(doc: Document) -> list[Chunk]
```

Purpose:

Allows interchangeable chunking strategies.

---

# Step D — Fixed token splitter

File:

```
ingest/splitters/fixed_token.py
```

Strategy:

```
sliding window
fixed token size
overlap
```

Parameters:

```
chunk_tokens
chunk_overlap
```

Purpose:

Baseline splitter and debugging tool.

---

# Step E — Sentence aware splitter

File:

```
ingest/splitters/sentence_aware.py
```

Strategy:

```
sentence segmentation
pack sentences until token target
```

Benefit:

More semantic coherence.

---

# Step F — Structure aware splitter

File:

```
ingest/splitters/structure_aware.py
```

Strategy:

```
detect headings
split into sections
fallback to sentence-aware
```

Recommended default splitter.

---

# Step G — Enrichment

## Metadata enrichment

File:

```
ingest/enrich/metadata.py
```

Adds metadata such as:

```
title
section heading
source uri
```

---

## Fingerprint hashing

File:

```
ingest/enrich/hash_fingerprint.py
```

Fingerprint rule:

```
sha256(chunk_text)
```

Uses:

```
dedupe
embedding cache keys
incremental ingestion
```

---

# 8) Chunk explosion concept

Large documents produce many chunks.

Example:

| doc size | chunks |
| -------- | ------ |
| 20 KB    | ~40    |
| 5 MB     | ~1500  |

Embedding cost scales with chunk count.

Therefore the real throughput metric becomes:

```
chunks/sec
```

---

# 9) Incremental ingestion (future optimization)

Problem with naive ingestion:

```
document edited
→ re-chunk
→ re-embed all chunks
→ re-index everything
```

Even if only a small section changed.

---

## Incremental ingestion idea

Use fingerprints to detect unchanged chunks.

Pipeline:

```
old chunks
      ↓
new chunks
      ↓
compare fingerprints
      ↓
embed only changed chunks
```

Example:

| scenario    | chunks embedded |
| ----------- | --------------- |
| naive       | 1000            |
| incremental | 5               |

Improvement:

```
20x – 200x faster
```

---

# 10) Future experimental module

We will build incremental ingestion **as a separate experiment**.

Proposed structure:

```
ingest/incremental/
    diff_engine.py
    chunk_cache.py
    delta_indexer.py

experiments/
    incremental_eval.py
```

Experiment compares:

```
full_reindex()
vs
delta_reindex()
```

Metrics:

```
time
embedding calls
chunks processed
```

---

# 11) Definition of done (Ingest v1)

The module is considered complete when:

✔ documents load correctly

✔ chunking works with at least one splitter

✔ metadata enrichment works

✔ fingerprints generated

✔ chunks ready for embedding

✔ ingestion respects size guardrails

---

# 12) Next implementation step

Next code step:

```
Step C — implement splitters/base.py
```

Then we build the **fixed token splitter** to run the first full ingestion pipeline.
