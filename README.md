# Week 5 — Embeddings & Vector Search

**Total Time:** ~10 hours
**Goal:** Build a solid mental model of embeddings and vector similarity, then implement a local-first semantic search engine that will later become the retrieval core of your RAG system (AskMyDocs).

---

## Learning Objectives (3 hours)

By the end of this week, you should be able to:

- Explain _why_ embeddings work using geometric intuition
- Reason about similarity metrics and their failure modes
- Design chunking strategies aligned with retrieval and generation
- Conffortably implement cosine similarity–based retrieval from scratch

---

## 1. Embeddings — Intuition (≈ 1 hour)

### Core Concepts

- Embeddings as **semantic projections**: mapping discrete symbols (text) into a continuous vector space
- Distributional hypothesis revisited: _"You shall know a word by the company it keeps"_ → dense vectors
- Relationship to classical ML:
  - Bag-of-words → sparse, high-dimensional
  - Embeddings → dense, low-dimensional, manifold-structured

- Embeddings as **learned feature extractors**, similar to CNN feature maps but for language

### What to Internalize

- Distance ≈ meaning difference
- Direction ≈ semantic axis (topic, sentiment, intent)
- Magnitude usually irrelevant (→ cosine similarity)

### Recommended Reading

- _Hands-On Large Language Models_ — Embeddings & Semantic Search chapters
- _NLP with Transformers_ — Sentence Transformers section
- _Hands-On Generative AI with Transformers_ — Representation learning chapters

### Optional (Deep Dive)

- Word2Vec (CBOW vs Skip-gram) to contrast static vs contextual embeddings
- Why contextual embeddings dominate in RAG

---

## 2. Cosine Similarity & Vector Geometry (≈ 45 minutes)

### Why Cosine Similarity?

- Measures **angular similarity**, not magnitude
- Robust to document length
- Works well in high-dimensional spaces

### Mathematical View

[ \cos(\theta) = \frac{A \cdot B}{||A||,||B||} ]

Interpretation:

- 1.0 → identical direction (high semantic similarity)
- 0.0 → orthogonal (unrelated)
- -1.0 → opposite meaning (rare in practice)

### Practical Notes

- Cosine vs Euclidean distance
- Normalized embeddings turn dot product into cosine similarity
- Curse of dimensionality still applies → motivates ANN later

### Exercises

- Manually compute cosine similarity for 3–5 toy vectors
- Observe effect of vector normalization

---

## 3. Chunking Strategies for Retrieval (≈ 1 hour 15 minutes)

### Why Chunking Matters

- LLM context windows ≠ retrieval granularity
- Retrieval quality is often limited by chunking, not embeddings

### Chunking Axes

**1. Size**

- Small chunks → higher recall, lower precision
- Large chunks → higher precision, lower recall

Typical ranges:

- 200–400 tokens (QA-focused)
- 500–800 tokens (explanatory docs)

**2. Overlap**

- Prevents semantic boundary loss
- Common overlap: 10–20%

**3. Structure-Aware Chunking**

- Headings
- Paragraphs
- Code blocks

### Chunking Heuristics (Rules of Thumb)

- Chunk ≈ smallest unit that answers a question
- Never split code blocks
- Prefer semantic boundaries over fixed length when possible

### Reading

- _LLM Engineer’s Handbook_ — RAG data preparation sections
- _Hands-On LLMs_ — Retrieval pipelines

---

## Build Phase — Project: Embedding Search Engine (7 hours)

### Project Goal

Build a **local semantic search engine** that:

- Loads documents
- Chunks them intelligently
- Embeds chunks
- Retrieves top-k chunks via cosine similarity

This will become the retrieval layer of AskMyDocs.

---

## Deliverables (Detailed)

### 1. Document Loader

**Requirements:**

- Support at least one format (PDF or Markdown)
- Preserve metadata:
  - source file
  - page number or section

**Implementation Notes:**

- Use `PyPDF2`, `pdfplumber`, or `unstructured`
- Output format:

```python
Document(
    text: str,
    metadata: dict
)
```

**Acceptance Criteria:**

- Can load a full document into memory as structured objects

---

### 2. Chunker

**Requirements:**

- Configurable chunk size
- Configurable overlap
- Deterministic output

