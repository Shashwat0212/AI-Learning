# Week 2 — Transformer Architecture (GPT)

This branch focuses on understanding and implementing the **decoder-only Transformer**
architecture used in GPT-style language models.

## What This Covers

- Encoder vs Decoder vs Decoder-only Transformers
- Learned positional embeddings
- Residual connections and LayerNorm (Pre-LN)
- Masked multi-head self-attention
- Feed-forward (MLP) blocks
- End-to-end forward pass from tokens → logits

## Project: Mini GPT Forward Pass

We implement a minimal GPT-style model from scratch in PyTorch.

### Implemented Components

- Token embeddings
- Positional embeddings
- Single Transformer block
  - Masked self-attention
  - MLP
  - Residual connections
  - LayerNorm
- Output projection to vocabulary logits

### Files

- `mini_gpt.py` — Complete forward-pass implementation

### Definition of Done

This project is complete when token IDs can be traced end-to-end
through the model to produce vocabulary logits, with full understanding
of each transformation step.

No training loop, datasets, or optimization is included in this branch.