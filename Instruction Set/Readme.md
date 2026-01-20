# Week 4 – Instruction Dataset Generation (Local, T4-safe)

This notebook (`Deliverable.ipynb`) implements **Supervised Fine-Tuning (SFT) data generation** using a **local open-source LLM**.

It mirrors the *LLM Engineer's Handbook* pipeline, adapted for:

* **Local execution** (Jupyter notebook, no external API calls)
* **Tesla T4 GPU** (16 GB VRAM) — with memory-efficient attention backends
* **Open-source models** (`Qwen/Qwen2.5-1.5B-Instruct`) — instruction-tuned, ~1.5B parameters

**High-level transformation:**

```
Raw documents → Text extraction → LLM transformation → Instruction–Answer pairs (JSON)
```

These pairs are structured and labeled — ready for **Supervised Fine-Tuning (Week 5)**.

---

## Notebook Structure (`Deliverable.ipynb`)

The notebook is organized into **12 logical cells** (in execution order):

| Cell | Purpose | Time |
|------|---------|------|
| 1 | Install dependencies | 10s |
| 2 | Import libraries & environment config | 14s |
| 3 | Load model & tokenizer (Qwen2.5-1.5B) | 1m |
| 4 | Text processing utilities (`clean_text`, `load_articles_from_json`) | — |
| 5 | JSON & tokenization utilities (`extract_first_json_object`, `truncate_to_max_tokens`) | — |
| 6 | Core LLM generation function (`generate_instruction_answer_pairs`) | — |
| 7 | Text chunking (`extract_substrings`) | — |
| 8 | Pipeline orchestration (`create_instruction_dataset`) | — |
| 9 | Load raw dataset (Wikipedia) | 8m |
| 10 | Run full pipeline | Variable |
| 11 | Display results | — |

**Order matters:** Cells must run top-to-bottom. Dependencies are loaded first; functions defined before use.

---

## Quick Start

### Step 1: Install Dependencies

Run once per environment:

```bash
pip install \
  transformers>=4.41 \
  accelerate>=0.30 \
  bitsandbytes>=0.43 \
  sentencepiece>=0.2 \
  datasets==2.20.0 \
  tqdm==4.66.4 \
  pydantic>=2.6
```

### Step 2: Hugging Face Authentication (Optional)

Only required if you plan to push datasets or models to the Hub. Set the token in your environment:

```bash
export HF_TOKEN="<your_hf_token_here>"
```

Or in the notebook (but **do NOT commit real tokens** — use environment variables instead):

```python
import os
os.environ["HF_TOKEN"] = "<your_hf_token_here>"
```

### Step 3: Run the Notebook

Open `Deliverable.ipynb` in Jupyter and run cells top-to-bottom. Estimated total time: **~20–30 minutes** (on T4 GPU with 10 Wikipedia articles).

---

## Detailed Walkthrough

### Model & Tokenizer Loading (Teacher Model)

We use **Qwen/Qwen2.5-1.5B-Instruct** because:

* **Fast on Tesla T4** — Optimized inference on mid-range GPUs
* **Low VRAM footprint** — Fits comfortably in 16GB T4 memory with 4-bit quantization
* **Strong instruction-following** — Reliable JSON output and prompt adherence

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token  # Avoid warnings

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    load_in_4bit=True,              # 4-bit quantization
    torch_dtype=torch.float16       # Float16 for speed
)

