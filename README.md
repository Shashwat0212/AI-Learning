Week 1 — LLM Foundations and Attention Mechanics

Objective

The objective of Week 1 was to establish a correct mental and implementation-level understanding of how modern Large Language Models work internally, focusing on attention and transformer fundamentals, and to translate that understanding into executable code artifacts.

The emphasis was on:
	•	Conceptual correctness over optimization
	•	Understanding why architectures work, not just how to call APIs
	•	Building minimal, inspectable code rather than production abstractions

⸻

Topics Covered

1. Neural Network Refresher (Contextual)
	•	Reviewed fundamentals of Artificial Neural Networks (ANNs)
	•	Revisited Convolutional Neural Networks (CNNs) to contrast vision models vs language models
	•	Identified why CNN/RNN-based approaches fail to scale for language modeling

2. How Large Language Models Are Trained (Conceptual)
	•	Understood LLMs as next-token prediction systems
	•	Learned how large-scale text data is:
	•	Collected
	•	Cleaned
	•	Tokenized
	•	Used to create implicit supervision (no explicit labels)
	•	Differentiated between:
	•	Pretraining
	•	Instruction tuning
	•	RLHF (high-level understanding only)

3. Attention Mechanism (Core Focus)
	•	Developed intuition for self-attention
	•	Understood the role of:
	•	Queries (Q)
	•	Keys (K)
	•	Values (V)
	•	Learned attention as a token interaction and routing mechanism, not memory or reasoning
	•	Traced how attention determines which tokens influence the next-token prediction

Key takeaway:

Attention decides which tokens matter for the next token, not what the answer is.

4. Transformer Architecture (Introductory)
	•	Studied the transformer block at a high level:
	•	Token embeddings
	•	Positional information
	•	Self-attention
	•	Feed-forward layers
	•	Residual connections and layer normalization
	•	Understood differences between:
	•	Encoder-only
	•	Decoder-only (GPT-style)
	•	Encoder–decoder architectures
	•	Clarified why modern LLMs (ChatGPT, GPT-4, Claude) are decoder-only models

⸻

Code Artifacts Built

Project: Attention Mechanism from Scratch

A minimal implementation of self-attention was built to validate understanding.

Scope
	•	Implemented attention using NumPy
	•	Explicit computation of:
	•	Query, Key, Value matrices
	•	Dot-product attention
	•	Softmax normalization
	•	Weighted sum of values
	•	Printed intermediate matrices to inspect behavior

Purpose
	•	Remove abstraction layers
	•	Observe how attention weights change with inputs
	•	Build intuition transferable to transformer-based systems

Deliverables
	•	attention.py
	•	Console outputs showing:
	•	Attention scores
	•	Normalized weights
	•	Final attended representations

⸻

Outcomes

By the end of Week 1:
	•	Able to explain attention and transformers without equations
	•	Able to trace:

tokens → embeddings → attention → output representation


	•	Understood why:
	•	Transformers scale better than RNNs
	•	Attention is the foundation of all modern LLM capabilities
	•	External memory (RAG) is required despite large context windows
	•	Produced executable code demonstrating attention mechanics

⸻

Key Learnings
	•	LLMs do not “understand” text — they predict tokens probabilistically
	•	Attention is a context-weighting mechanism, not intelligence
	•	Architectural understanding is critical before building RAG or agents
	•	Debugging AI systems requires knowing where failures originate (attention, context, data)

⸻

Explicitly Deferred

The following were intentionally not covered in Week 1:
	•	Fine-tuning or training models
	•	Prompt engineering techniques
	•	Retrieval-Augmented Generation (RAG)
	•	Agents or tool calling
	•	Performance or optimization concerns

These are addressed in subsequent weeks once foundational understanding is solid.

⸻

Status

Week 1 completed successfully.
Foundation established for moving into RAG engineering and applied LLM systems.