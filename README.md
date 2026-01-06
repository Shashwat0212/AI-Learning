# Week 3 — How LLMs Are Trained (Conceptual)

## Purpose of This Branch

This branch focuses on building a **conceptual understanding of how large language models are trained**, bridging theory with hands-on inspection of a real model.

The goal is **not** to train a model from scratch, but to understand:
- How pretrained language models work internally
- What happens during a forward pass
- How loss is computed in autoregressive language modeling
- How this connects to pretraining, fine-tuning, and instruction tuning

## Scope

### Learning
- Pretraining vs. fine-tuning
- Instruction tuning
- RLHF (high-level understanding)
- Implicit labels in next-token prediction

### Reading
- *Generative Deep Learning* — Chapters 1–2  
- *AI Engineering* — Chapter 1

### Build
**Project: HuggingFace GPT Walkthrough**
- Load GPT-2
- Tokenize sample text
- Run a forward pass
- Inspect logits and loss

## Definition of Done

This branch is complete when:
- The end-to-end GPT training pipeline makes **conceptual sense**
- Model inputs, outputs, and loss computation are clearly understood
- There is no “magic” left in how a language model learns from text

This branch establishes the mental model needed for later work on
instruction tuning, alignment, and retrieval-augmented generation.