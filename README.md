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

# Learnings

## Scope

* Pretraining vs Fine-tuning
* Instruction Tuning
* RLHF (High-level)
* Implicit Labels

---

## 1. What is RLHF?

**RLHF (Reinforcement Learning from Human Feedback)** is a post-training alignment technique used after supervised fine-tuning to shape *behavior*, not core knowledge.

Instead of learning from explicit labels like `(input → correct output)`, RLHF learns from **human preferences** over model outputs.

At a high level:

* The model generates multiple responses to the same prompt
* Humans rank or compare these responses ("A is better than B")
* A **reward model** is trained to predict these preferences
* The base model is then optimized (via RL) to maximize this learned reward

Key points:

* RLHF does **not** teach new facts
* It optimizes for qualities like helpfulness, harmlessness, tone, and refusal behavior
* It answers: *“Among many valid continuations, which ones do humans prefer?”*

Conceptually, RLHF turns a language model into a **policy optimized under a learned human reward function**, not a ground-truth objective.

---

## 2. Fine-tuning as Supervised Learning over a Base Model

Yes — this intuition is correct.

**Fine-tuning is supervised learning on top of a pretrained base model**, where:

* The base model already encodes language + world structure
* Fine-tuning shifts the model toward a *desired conditional behavior*

You can think of it as:

* Pretraining → learns representations and generative capability
* Fine-tuning → *reshapes the output distribution* for a specific task or format

Important nuance:

* Fine-tuning usually does **not** add much new knowledge
* It reallocates probability mass toward task-relevant outputs

This is analogous to:

* Freezing most of a CNN backbone
* Training a task-specific head

Except in LLMs, the "head" is distributed across all layers via gradient updates.

---

## 3. Implicit Labels — Are They Like Supervised Labels?

They play a **similar role**, but they are fundamentally different.

In pretraining:

* There are *no explicit labels*
* Every next token acts as a **self-generated training signal**

So instead of:

```text
(input, label)
```

we have:

```text
(tokens[0:n-1] → tokens[n])
```

Why they are called *implicit* labels:

* The dataset is unlabeled by humans
* But the structure of language itself provides supervision

Language encodes:

* Syntax rules
* Semantic relationships
* Factual co-occurrence
* Reasoning patterns

So yes — **next-token prediction functions like supervision**, but:

* The labels are *emergent from data*, not annotated
* The task is universal and task-agnostic

This is why LLMs learn reasoning, summarization, and explanation *before* being explicitly trained to do so.

---

## 4. Open Question

(To be filled — add the next concept or clarification here.)
