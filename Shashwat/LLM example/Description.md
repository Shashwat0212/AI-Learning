# Running Phi-3 Mini Locally with Quantization (Step-by-Step Notes)

These notes break down the provided notebook/script into **logical sections**, explain **what each part does**, **why it matters**, and capture **practical insights** you can later push to GitHub as a `.md` reference.

---

## 📌 Conceptual Foundations (Added Explanations)

### 1. What is CUDA?

**CUDA (Compute Unified Device Architecture)** is NVIDIA’s parallel computing platform that allows Python libraries like PyTorch to run tensor operations on the GPU instead of the CPU.

* CPU → few powerful cores (latency-optimized)
* GPU → thousands of smaller cores (throughput-optimized)

LLMs are essentially *massive matrix multiplications*. CUDA enables these operations to run **orders of magnitude faster**.

In this program:

* CUDA allows Phi-3 to run on your GPU
* Without CUDA → model would fall back to CPU → unusably slow

---

### 2. What is a Kernel?

A **kernel** is a small program that runs on the GPU.

In ML terms:

* Every operation like `matmul`, `attention`, `layernorm` launches GPU kernels
* PyTorch abstracts this away, but under the hood:

```
Python → PyTorch → CUDA kernel → GPU cores
```

When you restart the *Jupyter kernel*, you are restarting the **Python process**, not the GPU. The model weights must be reloaded and kernels re-registered.

---

### 3. What is NVIDIA T4 and its Capabilities?

If you’re seeing **T4**, it is:

* NVIDIA Tesla T4 (data-center GPU)
* 16 GB VRAM
* Designed for **inference**, not heavy training

Key capabilities:

* Excellent INT8 / FP16 performance
* Very good for **quantized LLMs (4-bit, 8-bit)**
* Limited raw FP32 compute

Why it works well here:

* Phi-3 + 4-bit quantization comfortably fits
* Ideal for local RAG inference workloads

---

### 4. Library-by-Library Explanation (Why Each Exists)

* **torch**

  * Core tensor + CUDA execution engine
  * Provides GPU abstraction

* **transformers**

  * Model definitions, generation logic, configs
  * Handles autoregressive decoding

* **tokenizers**

  * Fast Rust-backed tokenization
  * Converts text ↔ tokens efficiently

* **accelerate**

  * Device placement & sharding logic
  * Makes `device_map="auto"` work

* **bitsandbytes**

  * 4-bit / 8-bit quantized linear layers
  * Enables large models on small GPUs

* **huggingface_hub**

  * Model download, caching, auth

Without these:

* No GPU
* No quantization
* No pretrained model loading

---

### 5. Role of Hugging Face in This Program

Hugging Face provides:

1. **Model registry** (`microsoft/Phi-3-mini-4k-instruct`)
2. **Versioned weights + tokenizer**
3. **Download + local caching**
4. **Standard APIs** (`AutoModel`, `AutoTokenizer`)

Think of Hugging Face as:

> *GitHub + PyPI + Model Zoo for ML*

Once downloaded, everything runs **locally**.

---

### 6. What is Phi-3 and Why This Model?

**Phi-3 Mini (4k instruct)** is:

* ~3.8B parameter decoder-only transformer
* Instruction-tuned
* Optimized for reasoning and factual answers

Why choose it:

* Strong quality for its size
* Works extremely well with quantization
* Low VRAM requirement

Capabilities:

* Q&A
* Summarization
* RAG answer synthesis
* Tool reasoning (basic)

This makes it ideal as a **local RAG generator**.

---

### 7. bitsandbytes Config — What It Does (With Intuition)

```python
BitsAndBytesConfig(
  load_in_4bit=True,
  bnb_4bit_quant_type="nf4",
  bnb_4bit_compute_dtype=torch.float16
)
```

What happens conceptually:

* Original weight: FP16 (16 bits)
* Stored weight: NF4 (4 bits)
* Computation: still FP16

Analogy:

> Store books as summaries (NF4), read them fluently (FP16)

Result:

* ~75% VRAM reduction
* Minimal accuracy loss

---

### 8. What is Tokenizer Loading?

The tokenizer:

* Splits text into **tokens** (subwords)
* Maps tokens ↔ integers

Example:

```
"Explain RAG" → [23456, 7812, 91]
```

Tokenizer **must match the model** exactly.
Mismatch = garbage output.

---

### 9. What is Sharding? (The Reload Behavior You Saw)

**Sharding** means splitting model weights across devices.

With:

```python
device_map="auto"
```

Accelerate may:

* Put some layers on GPU
* Some on CPU (if needed)

When you restart:

* Python memory is wiped
* Weights reload from disk cache
* Sharding happens again

This is normal.

---

### 10. max_new_tokens, temperature & Output Shape

```python
out = model.generate(...)
```

Output shape:

```
out = [ [token_1, token_2, ..., token_n] ]
```

Why `out[0]`?

* Batch size = 1
* First (and only) generated sequence

Parameters:

* **max_new_tokens** → hard stop
* **temperature**:

  * 0.2 = deterministic
  * 0.7 = balanced
  * 1.0+ = creative

For RAG → prefer **low temperature**.

