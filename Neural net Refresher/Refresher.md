# Neural Networks from Scratch — A Beginner-First Walkthrough

> **How to read this document**
>
> - If you are **completely new**, read from top to bottom — every step explains _what we do_ **and why we do it**.
> - If you already know neural networks and want a **quick refresher**, jump directly to **Part 2: Full Numerical Walkthrough**.

This document is designed to be:

- **Gentle and intuitive first** 🧠
- **Mathematically exact at the end** 📐
- **Structured the same way real neural networks work**

---

## 1. Why Do We Even Need Neural Networks?

Before terminology, let’s answer the most important beginner question:

> **Why can’t we just write rules?**

For simple problems, we _can_ write rules.

But for problems like:

- recognizing images
- understanding language
- predicting complex patterns

…there are **too many rules to write by hand**.

So instead, we build a system that:

> **Learns the rules by itself from examples**.

A neural network is exactly that system.

---

## 2. What Is a Neural Network? (Very Plain English)

A neural network is a **machine that learns by adjusting numbers**.

You can think of it as:

> "A chain of small calculators whose knobs slowly turn until the answers improve."

Each time the network is wrong, it:

1. Measures _how wrong_
2. Figures out _which knobs caused the mistake_
3. Adjusts them slightly

Doing this repeatedly is called **training**.

---

## 3. Core Terminologies (What + Why)

### Neuron

**What it is:**
A neuron is a tiny calculator.

**What it does:**
It combines inputs, applies importance, and produces an output.

**Why it exists:**
One neuron can learn a _simple pattern_. Many neurons together can learn _complex patterns_.

---

### Weight

**What it is:**
A weight is a number multiplied with an input.

**Why we need it:**
Not all inputs matter equally. Weights let the network decide _what matters more_.

---

### Bias

**What it is:**
A constant number added at the end.

**Why we need it:**
It allows the neuron to shift its decision even when inputs are zero. Without bias, learning is severely limited.

---

### Layer

**What it is:**
A collection of neurons operating at the same stage.

**Why layers matter:**

- Early layers learn **simple patterns**
- Deeper layers combine them into **complex ideas**

---

### Activation Function

**What it is:**
A function applied after combining inputs.

**Why we need it:**
Without activation functions, the network would behave like a single linear equation — no matter how deep it is.

Activation functions introduce **non-linearity**, which enables learning complex relationships.

---

### Loss Function

**What it is:**
A function that measures error.

**Why we need it:**
The network has no idea what “good” or “bad” means unless we define it mathematically.

Loss is the **signal that drives learning**.

---

### Backpropagation

**What it is:**
A method to send error information backward.

**Why we need it:**
We must know **which weights caused the error** and **how much** they contributed.

Backpropagation provides this blame assignment.

---

### Learning Rate

**What it is:**
A small number controlling update size.

**Why we need it:**
Learning too fast breaks learning. Learning too slow wastes time.

---

## 4. Our Tiny Neural Network (What We’re Building and Why)

We intentionally choose a **very small network** so every calculation fits on one page.

### Architecture

- 2 input values
- 1 hidden layer with 2 neurons
- 1 output neuron

**Why this setup?**
It is the smallest network that can show _all core ideas_: layers, activations, loss, and backpropagation.

---

## 5. Problem Setup

### Input

```
x = [1, 0]
```

### Target (Correct Answer)

```
y = 1
```

**Why a target?**
Learning is impossible without feedback. The target is the feedback signal.

---

## 6. Forward Pass — Making a Prediction

**Why this step exists:**
Before fixing mistakes, the network must _try_.

This attempt is called the **forward pass**.

---

### 6.1 Hidden Layer Computation

Each hidden neuron:

1. Multiplies inputs by weights
2. Adds bias
3. Applies activation

We use **ReLU**:

```
ReLU(z) = max(0, z)
```

**Why ReLU?**
It is simple, fast, and helps learning stay stable.

---

### 6.2 Output Layer

We use **Sigmoid**:

```
Sigmoid(z) = 1 / (1 + e^-z)
```

**Why Sigmoid?**
It converts output into a probability-like value between 0 and 1.

---

## 7. Loss — Measuring Mistake

We use **Mean Squared Error**:

```
Loss = (prediction − target)²
```

**Why loss comes after prediction:**
The network cannot improve unless it knows _how wrong it was_.

---

## 8. Backpropagation — Learning From the Mistake

**Why this step exists:**
Loss alone does not tell us _how to fix_ the network.

Backpropagation answers:

> “Which weight should change, and by how much?”

It uses calculus (derivatives) to compute this efficiently.

---

## 9. Weight Update — Actually Learning

Each weight update follows:

```
new_weight = old_weight − learning_rate × gradient
```

**Why subtraction?**
Gradients point toward increasing error. We move in the opposite direction.

---

# PART 2 — FULL NUMERICAL WALKTHROUGH (REFRESHER MODE)

This section is **pure mechanics**. No stories. No intuition.

---

## 10. Parameters

Inputs:

```
x = [1, 0]
y = 1
```

Hidden layer:

```
w1=0.1  w2=0.2  b1=0
w3=0.3  w4=0.4  b2=0
```

Output layer:

```
w5=0.5  w6=0.6  b3=0
```

Learning rate:

```
η = 0.1
```

---

## 11. Forward Pass

Hidden neuron 1:

```
z1 = 1×0.1 + 0×0.2 = 0.1
a1 = ReLU(0.1) = 0.1
```

Hidden neuron 2:

```
z2 = 1×0.3 + 0×0.4 = 0.3
a2 = ReLU(0.3) = 0.3
```

Output:

```
z3 = 0.1×0.5 + 0.3×0.6 = 0.23
ŷ = sigmoid(0.23) ≈ 0.557
```

---

## 12. Loss

```
L = (0.557 − 1)² ≈ 0.196
```

---

## 13. Backpropagation

```
∂L/∂ŷ = 2(ŷ − y) = −0.886
σ'(z3) ≈ 0.247
δ_out = −0.219
```

Output weights:

```
∂L/∂w5 = −0.0219
∂L/∂w6 = −0.0657
```

Updated:

```
w5=0.5022  w6=0.6066
```

Hidden layer:

```
δ_h1 = −0.1095
δ_h2 = −0.1314
```

Updated:

```
w1=0.1109  w3=0.3131
```

---

## 14. Final Mental Model

> Neural networks are not magic.
> They are **organized math + feedback + repetition**.

If you understand this document, you understand the foundation of _all_ modern deep learning.
