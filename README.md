# AI-Learning

A structured, progressive learning path focused on building the foundational skills needed to design and implement **local-first RAG systems**, **LLM applications**, and **MLOps pipelines**.  
This repository tracks learning milestones, notes, and implementation sketches across four phases:

1. **ML Foundations** (this document includes the detailed tracking list)
2. **LLM Foundations**
3. **Retrieval-Augmented Generation (RAG) Systems**
4. **MLOps for LLM/RAG Pipelines**

---

# 📘 Phase 1 — ML Foundations (RAG + LLM Essentials)

This phase covers *only* the subset of ML concepts required to understand:

- How **embeddings** work  
- How **semantic vector search** works  
- Why **chunking, model choice, and evaluation** matter in RAG  
- How **neural networks encode meaning**

The topics and reading locations below come directly from the PDFs used as part of this learning track.

---

## ✅ 1. What Machine Learning Is (Supervised vs. Unsupervised)

### Required Reading
**Machine Learning for Absolute Beginners**
- WHAT IS MACHINE LEARNING?
- MACHINE LEARNING CATEGORIES

**Machine Learning: A Probabilistic Perspective (Murphy)**
- Chapter 1 — Introduction  
  - 1.1 Machine learning: what and why?  
  - 1.2 Supervised learning  
  - 1.3 Unsupervised learning  

### Learning Outcome
- Understand how models learn patterns with or without labels.
- Build the intuition behind why embeddings are *unsupervised-style* representations.

---

## ✅ 2. Vectors, Embeddings & Cosine Similarity (Core Concepts for RAG)

### Required Reading
**Hands-On Large Language Models**
- Embeddings and vector representations  
- Semantic search  
- Dense retrieval  

**Generative Deep Learning**
- Intro sections on latent spaces  
- How deep networks form representations  

### Learning Outcome
- Understand vector spaces, distances, similarity scores.
- Know why cosine similarity is the dominant metric for retrieval.
- Understand why two pieces of text with similar meaning have nearby embeddings.

---

## ✅ 3. Train/Test Mindset (Minimal Viable ML Evaluation)

### Required Reading
**Machine Learning for Absolute Beginners**
- BIAS & VARIANCE  
- MODEL OPTIMIZATION  
- BUILDING A MODEL IN PYTHON (skim for intuition)

**Machine Learning: A Probabilistic Perspective (Murphy)**
- 1.4 Some basic concepts in machine learning  
  - Overfitting  
  - Model selection  
  - No free lunch theorem  

### Learning Outcome
- Recognize underfitting/overfitting.
- Understand why evaluation and experimentation matter in RAG systems.
- Know why retrieval pipelines require their own evaluation workflows.

---

## ✅ 4. Basic Neural Network Intuition (What You Need for Embeddings)

### Required Reading
**Machine Learning for Absolute Beginners**
- ARTIFICIAL NEURAL NETWORKS  

**Generative Deep Learning**
- Deep learning basics  
- Representation learning (how networks form latent features)

**Hands-On Generative AI with Transformers (Optional but helpful)**
- Transformer basics (early chapters)

### Learning Outcome
- Understand how neural networks build hierarchical representations.
- Know what “latent space” means and why embeddings live there.
- Build intuition for why modern embedding models outperform older approaches.

---

# 🎯 Phase 1 Completion Criteria

You can consider Phase 1 complete when you can:

- Explain supervised vs. unsupervised learning with examples.  
- Describe what embeddings are and how cosine similarity is computed.  
- Explain overfitting and why train/test separation matters.  
- Describe how neural networks encode data into vector spaces.  

Once Phase 1 is complete, you are ready to begin **Phase 2: LLM Foundations**, where you will study tokenization, transformer internals, attention mechanisms, and representation models in depth.

---