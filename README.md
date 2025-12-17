# 24-Week Agentic AI Engineer Execution Plan

This document is a **project-first, execution-focused roadmap** to prepare for **GenAI / Agentic AI Engineer / AI Platform Engineer** roles by **end of May**.

**Assumptions**

* Time commitment: ~10–12 hrs/week (avg)
* Primary language: Python (with Java/Spring integration later)
* Goal: Production-grade agentic systems (not ML research)

---

## Execution Principles (Read First)

* Every week must produce **code, logs, metrics, or written analysis**
* Prefer **1 evolving system** over many disconnected demos
* Evaluation, cost, and failure analysis are first-class citizens
* Books are **reference tools**, not cover-to-cover goals

---

# PHASE 1 — LLM CORE & TRANSFORMERS

**Weeks 1–4 | 8–10 hrs/week**

## Week 1 — Attention & Transformer Internals

**Hours**: 8–9

### Learn (3 hrs)

* Self-attention intuition (Q, K, V)
* Dot-product attention
* Masked self-attention

**Reading**

* Hands-On Large Language Models — Ch 1–2
* NLP with Transformers — Ch 1

### Build (5–6 hrs)

**Project: Attention From Scratch (NumPy)**

Deliverables:

* `attention.py`
* Q/K/V computation
* Softmax + weighted sum
* Printed intermediate matrices

**Done when**: You can explain attention without equations

---

## Week 2 — Transformer Architecture (GPT)

**Hours**: 9–10

### Learn (3–4 hrs)

* Encoder vs Decoder vs Decoder-only
* Positional embeddings
* Residuals + LayerNorm

**Reading**

* Hands-On LLMs — Ch 3–4
* LLM Engineers Handbook — Architecture section

### Build (6 hrs)

**Project: Mini GPT Forward Pass**

Deliverables:

* `mini_gpt.py`
* Token + positional embeddings
* Single transformer block
* Output logits

**Done when**: You can trace token → logits end-to-end

---

## Week 3 — How LLMs Are Trained (Conceptual)

**Hours**: 8–9

### Learn (3 hrs)

* Pretraining vs fine-tuning
* Instruction tuning
* RLHF (high level)
* Implicit labels

**Reading**

* Generative Deep Learning — Ch 1–2
* AI Engineering — Ch 1

### Build (5–6 hrs)

**Project: HuggingFace GPT Walkthrough**

Deliverables:

* Load GPT-2
* Tokenize text
* Forward pass
* Inspect loss

**Done when**: Training pipeline makes conceptual sense

---

## Week 4 — Prompting & LLM Control

**Hours**: 8–10

### Learn (2–3 hrs)

* Prompt structure
* Temperature / top-p
* System vs user prompts

**Reading**

* LLM Engineers Handbook — Prompting section

### Build (6–7 hrs)

**Project: CLI LLM Playground**

Deliverables:

* CLI chat app
* Temperature toggle
* Token usage logging

**Done when**: You can predict output behavior changes

---

# PHASE 2 — RAG ENGINEERING

**Weeks 5–10 | 10–12 hrs/week**

## Week 5 — Embeddings & Vector Search

**Hours**: 10

### Learn (3 hrs)

* Embeddings intuition
* Cosine similarity
* Chunking strategies

**Reading**

* Hands-On LLMs — Embeddings
* AI Engineering — RAG intro

### Build (7 hrs)

**Project: Embedding Search Engine**

Deliverables:

* Document loader
* Chunker
* Embedding + cosine search

---

## Week 6 — RAG v1 (Project #1 Start)

**Hours**: 12

### Build

* Retrieval
* Context injection
* LLM answer generation

Deliverables:

* FastAPI `/query` endpoint

---

## Week 7 — RAG Failure Handling

**Hours**: 10

### Learn (2 hrs)

* Hallucination
* Missing context

**Reading**

* AI Engineering — RAG failure modes

### Build (8 hrs)

* “I don’t know” responses
* Source citations
* Context window limits

---

## Week 8 — RAG Evaluation

**Hours**: 11

### Build

* 30 test queries
* LLM-as-judge
* Hallucination metrics

Deliverables:

* `evals.py`

---

## Week 9 — RAG Cost & Performance

**Hours**: 10

### Build

* Latency logging
* Token cost tracking
* Budget caps

---

## Week 10 — RAG Productionization

**Hours**: 12

### Build

* Dockerization
* Structured logging
* Error handling

**Checkpoint**: Project #1 COMPLETE

---

# PHASE 3 — AGENTIC SYSTEMS

**Weeks 11–18 | 11–13 hrs/week**

## Week 11 — Agent Fundamentals

**Hours**: 10

### Build (Project #2 Start)

* ReAct loop
* Tool calling

---

## Week 12 — Tools & Function Calling

**Hours**: 11

### Build

* Search tool
* Calculator tool
* RAG tool

---

## Week 13 — Agent Orchestration

**Hours**: 12

### Build

* LangGraph state machine
* Conditional flows

---

## Week 14 — Agent Observability

**Hours**: 10

### Build

* Step-level traces
* Decision logs

---

## Week 15 — Agent Evaluation

**Hours**: 12

### Build

* Task completion metrics
* Tool correctness checks

---

## Week 16 — Human-in-the-Loop

**Hours**: 10

### Build

* Confidence threshold
* Escalation logic

---

## Week 17 — Multi-Agent Systems

**Hours**: 12

### Build

* Manager + worker agents

---

## Week 18 — Failure Analysis

**Hours**: 10

### Build

* Intentional failure injection
* `FAILURE_MODES.md`

**Checkpoint**: Project #2 COMPLETE

---

# PHASE 4 — CAPSTONE & INTERVIEW READINESS

**Weeks 19–24 | 12–14 hrs/week**

## Weeks 19–20 — Capstone Project (Project #3)

**Hours**: 25–28 total

**Domain Agent (Finance / Support)**

* RAG
* Agents
* Evaluation
* Cost tracking
* Human-in-the-loop

---

## Week 21 — Java / Spring Integration

**Hours**: 12

* Java API → Python agent
* OR Spring AI RAG microservice

---

## Week 22 — Deployment

**Hours**: 14

* AWS deployment
* CI pipeline

---

## Week 23 — System Design Prep

**Hours**: 10

* 5 agent system designs
* Written answers

---

## Week 24 — Polish & Apply

**Hours**: 8–10

* README polish
* Demo videos
* LinkedIn article

---

# END STATE

By end of May you will have:

* 3 production-grade projects
* Deep LLM & agent intuition
* Evaluation & reliability mindset
* Interview-ready system narratives

This profile aligns directly with **GenAI Engineer / Agentic AI Engineer / AI Platform Engineer** roles.