---

### 11. End-to-End Flow Diagram

```
[ User Prompt ]
      ↓
[ Tokenizer ]
      ↓
[ Token IDs ]
      ↓
[ Phi-3 Model (4-bit, CUDA) ]
      ↓
[ Autoregressive Decoding ]
      ↓
[ Generated Tokens ]
      ↓
[ Tokenizer Decode ]
      ↓
[ Text Output ]
```

This script implements **everything except retrieval**.

## 1. Environment Pinning & Compatibility

```python
# transformers==4.40.2
# accelerate==0.30.1
# tokenizers==0.19.1
# bitsandbytes
# huggingface_hub
```

### Why this matters

* **Phi-3-mini-4k-instruct is NOT compatible with transformers >= 4.41**.
* Hugging Face models with custom `trust_remote_code=True` are *very sensitive* to version drift.

### Key Insight

Treat LLM environments like CUDA kernels:

> **Pin first, upgrade later (intentionally).**

This is especially important for:

* Quantization (bitsandbytes)
* Flash attention / custom kernels
* New tokenizer backends

---

## 2. Hardware & CUDA Sanity Check

```python
!nvidia-smi
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

### What this verifies

* GPU is visible to the system
* PyTorch is compiled with CUDA
* Correct GPU is selected (important for multi-GPU machines)

### Practical Tip

If `torch.cuda.is_available()` is `False`:

* Check CUDA version vs PyTorch build
* Check Docker `--gpus all`
* Check WSL vs native Linux mismatch

---

## 3. Dependency Installation (Reproducibility)

```bash
pip install \
  transformers==4.40.2 \
  accelerate==0.30.1 \
  tokenizers==0.19.1 \
  safetensors \
  huggingface_hub \
  bitsandbytes
```

### Why install explicitly even if "already installed"

* Jupyter kernels often drift
* Colab / VM images silently update
* `bitsandbytes` must match CUDA runtime

### RAG/MLOps Note

In production:

* Bake this into a **Docker image**
* Never `pip install` at runtime

---

## 4. Hugging Face Authentication

```python
import os
os.environ["HF_TOKEN"] = "hf_your_token_here"
assert "HF_TOKEN" in os.environ
```

### What this does

* Enables gated model access
* Allows authenticated model pulls

### Security Note

⚠️ **Never hardcode tokens in GitHub**

Use instead:

* `.env` files
* `os.environ` injection
* Secret managers (Vault, SSM, GH Secrets)

---

## 5. Model Selection: Phi-3 Mini

```python
model_id = "microsoft/Phi-3-mini-4k-instruct"
```

### Why Phi-3 Mini?

* Strong instruction tuning
* Small footprint (~3.8B params)
* Excellent quality / VRAM tradeoff

### RAG Context

Phi-3 Mini is a **great local generator** for:

* RAG answer synthesis
* Document Q&A
* Tool-augmented pipelines

---

## 6. 4-bit Quantization with bitsandbytes

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
```

### What NF4 does

* NormalFloat4 quantization
* Preserves distribution shape better than int4
* Designed specifically for LLM weights

### Trade-offs

| Aspect  | Effect       |
| ------- | ------------ |
| VRAM    | ↓↓↓          |
| Speed   | Slight ↓     |
| Quality | Minimal loss |

This is **ideal for local RAG inference**.

---

## 7. Tokenizer Loading

```python
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    token=True
)
```

### Notes

* `token=True` uses `HF_TOKEN`
* Tokenizers are often model-specific

### Common Pitfall

Mismatch between tokenizer + model revision = broken generations

---

## 8. Model Loading (The Critical Part)

```python
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    token=True,
    device_map="auto",
    quantization_config=bnb_config,
    trust_remote_code=True,
)
```

### Key Flags Explained

* `device_map="auto"`

  * Automatically shards model across GPUs / CPU

* `quantization_config=bnb_config`

  * Activates 4-bit loading

* `trust_remote_code=True`

  * Required for Phi-3 custom architecture

⚠️ **Never set `trust_remote_code=True` for untrusted models**

---

## 9. Prompting & Inference

```python
prompt = "Explain RAG (transformers) in simple terms."
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

out = model.generate(
    **inputs,
    max_new_tokens=100,
    temperature=0.7,
)

print(tokenizer.decode(out[0], skip_special_tokens=True))
```

### What happens here

1. Text → tokens
2. Tokens → GPU
3. Autoregressive generation
4. Tokens → decoded text

### Generation Controls

* `temperature=0.7` → balanced creativity
* `max_new_tokens=100` → hard stop

For RAG:

* Use **lower temperature (0.2–0.4)**
* Prefer factual consistency

---

## 10. Where This Fits in a RAG System

This script represents:

✅ **The Generator Node**

Missing pieces (next steps):

* Embedding model (e5, bge, Instructor)
* Vector store (FAISS / Chroma)
* Retriever
* Prompt template with retrieved context

---

## TL;DR Architecture Mapping

```
[ User Query ]
      ↓
[ Retriever (FAISS) ]
      ↓
[ Context + Prompt ]
      ↓
[ Phi-3 Mini (this code) ]
      ↓
[ Answer ]
```

---
