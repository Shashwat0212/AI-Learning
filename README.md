# Week 4 — Prompting & LLM Control

**Total Time Commitment:** 8–10 hours
**Theme:** Controlling LLM behavior through prompts and decoding parameters

---

## Learning Objectives (What You Should Be Able to Do by the End of the Week)

By the end of Week 4, you should be able to:

* Reason about LLM output *before* running a prompt
* Explain why two prompts that look similar produce different outputs
* Predict how changing decoding parameters (temperature, top-p) alters response style
* Deliberately constrain or expand model behavior using system vs user prompts
* Build a minimal but well-instrumented CLI playground for prompt experimentation

This week is about **developing intuition and control**, not adding new infrastructure.

---

## Part 1 — Learn (2–3 hours)

### 1. Prompt Structure (≈45–60 min)

Focus on how prompts are *interpreted*, not just written.

Key concepts to internalize:

* **Instruction vs context vs data** separation
* Why explicit structure (bullet points, sections, delimiters) improves reliability
* The difference between:

  * Asking for information
  * Assigning a role
  * Constraining output format

Study examples such as:

* Vague prompt vs structured prompt
* Single-turn instruction vs multi-step instruction
* Open-ended vs constrained outputs (lists, JSON, markdown)

You should start asking yourself:

> “What is the model *allowed* to do given this prompt?”

---

### 2. Decoding Parameters: Temperature & Top-p (≈45–60 min)

You already understand sampling from probability distributions—apply that intuition here.

Cover the following in detail:

#### Temperature

* What temperature actually scales (logits, not probabilities)
* Low temperature (≈0–0.3):

  * Deterministic
  * Repetitive
  * Conservative completions
* High temperature (≈0.8–1.2):

  * Diverse phrasing
  * Creative but error-prone

Think in terms of **entropy control**.

#### Top-p (Nucleus Sampling)

* How top-p truncates the probability mass
* Why top-p + temperature is often better than top-k
* Failure modes when top-p is too low or too high

Mental model to adopt:

> Temperature shapes *sharpness*, top-p shapes *breadth*.

---

### 3. System vs User Prompts (≈30–45 min)

Understand prompt hierarchy and control priority.

Key ideas:

* System prompt defines **behavioral boundaries**
* User prompt defines **task intent**
* Why system prompts are more stable than repeating instructions in user input

Examples to reason about:

* Persona enforcement ("You are a strict compiler")
* Safety or formatting guarantees
* Domain restriction ("Only answer using the provided context")

By the end of this section, you should be able to say:

> “This behavior belongs in the system prompt, not the user prompt.”

---

## Reading (Integrated)

**Primary Reading:**

* *LLM Engineer’s Handbook* — Prompting section

Read actively:

* Rewrite example prompts in your own words
* Note which parts are doing *control* vs *content*
* Identify implicit assumptions made by the model

---

## Part 2 — Build (6–7 hours)

### Project: CLI LLM Playground

This is a **controlled experimentation environment**, not a product.

---

### Step 1 — Basic CLI Chat Loop (≈1–1.5 hrs)

Requirements:

* Terminal-based chat interface
* Persistent conversation loop
* Clear separation of:

  * System prompt
  * User input
  * Model output

Design decisions to make deliberately:

* Where the system prompt lives (config file vs hardcoded)
* Whether conversation history is appended or summarized

Deliverable:

* You can chat continuously without restarting the program

---

### Step 2 — Temperature Toggle (≈1–1.5 hrs)

Add runtime control over temperature.

Requirements:

* CLI flag or interactive command to set temperature
* Ability to change temperature mid-session

Experiments to run:

* Same prompt at temperatures: 0.2, 0.5, 0.9
* Observe:

  * Sentence length
  * Word choice variability
  * Error rate

Document your observations in comments or a README.

---

### Step 3 — Token Usage Logging (≈1–1.5 hrs)

Instrument the system.

Track at minimum:

* Prompt tokens
* Completion tokens
* Total tokens per turn

Optional (recommended):

* Tokens per second
* Rolling averages per session

Why this matters:

* Cost awareness
* Latency intuition
* Prompt verbosity trade-offs

You should be able to answer:

> “Which part of my prompt is expensive?”

---

### Step 4 — Prompt Experiments (≈2–2.5 hrs)

Use the playground to *systematically test behavior*.

Suggested experiments:

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

* You can predict output changes *before* running the prompt
* You can justify why a response changed using:

  * Prompt structure
  * Temperature
  * System vs user roles
* Your CLI playground lets you test these hypotheses quickly

This intuition is foundational for:

* RAG grounding
* Tool calling
* Agent behavior control

Week 5 will assume you can *control* the model, not just talk to it.
