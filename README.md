# Week 5 — RAG Foundations & End-to-End System

**Phase:** RAG Engineering
**Hours:** ~18–20 (merged from original Weeks 5–7)

This week consolidates **Embeddings & Vector Search**, **RAG v1**, and **Failure Handling** into a single, production-oriented milestone. By the end of the week, you will have a working **AskMyDocs RAG v1.5** system with safe failure behavior and source attribution.

---

## 🎯 Objectives

By the end of this week, you will have:

* A semantic search engine using dense embeddings
* A complete Retrieval-Augmented Generation (RAG) pipeline
* Explicit handling for missing context and hallucinations
* Source-aware answers with citations
* A FastAPI `/query` endpoint suitable for local use

This is the **first shippable version** of AskMyDocs.

---

## 🧠 Learn (4–5 hrs)

### 1. Embeddings & Vector Search

Focus on embeddings as **semantic feature extractors**, analogous to frozen CNN backbones in vision.

Key concepts:

* Semantic geometry of embedding spaces
* Cosine similarity vs dot product
* Approximate vs exact nearest neighbor search
* Embedding drift and corpus sensitivity

**Mental model**: retrieval quality dominates generation quality.

---

### 2. Chunking Strategies

Chunking is a bias–variance tradeoff.

Study:

* Fixed-size chunking
* Recursive / structure-aware chunking
* Overlap tuning
* Metadata propagation (file, page, section)

Rule of thumb:

> If a chunk answers more than one question, it is too large.
> If it answers none, it is too small.

---

### 3. RAG Failure Modes

Understand why RAG systems fail *silently* if not designed carefully.

Failure modes:

* Hallucination under low-recall retrieval
* Confident answers with missing context
* Context window overflow
* Irrelevant top-k retrieval

Design principle:

> Silence is better than fiction.

---

## 🛠️ Build (14–15 hrs)

### Project: **AskMyDocs — RAG v1**

You will incrementally assemble a full RAG pipeline.

---

## 🧩 System Architecture

```
User Query
   ↓
Embed Query
   ↓
Vector Store Search (top-k)
   ↓
Context Assembly
   ↓
LLM Generation
   ↓
Answer + Sources OR "I don't know"
```

---

## 🔨 Implementation Tasks

### 1. Document Loader

* Load PDFs / markdown / text files
* Preserve metadata:

  * filename
  * page number
  * section (if available)

**Deliverable**
`load_documents() -> (text, metadata)[]`

---

### 2. Chunker

* Chunk size: ~300–500 tokens
* Overlap: 10–20%
* Attach metadata to each chunk

**Deliverable**
`chunk_documents(docs) -> chunks[]`

---

### 3. Embedding + Vector Store

* Generate embeddings for all chunks
* Store vectors + metadata
* Implement cosine similarity search

**Deliverables**

* `index_chunks(chunks)`
* `search(query, top_k=5)`

---

### 4. Retrieval Layer

* Embed user query
* Retrieve top-k chunks
* Apply a **minimum similarity threshold**

Hard rule:

```
If no chunk passes threshold → no answer
```

**Deliverable**
`retrieve_context(query) -> chunks[]`

---

### 5. Context Injection

* Concatenate retrieved chunks
* Enforce maximum token budget
* Preserve source boundaries

**Deliverable**
`build_context(chunks) -> prompt_context`

---

### 6. LLM Answer Generation

* Instruction constraints:

  * Answer **only** from provided context
  * Say "I don’t know" if information is insufficient
* Temperature ≤ 0.3

**Deliverable**
`generate_answer(query, context)`

---

### 7. Failure Handling (Merged from Week 7)

Implement explicit safeguards.

#### a. “I Don’t Know” Responses

Trigger when:

* No retrieved chunk exceeds similarity threshold
* Context length is below a minimum viable token count

#### b. Source Citations

* Every answer must list its source documents
* No sources → no answer

#### c. Context Window Limits

* Hard cap context size
* Drop lowest-similarity chunks first

---

### 8. API Layer

Expose the system via FastAPI.

**Endpoint**

```
POST /query
```

**Response schema**

```json
{
  "answer": "...",
  "sources": [
    {"file": "...", "page": 12}
  ]
}
```

---

## ✅ Deliverables Checklist

* [ ] Document loader with metadata
* [ ] Chunking strategy implemented
* [ ] Embedding + vector search
* [ ] Retrieval with similarity threshold
* [ ] Context-aware generation
* [ ] “I don’t know” handling
* [ ] Source citations
* [ ] FastAPI `/query` endpoint
* [ ] README with usage instructions

---

## 🧪 Validation Tests

Manually test:

1. Question clearly answered by docs → correct answer + sources
2. Question not in docs → “I don’t know”
3. Ambiguous question → partial answer + sources
4. Irrelevant question → no hallucination

---

## 📚 Study References (From Your Provided PDFs)

Use these **selectively**, not cover-to-cover.

### Core RAG & Embeddings

* **Hands-On Large Language Models** (Alammar & Grootendorst)

  * Chapters on *Embeddings*, *Semantic Search*, and *Retrieval-Augmented Generation*
  * Use for intuition on dense retrieval and cosine similarity

* **Natural Language Processing with Transformers** (Tunstall, von Werra, Wolf)

  * Chapters on *Semantic Search* and *Question Answering*
  * Practical grounding in embedding-based retrieval pipelines

---

### RAG System Design & Failure Modes

* **LLM Engineer’s Handbook** (Iusztin & Labonne)

  * Sections on *RAG Pipelines* and *Production Guardrails*
  * Focus on failure handling, retrieval thresholds, and safe defaults

* **Hands-On Generative AI with Transformers and Diffusion Models**

  * Sections discussing *LLM applications* and *retrieval-based augmentation*
  * Useful for understanding where generation ends and retrieval must take over

---

### Conceptual Foundations (Optional Refresh)

* **Machine Learning: A Probabilistic Perspective** (Kevin Murphy)

  * Review similarity metrics and high-dimensional geometry (intuition only)

* **Generative Deep Learning** (David Foster)

  * Chapters on Transformers and representation learning
  * Helps frame embeddings as learned manifolds