model.eval()
```

---

### CUDA Memory & Attention Safety (CRITICAL FOR T4)

This prevents catastrophic **attention OOMs** (quadratic memory growth) on Tesla T4.

```python
import os, torch

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Attention backend configuration (T4 compatibility)
torch.backends.cuda.enable_flash_sdp(False)          # Not supported on T4
torch.backends.cuda.enable_mem_efficient_sdp(True)   # Preferred for T4
torch.backends.cuda.enable_math_sdp(True)            # Safe fallback
```

---

### Text Processing & Cleaning

The raw dataset needs cleaning before LLM processing. This removes noise and normalizes spacing.

```python
def clean_text(text: str) -> str:
    """Remove special chars, normalize whitespace."""
    text = re.sub(r"[^\w\s.,!?']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

---

### Text Extraction & Chunking

Splits long documents into semantically coherent chunks (200–500 chars each). This keeps the LLM focused on a single topic per call.

```python
def extract_substrings(
    dataset: Dataset,
    text_column: str,
    min_length: int = 200,
    max_length: int = 500
) -> List[str]:
    extracts = []
    sentence_pattern = r"(?<!\w\.\w.)(?<![A-Z][a-z]\.) (?<=\.|\?|!)\s"

    for article in dataset[text_column]:
        cleaned = clean_text(article)
        sentences = re.split(sentence_pattern, cleaned)
        current = ""

        for s in sentences:
            if len(current) + len(s) <= max_length:
                current += s + " "
            else:
                if len(current) >= min_length:
                    extracts.append(current.strip())
                current = s + " "

        if len(current) >= min_length:
            extracts.append(current.strip())

    return extracts
```

---

## Utility Functions

### JSON Extraction (Production-grade)

LLMs often hallucinate or add commentary around JSON. This parser **robustly extracts the first valid JSON object**, ignoring junk before/after.

```python
def extract_first_json_object(text: str) -> dict:
    decoder = json.JSONDecoder()
    text = text.strip()

    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("No valid JSON object found")
```

### Token-Level Safety Truncation

Mandatory to prevent quadratic attention OOMs on T4.

```python
def truncate_to_max_tokens(text, tokenizer, max_tokens=512):
    """Truncate text to fit within token budget (prevents OOM)."""
    tokens = tokenizer(
        text,
        truncation=True,
        max_length=max_tokens,
        return_tensors="pt"
    )
    return tokenizer.decode(tokens["input_ids"][0], skip_special_tokens=True)
```

---

## Core Pipeline Functions

### Instruction-Answer Generation

This is the **teacher-model transformation step**. The model reads each extract and generates structured instruction-answer pairs suitable for fine-tuning.

**Key improvements in implementation:**

* **Temperature tuned to 0.5** — Ensures more consistent, structured JSON output
* **New token extraction** — Only the model's NEW tokens are decoded (not the prompt echoed back)
* **Simplified prompt** — Clearer instructions reduce hallucination and off-topic generation
* **Improved error handling** — Gracefully skips malformed JSON instead of crashing
    extract: str,
    tokenizer,
    model,
    max_new_tokens: int = 512,
    temperature: float = 0.5  # Lowered for consistency
) -> List[Tuple[str, str]]:
    """
    Generate instruction-answer pairs from a text extract using LLM.
    """
    # Hard safety cap (prevents quadratic attention explosion)
    extract = truncate_to_max_tokens(extract, tokenizer, max_tokens=512)

    prompt = f"""Generate exactly 3 instruction-answer pairs in JSON format ONLY.

{{
  "instruction_answer_pairs": [
    {{"instruction": "first question about the text", "answer": "answer based on the text"}},
    {{"instruction": "second question about the text", "answer": "answer based on the text"}},
    {{"instruction": "third question about the text", "answer": "answer based on the text"}}
  ]
}}

TEXT:
{extract}

OUTPUT JSON:"""

    messages = [
        {"role": "system", "content": "Output ONLY valid JSON. Do not add any text before or after."},
        {"role": "user", "content": prompt},
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
            top_p=0.9
        )

    # CRITICAL: Extract only NEW tokens (not the input prompt)
    new_tokens = outputs[0][inputs.shape[1]:]
    decoded = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    try:
        data = extract_first_json_object(decoded)
        pairs = [
            (p.get("instruction", ""), p.get("answer", ""))
            for p in data.get("instruction_answer_pairs", [])
            if p.get("instruction") and p.get("answer")  # Skip incomplete pairs
        ]
        return pairs if pairs else []
    except Exception as e:
        # Silent fail: return empty list instead of crashing
        return []
