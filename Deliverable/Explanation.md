
# Mini GPT Forward Pass — Intuitive Explanation

This document explains the `mini_gpt.py` file **intuitively and step‑by‑step**.

The goals are:

* Explain *what each library and concept is*
* Explain *what happens to the data at every step*
* Answer common conceptual doubts
* Keep the original code logic unchanged
* Build a strong mental model of GPT-style forward passes

---

## 1. What is the `torch` library?

`torch` (PyTorch) is a **numerical computing + automatic differentiation** library designed for deep learning.

At a high level, PyTorch provides:

* **Tensors** → multidimensional arrays (like NumPy, but faster and GPU‑aware)
* **nn.Module** → a way to define neural network layers as Python classes
* **Autograd** → automatic gradient computation (used during training)

In this project, we use PyTorch **only for forward computation**, not training.

### What is `nn.Embedding`?

```python
self.token_emb = nn.Embedding(vocab_size, embedding_dim)
```

An embedding layer is a **learned lookup table**:

* Input: integer token IDs
* Output: dense vectors

This is conceptually similar to **Word2Vec or GloVe**, but:

* Word2Vec = pretrained static embeddings
* `nn.Embedding` = learned *inside* the model

You can think of it as a dictionary:

```
Token ID → Vector
421      → [0.13, -0.7, 0.22, ...]
```

---

## 2. What does `(2, 8)` mean? What are `B`, `T`, `C`?

Throughout the code we use the convention:

| Symbol | Meaning                   | Example                |
| ------ | ------------------------- | ---------------------- |
| `B`    | Batch size                | 2 sequences at once    |
| `T`    | Time / sequence length    | 8 tokens per sequence  |
| `C`    | Channels / embedding size | 64‑dimensional vectors |

### Example

```python
idx.shape == (2, 8)
```

This means:

```
Batch 0: [17, 503, 12, 98, 421, 77, 9, 201]
Batch 1: [88,  41,  6,  19,  90, 11, 3,  55]
```

After embedding:

```python
x.shape == (2, 8, 64)
```

Now each token is a **64‑dimensional vector**.

---

## 3. Positional Embeddings — visual intuition

Transformers have **no built‑in notion of order**.

Without positional embeddings, these would look identical:

```
["I", "love", "AI"]
["AI", "love", "I"]
```

### What we do in code

```python
pos = torch.arange(T)
pos_emb = self.pos_emb(pos)
x = token_emb + pos_emb
```

### Concrete example

Assume:

```
Token embedding("cat") = [1.0, 0.5]
Position 0 embedding      = [0.1, 0.0]
Position 1 embedding      = [0.0, 0.2]
```

Then:

```
"cat" at position 0 → [1.1, 0.5]
"cat" at position 1 → [1.0, 0.7]
```

Same word, **different vector**, because position is different.

That is how order is injected.

---

## 4. Step‑by‑step data flow (with explanations)

Below is the **conceptual flow**, matching the code exactly.

### Step 1 — Input token IDs

```python
idx = torch.randint(0, vocab_size, (B, T))
```

* Pure integers
* No meaning yet

---

### Step 2 — Token embeddings

```python
token_vectors = token_embedding(idx)
```

**Why?**
Neural networks cannot reason over integers.

**Effect:**

```
(B, T) → (B, T, C)
```

---

### Step 3 — Positional embeddings

```python
position_vectors = position_embedding(0..T-1)
combined = token_vectors + position_vectors
```

**Why?**
To encode order information.

---

### Step 4 — LayerNorm before attention

```python
normalized = LayerNorm(combined)
```

**Why?**
Stabilizes scale before attention computation.

---

### Step 5 — Causal self‑attention

Each token asks:

> “Which previous tokens matter to me?”

Causal mask ensures:

```
Token i can only see tokens ≤ i
```

**Why?**
Prevents looking into the future during generation.

---

### Step 6 — Residual connection (attention)

```python
x = x + attention_output
```

**Why?**
The model learns *adjustments*, not replacements.

Yes — **residual = original input + attention output**.

---

### Step 7 — MLP (feed‑forward network)

```python
C → 4C → C
```

**Important:**

* No token interaction here
* Each token is processed independently

**Why?**
This is where non‑linear reasoning happens.

---

### Step 8 — Residual connection (MLP)

```python
x = x + mlp_output
```

Same logic as before: stability and expressiveness.

---

### Step 9 — Final LayerNorm

```python
x = LayerNorm(x)
```

**Why?**
Ensures clean, stable activations before prediction.

---

### Step 10 — Vocabulary projection

```python
logits = Linear(x)
```

Effect:

```
(B, T, C) → (B, T, vocab_size)
```

Each token position now has a score for **every possible next token**.

---

## 5. Residual connections (clarification)

Yes — your intuition is correct:

> **Residual = original input + sublayer output**

This allows:

* Better gradient flow
* Easier optimization
* Deeper networks

Without residuals, Transformers do not scale.

---

## 6. Variable naming clarification (mental mapping)

Although the code stays unchanged, here is how to *read* variables mentally:

| Code Variable | Mental Meaning                  |
| ------------- | ------------------------------- |
| `idx`         | token IDs                       |
| `x`           | current token representations   |
| `q, k, v`     | attention queries, keys, values |
| `att`         | attention weights               |
| `logits`      | vocabulary scores               |

If you later want, we can refactor names *without changing logic*.

---

## Final takeaway

> **Embedding = representation**
> **Attention = context gathering**
> **MLP = reasoning**
> **Linear head = decision**

This file implements a complete GPT forward pass in its simplest correct form.

---

This document will be updated with **future doubts and clarifications** as they come.
