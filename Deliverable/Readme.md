Week 4 — CLI LLM Playground (Colab‑First, Step‑by‑Step Build Guide)

Purpose of this document
This is a hands‑on, incremental tutorial designed so you write code in small chunks, run explicit validations after each section, and keep a clean, reproducible Colab‑compatible codebase that you can push to a GitHub branch.

You should not copy–paste everything at once. Each section is intentionally small, testable, and mapped to a Week‑4 learning objective.

⸻

How to Use This Guide

Workflow you should follow:
	1.	Read one section
	2.	Write the code yourself (line‑by‑line)
	3.	Run the validation cell
	4.	Compare with the Checkpoint Snapshot at the end of the section
	5.	Commit (optional but recommended)

If a section fails, do not continue. Fix it first.

⸻

Target Environment (Important)

This guide assumes:
	•	Google Colab (T4) for reproducibility
	•	Python 3.10+
	•	Hugging Face transformers (not Ollama)
	•	Single‑file CLI logic (later splittable into modules)

Why Colab?
	•	Deterministic GPU
	•	No local daemon dependencies
	•	Easy for others to reproduce later

⸻

Project Goal (Reminder)

You are building a CLI‑style LLM playground that allows you to:
	•	Separate system prompt vs user prompt
	•	Control temperature and top‑p at runtime
	•	Observe token usage and latency
	•	Predict output changes before execution

No RAG. No tools. No agents.

⸻

Section 0 — Colab & Repo Setup (Validation: environment boots)

Step 0.1 — Create a New Branch

In your local repo:

git checkout -b week4-cli-playground

This branch will contain only Week‑4 work.

⸻

Step 0.2 — Open a New Colab Notebook
	•	Name it: week4_cli_llm_playground.ipynb
	•	Set runtime to GPU (T4)

⸻

Step 0.3 — Install Dependencies

You write this cell:

!pip install -q transformers accelerate sentencepiece


⸻

Step 0.4 — Validation

Run:

import torch
import transformers

print(torch.cuda.get_device_name(0))
print(transformers.__version__)

Expected:
	•	A T4 GPU name
	•	No import errors

⸻

✅ Checkpoint Snapshot (Section 0)

At this point, your notebook should:
	•	Run on GPU
	•	Import transformers successfully

Do not proceed if this fails.

⸻

Section 1 — Load a Base LLM (Validation: single response generation)

Week‑4 concepts used:
	•	Deterministic inference baseline
	•	Model as a fixed distribution

⸻

Step 1.1 — Choose a Model

Use a small, stable instruct model:

Recommended:

mistralai/Mistral-7B-Instruct-v0.2

(Any instruct‑tuned model is acceptable, but do not change later.)

⸻

Step 1.2 — Load Tokenizer and Model

You write this cell slowly:

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto"
)


⸻

Step 1.3 — Validation: Raw Generation

prompt = "Explain temperature in language models in one sentence."

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=False
)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))

Expected:
	•	One deterministic, boring answer
	•	No sampling

⸻

✅ Checkpoint Snapshot (Section 1)

You now have:
	•	A working LLM
	•	Deterministic decoding
	•	GPU‑backed inference

This is your baseline distribution.

⸻

Section 2 — Introduce a System Prompt (Validation: behavior shift)

Week‑4 concepts used:
	•	Prompt hierarchy
	•	Behavioral boundaries

⸻

Step 2.1 — Define a System Prompt

SYSTEM_PROMPT = """
You are a strict technical assistant.

Rules:
- Answer concisely
- Use bullet points when possible
- Do not add examples unless asked
""".strip()


⸻

Step 2.2 — Compose System + User Prompt

def build_prompt(system_prompt: str, user_prompt: str) -> str:
    return f"""
<system>
{system_prompt}
</system>

<user>
{user_prompt}
</user>

<assistant>
""".strip()


⸻

Step 2.3 — Validation: Compare Behavior

user_prompt = "Explain temperature in language models."

full_prompt = build_prompt(SYSTEM_PROMPT, user_prompt)

inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=100, do_sample=False)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))

Expected:
	•	Shorter
	•	More structured
	•	Less narrative

⸻

✅ Checkpoint Snapshot (Section 2)

You have now:
	•	Explicit system vs user separation
	•	Behavioral control without changing the task

This distinction is foundational for RAG and agents.

⸻

Section 3 — Add Temperature Control (Validation: entropy change)

Week‑4 concepts used:
	•	Softmax temperature
	•	Entropy control

⸻

Step 3.1 — Parameterize Generation

def generate_response(prompt: str, temperature: float):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=True,
        temperature=temperature
    )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


⸻

Step 3.2 — Validation: Temperature Sweep

for t in [0.2, 0.5, 0.9]:
    print("\nTemperature:", t)
    print(generate_response(full_prompt, temperature=t))

Expected:
	•	0.2: conservative, repetitive
	•	0.9: verbose, varied, riskier

⸻

✅ Checkpoint Snapshot (Section 3)

You can now:
	•	Predict output before running
	•	Control entropy explicitly

This is decoding intuition, not prompt hacking.

⸻

Section 4 — Add Top‑p (Validation: breadth vs sharpness)

Week‑4 concepts used:
	•	Nucleus sampling
	•	Probability mass truncation

⸻

Step 4.1 — Extend Generator

def generate_response(prompt: str, temperature: float, top_p: float):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=True,
        temperature=temperature,
        top_p=top_p
    )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


⸻

Step 4.2 — Validation: Top‑p Sweep

for p in [0.7, 0.9, 0.95]:
    print("\nTop‑p:", p)
    print(generate_response(full_prompt, temperature=0.7, top_p=p))

Expected:
	•	Low top‑p: focused, safe
	•	High top‑p: broader phrasing

⸻

✅ Checkpoint Snapshot (Section 4)

You now understand:
	•	Temperature = sharpness
	•	Top‑p = breadth

You can control them independently.

⸻

Section 5 — Token Usage & Latency (Validation: instrumentation works)

Week‑4 concepts used:
	•	Cost awareness
	•	Prompt efficiency

⸻

Step 5.1 — Add Token Counting

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


⸻

Step 5.2 — Time the Generation

import time

start = time.time()
response = generate_response(full_prompt, temperature=0.7, top_p=0.9)
latency = time.time() - start

print("Response tokens:", count_tokens(response))
print("Latency (s):", round(latency, 2))


⸻

✅ Checkpoint Snapshot (Section 5)

You can now answer:

“Which part of my prompt is expensive?”

This skill directly transfers to RAG.

⸻

Section 6 — Final CLI Loop (Optional Extension)

At this point you have all primitives needed to wrap this into:
	•	a Python CLI (while True: loop)
	•	/temp and /topp commands
	•	session‑level experiments

This is left as an integration exercise, since you already validated every component independently.

⸻

Final State (Week‑4 Exit Criteria)

You have built:
	•	A reproducible LLM playground
	•	Explicit system vs user separation
	•	Live decoding control
	•	Token + latency instrumentation

Most importantly:

You can now predict LLM behavior before execution.

⸻

Next Week

Week‑5 will assume this playground exists and will layer retrieval uncertainty on top of a system you already control.

Do not skip this foundation.