**Stretch Goals:**

- Markdown-aware chunking
- Section-based chunking

**Output:**

```python
Chunk(
    text: str,
    metadata: {
        source,
        chunk_id,
        start_idx,
        end_idx
    }
)
```

**Acceptance Criteria:**

- No chunk exceeds max token length
- Overlap is correctly applied

---

### 3. Embedding + Cosine Search

**Requirements:**

- Local embedding model (e.g. sentence-transformers)
- Store embeddings in memory (NumPy)
- Implement cosine similarity manually (no vector DB yet)

**Pipeline:**

1. Embed all chunks → matrix `(N, D)`
2. Embed query → vector `(D,)`
3. Compute cosine similarity
4. Return top-k chunks

**Acceptance Criteria:**

- Query returns semantically relevant chunks
- Results are stable across runs

---

## Repo & Branch Structure (How This Week Fits Your Workflow)

You mentioned that **each week lives on its own branch**, with:

- **Theory** → `.md`
- **Deliverables** → `.ipynb`

Below is a structure optimized for that workflow.

### Branch Naming

```
week-05-embeddings-vector-search
```

---

## Files in This Branch

### 1️⃣ Theory (Markdown)

```
week-05-embeddings-vector-search.md
```

Contents:

- Embeddings intuition
- Cosine similarity geometry
- Chunking strategies
- Design tradeoffs (recall vs precision)

This file is **what you already see in this canvas**.

---

### 2️⃣ Deliverables (Notebooks)

```
notebooks/
├── 01_document_loader.ipynb
├── 02_chunking_strategies.ipynb
├── 03_embedding_and_cosine_search.ipynb
```

Each notebook is **atomic**, testable, and reusable later in RAG.

---

## Notebook-Level Deliverables (Detailed)

### 📓 01_document_loader.ipynb

**Goal:** Load raw documents into a structured internal format.

**Must Contain:**

- PDF (or Markdown) loading
- Text extraction
- Metadata preservation

**Output Object:**

```python
{
  "text": str,
  "metadata": {
      "source": str,
      "page": int | None
  }
}
```

**Validation Cell:**

- Print first 500 characters
- Print metadata

---

### 📓 02_chunking_strategies.ipynb

**Goal:** Convert documents into retrieval-ready chunks.

**Must Contain:**

- Fixed-size chunking
- Overlap handling
- Token-length awareness

**Experiments (Required):**

- Compare 2 chunk sizes
- Compare overlap vs no overlap

**Output Object:**

```python
{
  "chunk_id": int,
  "text": str,
  "metadata": {
      "source": str,
      "start": int,
      "end": int
  }
}
```

---

### 📓 03_embedding_and_cosine_search.ipynb

**Goal:** Build a semantic search engine _without_ a vector DB.

**Must Contain:**

- Local embedding model
- Manual cosine similarity
- Top-k retrieval

**Pipeline:**

1. Embed all chunks → `(N, D)`
2. Embed query → `(D,)`
3. Compute cosine similarity
4. Rank + retrieve

**Validation Queries:**

- At least 3 natural-language queries
- Inspect retrieved chunks manually

---

## Promotion Rule (When to Merge This Branch)

You should merge `week-05-embeddings-vector-search` **only when**:

- You can retrieve correct chunks without an LLM
- Chunking choices are justified in markdown
- Cosine similarity is implemented from scratch

---

## How This Feeds Week 6

Week 6 will:

- Replace cosine search with FAISS / Chroma
- Keep the _same_ chunker and embedder
- Add evaluation + ANN tradeoffs

This is why Week 5 must stay **framework-free and explicit**.

```
askmydocs/
├── loaders/
│   └── pdf_loader.py
├── chunking/
│   └── chunker.py
├── embeddings/
│   └── embedder.py
├── search/
│   └── cosine_search.py
├── data/
└── notebooks/
```

---

## Exit Criteria (You’re Ready to Move On When…)

- You can explain embeddings without math hand-waving
- You can justify your chunk size choices
- You can retrieve correct context without an LLM

---

## Preview of Week 6

- Vector databases (FAISS / Chroma)
- ANN vs exact search
- Retrieval evaluation (precision@k, recall@k)
- First RAG loop
