# GPT-2 Forward Pass (HuggingFace) — Line-by-Line Explanation

This document explains **every line** of the GPT‑2 walkthrough notebook you are running in **VS Code (.ipynb) on a Tesla T4**.

The goal of the notebook is to:

1. Load GPT‑2
2. Tokenize text
3. Run a forward pass
4. Inspect logits and loss

---

## 1. Imports

```python
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
```

### Explanation

* `os`: Standard Python module (not strictly required here, but commonly imported for path/env handling).
* `torch`: PyTorch core library. Provides tensors, GPU support, and model execution.
* `AutoTokenizer`: HuggingFace factory that automatically selects the correct tokenizer for a model name.
* `AutoModelForCausalLM`: Loads a **causal language model** head (decoder-only, next-token prediction).

> Conceptually: `AutoModelForCausalLM` = Transformer decoder + LM head → logits over vocabulary.

---

## 2. Configuration

```python
MODEL_NAME = "gpt2"
SAMPLE_TEXT = "Hello from VS Code on a Tesla T4! Let's inspect GPT-2 logits and loss."
```

### Explanation

* `MODEL_NAME`: HuggingFace model identifier. `"gpt2"` refers to the **small GPT‑2 (124M params)**.
* `SAMPLE_TEXT`: Input prompt we will tokenize and feed to the model.

---

## 3. Device Selection (CPU vs GPU)

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)
if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))
```

### Explanation

* `torch.cuda.is_available()`: Checks whether CUDA is accessible.
* If available, we use GPU (`"cuda"`), otherwise CPU.
* `torch.cuda.get_device_name(0)`: Prints GPU model (Tesla T4 in your case).

> This ensures **model weights and tensors live on the same device**, which is mandatory in PyTorch.

---

## 4. Load Tokenizer

```python
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
```

### Explanation

* Downloads (or loads from cache) the tokenizer associated with GPT‑2.
* GPT‑2 uses **byte-pair encoding (BPE)** over bytes → subword tokens.

---

## 5. Handle GPT‑2 Padding Token

```python
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
```

### Explanation

* GPT‑2 **does not define a padding token** by default.
* HuggingFace expects one when batching.
* We reuse `eos_token` (end-of-sequence) as `pad_token`.

> This is a practical fix, not a modeling change.

---

## 6. Load GPT‑2 Model

```python
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.to(device)
model.eval()
```

### Explanation

* `from_pretrained`: Downloads GPT‑2 weights.
* `model.to(device)`: Moves **all parameters** to GPU or CPU.
* `model.eval()`: Sets evaluation mode:

  * Disables dropout
  * Disables training-only layers

> Equivalent to `model.train(False)`.

---

## 7. Tokenization

```python
enc = tokenizer(
    SAMPLE_TEXT,
    return_tensors="pt",
    padding=True,
    truncation=True,
)
```

### Explanation

* Converts text → token IDs.
* `return_tensors="pt"`: Output PyTorch tensors.
* `padding=True`: Pads to max sequence length in batch.
* `truncation=True`: Cuts off text if too long.

Returned dictionary includes:

* `input_ids`
* `attention_mask`

---

## 8. Move Inputs to GPU

```python
input_ids = enc["input_ids"].to(device)
attention_mask = enc["attention_mask"].to(device)
```

### Explanation

* Tensors **must be on the same device as the model**.
* `attention_mask` tells GPT‑2 which tokens are real vs padding.

---

## 9. Inspect Tokenization

```python
print("input_ids shape:", tuple(input_ids.shape))
print("attention_mask shape:", tuple(attention_mask.shape))
print("Decoded back:", tokenizer.decode(input_ids[0]))
```

### Explanation

* Shapes:

  * `[batch_size, sequence_length]`
* `decode` verifies that tokenization is reversible.

---

## 10. Forward Pass with Loss

```python
with torch.no_grad():
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=input_ids,
    )