```

---

### Dataset Assembly Pipeline

Orchestrates the full transformation: extract chunks → generate pairs → assemble dataset.

```python
def create_instruction_dataset(dataset: Dataset, tokenizer, model) -> Dataset:
    """
    Transform raw dataset into instruction-answer pairs.
    """
    # Extract text chunks
    extracts = extract_substrings(dataset, text_column="text")

    # Generate pairs from each chunk
    pairs = []
    for extract in tqdm(extracts, desc="Generating pairs"):
        pairs.extend(generate_instruction_answer_pairs(extract, tokenizer, model))
        torch.cuda.empty_cache()  # Prevent OOM

    # Assemble into HF Dataset
    if not pairs:
        return Dataset.from_dict({"instruction": [], "output": []})
    
    instructions, outputs = zip(*pairs)

    return Dataset.from_dict({
        "instruction": list(instructions),
        "output": list(outputs)
    })
```

---

## Running the Pipeline

### Load Raw Data

Using Wikipedia as an example source (10 articles for testing):

```python
from datasets import load_dataset

wiki = load_dataset(
    "wikipedia",
    "20220301.en",
    split="train[:10]"  # Small subset for testing
)
```

### Execute Full Pipeline

### Execute Full Pipeline

```python
print("🚀 Starting instruction dataset generation pipeline...\n")

# Create instruction dataset
instruction_dataset = create_instruction_dataset(
    wiki,
    tokenizer,
    model,
    text_column="text",
    min_length=200,
    max_length=500
)

print(f"✓ Instruction dataset created with {len(instruction_dataset)} examples")

# Split into train/test (90/10)
split_dataset = instruction_dataset.train_test_split(test_size=0.1)
print(f"Train: {len(split_dataset['train'])} | Test: {len(split_dataset['test'])}")
```

---

## Expected Output

---

## Expected Output

Example instruction-answer pair generated from a Wikipedia article on machine learning:

```
INSTRUCTION:
"Explain the role of feature stores in machine learning systems."

OUTPUT:
"Feature stores provide a centralized mechanism for managing, versioning, 
and serving features consistently across training and inference pipelines."
```

Each pair is grounded in the original text and suitable for supervised fine-tuning.

---

## What You've Built

By completing this notebook, you have:

* ✅ A fully **local Supervised Fine-Tuning (SFT) dataset pipeline**
* ✅ Generated safely on **Tesla T4** (memory-efficient attention + 4-bit quantization)
* ✅ A production-grade **JSON extraction** layer (handles LLM hallucinations)
* ✅ A reusable **text chunking** strategy (semantic boundaries)
* ✅ Dataset ready for **fine-tuning (Week 5)** or evaluation

---

## Mental Model – How This Works End-to-End

**The core insight:** We tell the model **once** how to transform text (the prompt template), then apply it repeatedly to many chunks.

```
Raw text chunks
     ↓
[Prompt template] → LLM → JSON output
     ↓
Structured (instruction, answer) pairs
     ↓
HF Dataset (ready for SFT)
```

This is the **bridge between unstructured data and fine-tuning**—the conceptual heart of Week 4.

---

## Next Steps

* **Week 5:** Fine-tune a model on this instruction dataset using `transformers.Trainer`
* **Scaling:** Replace Wikipedia with your own domain data (docs, articles, conversations)
* **Optimization:** Experiment with different prompts, models, or chunking strategies

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `CUDA out of memory` | Reduce `max_length` in `extract_substrings` or `max_new_tokens` in generation |
| `No valid JSON found` | Check that model output starts with `{`; lower `temperature` to 0.3 |
| Slow generation | Reduce Wikipedia subset (use `split="train[:5]"` for testing) |
| Token parsing fails | Ensure tokenizer is set: `tokenizer.pad_token = tokenizer.eos_token` |
