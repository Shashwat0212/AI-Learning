# Week 4 — Prompting & LLM Control

**Total Time Commitment:** 8–10 hours
**Theme:** Controlling LLM behavior through prompts and decoding parameters

This week is about **developing intuition and control**, not adding infrastructure.

---

## Learning Objectives (What You Should Be Able to Do by the End of the Week)

By the end of Week 4, you should be able to:

* Reason about LLM output *before* running a prompt
* Explain why two prompts that look similar produce different outputs
* Predict how changing decoding parameters (temperature, top-p) alters response style
* Deliberately constrain or expand model behavior using system vs user prompts
* Build a minimal, well-instrumented CLI playground for prompt experimentation

---

## Core References (You Will Revisit These All Week)

| Topic                              | Book                           | Chapter  |
| ---------------------------------- | ------------------------------ | -------- |
| Prompt structure                   | Hands-On Large Language Models | Ch. 6    |
| Structured vs vague prompts        | Hands-On Large Language Models | Ch. 6    |
| Temperature mechanics              | Hands-On Large Language Models | Ch. 6    |
| Top-p (nucleus sampling) intuition | Hands-On Large Language Models | Ch. 6    |
| Softmax temperature math           | ML: Probabilistic Perspective  | Ch. 4    |
| Prompt hierarchy (system vs user)  | Hands-On Large Language Models | Ch. 6    |
| System prompt stability            | LLM Engineer’s Handbook        | Ch. 1, 9 |

---

## Part 1 — Learn (2–3 hours)

### 1. Prompt Structure (≈45–60 min)

Focus on how prompts are **interpreted**, not just written.

Key concepts to internalize:

* Instruction vs context vs data separation
* Why explicit structure (sections, bullet points, delimiters) improves reliability
* The difference between:

  * Asking for information
  * Assigning a role
  * Constraining output format

Study and compare:

* Vague prompt vs structured prompt
* Single-turn instruction vs multi-step instruction
* Open-ended outputs vs constrained outputs (lists, JSON, markdown)

Guiding question:

> “What is the model *allowed* to do given this prompt?”

---

### 2. Decoding Parameters: Temperature & Top-p (≈45–60 min)

Apply your intuition about probability distributions and sampling.

#### Temperature

* Temperature scales **logits**, not probabilities
* Low temperature (≈0–0.3):

  * Deterministic
  * Repetitive
  * Conservative completions
* High temperature (≈0.8–1.2):

  * More diverse phrasing
  * Creative but error-prone

Think in terms of **entropy control**, not creativity.

#### Top-p (Nucleus Sampling)

* Truncates cumulative probability mass
* Often more stable than top-k when combined with temperature

Failure modes:

* Too low → brittle, repetitive outputs
* Too high → incoherent or off-task outputs

Mental model:

> Temperature shapes **sharpness**, top-p shapes **breadth**.

---

### 3. System vs User Prompts (≈30–45 min)

Understand prompt hierarchy and control priority.

Key ideas:

* System prompt defines **behavioral boundaries**
* User prompt defines **task intent**
* System prompts are more stable than repeating rules in user input

Reason through examples:

* Persona enforcement ("You are a strict compiler")
* Safety or formatting guarantees
* Domain restriction ("Only answer using the provided context")

Checkpoint:

> “This behavior belongs in the system prompt, not the user prompt.”

---

## Part 2 — Build (6–7 hours)

## Project: CLI LLM Playground

This is a **controlled experimentation environment**, not a product.

**Non-goals:**

* No UI polish
* No agents
* No tools
* No RAG
* No external memory beyond the session

---

### Step 1 — Basic CLI Chat Loop (≈1–1.5 hrs)

Requirements:

* Terminal-based chat interface
* Persistent conversation loop
* Clear separation of:

  * System prompt
  * User input
  * Model output

Design decisions:

* Where the system prompt lives (config vs hardcoded)
* Whether conversation history is appended or summarized

Deliverable:

* Continuous chat without restarting the program

---

### Step 2 — Temperature Toggle (≈1–1.5 hrs)

Requirements:

* CLI flag or interactive command to set temperature
* Ability to change temperature mid-session

Experiments:

* Same prompt at temperatures: 0.2, 0.5, 0.9

Observe:

* Sentence length
* Word choice variability
* Error rate

Document observations in comments or a README.

---

### Step 3 — Token Usage Logging (≈1–1.5 hrs)

Track at minimum:

* Prompt tokens
* Completion tokens
* Total tokens per turn

Optional:

* Tokens per second
* Rolling averages per session

Guiding question:

> “Which part of my prompt is expensive?”

---

### Step 4 — Prompt Experiments (≈2–2.5 hrs)

Run systematic experiments:

1. Same task, different system prompts
2. Same prompt, different temperature
3. Over-constrained vs under-constrained prompts
4. Removing vs adding explicit output format

Keep notes:

* What surprised you?
* What was unstable?
* What became predictable?

---

## Done When (Exit Criteria)

You are **done with Week 4** when:

* You can predict output changes *before* running a prompt
* You can justify changes using:

  * Prompt structure
  * Temperature / top-p
  * System vs user roles
* Your CLI playground lets you test hypotheses quickly

This intuition is foundational for:

* RAG grounding
* Tool calling
* Agent behavior control

**Week 5 will assume you can control the model, not just talk to it.**