```

### Explanation

* `torch.no_grad()`: Disables gradient tracking (saves memory).
* Passing `labels=input_ids` tells HuggingFace to:

  * Shift tokens internally
  * Compute **cross-entropy loss** for next-token prediction

> GPT‑2 predicts token *t+1* from tokens `[0..t]`.

---

## 11. Extract Logits and Loss

```python
logits = outputs.logits
loss = outputs.loss
```

### Explanation

* `logits`: Raw scores before softmax

  * Shape: `[batch, seq_len, vocab_size]`
* `loss`: Scalar

  * Mean negative log-likelihood over all valid tokens

---

## 12. Inspect Logits Shape

```python
print("logits shape:", tuple(logits.shape))
print("loss:", float(loss))
```

### Explanation

* `vocab_size ≈ 50,257` for GPT‑2.
* Loss tells you how surprised the model is by the next tokens.

---

## 13. Top‑K Token Prediction at One Position

```python
probs = torch.softmax(logits[batch_idx, pos], dim=-1)
topk = torch.topk(probs, k)
```

### Explanation

* Applies softmax → probability distribution.
* Extracts top‑K most likely next tokens.

This is exactly what **generation** is built on.

---

## 14. Decode Predicted Tokens

```python
topk_tokens = [tokenizer.decode([i]) for i in topk_ids]
```

### Explanation

* Converts token IDs → readable text fragments.
* GPT‑2 tokens may include leading spaces or partial words.

---

## 15. Manual Per‑Token Loss (Advanced Inspection)

```python
shift_logits = logits[:, :-1, :]
shift_labels = input_ids[:, 1:]
```

### Explanation

* GPT‑2 loss ignores the final token.
* Logits at position *t* predict label at *t+1*.

---

## 16. Negative Log‑Likelihood

```python
log_probs = torch.log_softmax(shift_logits, dim=-1)
nll = -log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1))
```

### Explanation

* Computes token‑level cross‑entropy manually.
* Lets you see **which tokens are hard to predict**.

---

## 17. Token‑by‑Token Inspection

```python
prev_tok = tokenizer.decode([input_ids[0, i].item()])
next_tok = tokenizer.decode([input_ids[0, i+1].item()])
```

### Explanation

* Shows:

  * Current token
  * Target next token
  * Corresponding loss

This is the **core training signal** of GPT‑style models.

---

## Mental Model Summary

* GPT‑2 is trained as:

  **P(xₜ₊₁ | x₀ … xₜ)**

* Logits → Softmax → Probabilities

* Loss = average surprise over next tokens

This notebook shows the **exact mechanics** used during GPT‑2 pretraining.

---

Next steps you may want to add:

* Text generation loop
* KV‑cache inspection
* Mixed precision (fp16)
* Comparing logits across layers

---

## Final Conceptual Closure: Why This Experiment Proves GPT-2 Is Decoder-Only

You now correctly understand the **core point of this entire experiment**, and it’s worth stating it cleanly so you can keep it in your document as a reference explanation.

### What We Deliberately Did

* We fed **raw, unmasked text** into GPT-2.
* We did **not** ask it to generate future tokens.
* Instead, we paused at an **intermediate position** and inspected:

  * The next-token probability distribution (logits → softmax)
  * The loss for the *actual* next token

Crucially, we did this **without letting the model see anything beyond that position**.

---

## Why This Demonstrates “No Future Access”

GPT-2 is a **decoder-only, causal language model**. That means:

> At position *t*, the model can only attend to tokens `[0 … t]`.

Even though the **entire sequence is passed in one tensor**, the model enforces a **causal attention mask** internally:

* Tokens at position *t* **cannot attend to** positions `> t`
* This is hard-coded in the attention mechanism
* There is no runtime path that leaks future information

So when we inspect predictions at `position = 5`, the model:

* Has *no idea* that "Tesla T4" appears later
* Cannot “cheat” by peeking ahead
* Is behaving exactly as it would during training

---

## Why We Chose a Middle Position (On Purpose)

If we only looked at the **final token**, it would be ambiguous whether the model had implicitly used the full context.

By choosing a **middle token**:

```
Hello | from | VS | Code | on |  a  | Tesla | T4 | ...
                      ↑
              we inspect here
```

We force the following guarantee:

* Everything to the right is **invisible** to the model
* The distribution we see is *purely causal*

This is the cleanest possible proof that:

> GPT-2 predicts strictly left-to-right, one token at a time.

---

## Why Passing `labels=input_ids` Is Still Correct

This often confuses people, so let’s be explicit.

Even though we pass the **full sequence** as `labels`, HuggingFace:

* Internally shifts labels by one position
* Computes loss only for valid causal positions
* Ignores the final token

So the loss is equivalent to:

```
for t in range(len(tokens) - 1):
    predict tokens[t+1] using tokens[:t]
```

No future leakage occurs.

---

## Training-Time and Inference-Time Are the Same Mechanism

This experiment shows something subtle but important:

* **Training** uses teacher forcing (true previous tokens)
* **Inference** uses generated tokens

But the **model computation itself is identical**.

Same transformer.
Same causal mask.
Same logits.

Only the *source of the previous token* changes.

---

## Why This Matters for Everything That Comes Next

Understanding this deeply unlocks:

* Why prompt wording matters
* Why RAG must prepend context (not append)
* Why hallucinations happen
* Why KV-caching works
* Why decoder-only models scale so well

Everything you’ll build next (generation, RAG, agents) rests on this exact behavior.

---

## One-Sentence Summary (Repo-Ready)

> This notebook intentionally inspects GPT-2 predictions at an intermediate token position to demonstrate that a decoder-only language model cannot access future tokens, even when the full sequence is provided, because causal self-attention strictly enforces left-to-right prediction.

---

End of walkthrough.
