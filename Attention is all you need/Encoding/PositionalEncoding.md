
# Positional Encoding — from intuition → design → math

## 1. The core problem

* Word embeddings encode **what** a word means.
* Self-attention lets every word look at every other word.
* **But attention has no built-in notion of order**.

Without positional information:

* "dog bites man" and "man bites dog" look almost identical.

So we must inject **order** into the model.

---

## 2. Why not just use position numbers?

If we assign:

* position 1 → `1`
* position 2 → `2`
* position 10 → `10`

Then:

* positions are unique ✅
* but distance is not geometrically meaningful ❌

The model cannot easily infer:

* which positions are close
* which are far

Raw numbers are labels, not structure.

---

## 3. High-level intuition of sinusoidal positional encoding

Instead of labels, we encode position as a **pattern**.

Think of each position as a **sound made of many tones**:

* fast-changing tones (high frequency)
* slow-changing tones (low frequency)

The *combination* of tones uniquely identifies a position.

* Nearby positions → similar sound
* Far positions → very different sound

---

## 4. Are we assigning parts of a curve to words?

**Yes — but not one curve.**

Each position is mapped to:

* a point on **many sine/cosine waves**
* each wave has a different frequency

So a word at position `pos` is represented by:

> its phase across multiple waves

A position is not "3" — it is a **multi-wave signature**.

---

## 5. Multiple frequencies = multiple distance scales

Each dimension pair uses a different wavelength:

* **High frequency (early dimensions)**
  → changes rapidly
  → captures *local order* (neighboring words)

* **Low frequency (later dimensions)**
  → changes slowly
  → captures *global position* (early vs late in sentence)

So one vector simultaneously knows:

* who is next to me
* roughly where I am overall

---

## 6. Fixed ordering of frequencies in the vector (important)

Yes — in the original Transformer this is **fixed by design**:

```
[ high freq | high freq | medium freq | medium freq | low freq | low freq ]
```

* Early dimensions → fast waves (local detail)
* Later dimensions → slow waves (global structure)

Because linear layers preserve dimension order, the model can learn:

* local grammar from early dimensions
* long-range structure from later dimensions

This ordering is intentional.

---

## 7. Mathematical definition

For each position `pos` and dimension index `i`:

```
PE(pos, 2i)   = sin(pos / 10000^(2i / d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i / d_model))
```

As `i` increases:

* denominator increases
* frequency decreases

---

## 8. Toy example: PE(3) (d_model = 6)

We have 3 sine–cosine pairs:

### Pair 1 — high frequency (local)

```
sin(3) ≈ 0.141
cos(3) ≈ -0.990
```

Changes quickly → sensitive to nearby positions.

### Pair 2 — medium frequency

```
sin(3/100) ≈ 0.030
cos(3/100) ≈ 0.999
```

Encodes mid-range distance.

### Pair 3 — low frequency (global)

```
sin(3/10000) ≈ 0.0003
cos(3/10000) ≈ 0.999999
```

Almost constant → encodes rough global position.

Final vector:

```
PE(3) ≈ [
  0.141, -0.990,   # local
  0.030,  0.999,   # medium
  0.0003, 0.999999 # global
]
```

---

## 9. Why periodicity is not a problem

High-frequency waves wrap around.

But ambiguity is resolved because:

* low-frequency waves disambiguate long-range position
* all frequencies are used together

Analogy:

> seconds + minutes + hours hand on a clock

One hand is ambiguous; all together are precise.

---

## 10. Combining word meaning + position

### Conceptually

* Word embedding → *what the word is*
* Positional encoding → *where it appears*

They are **added**, not concatenated.

### Mathematically

```
x_i = embedding_i + PE(pos_i)
```

This produces a **time-stamped meaning vector**.

---

## 11. How attention uses this information

Self-attention computes:

```
score(i, j) = Q_i · K_j
```

Where:

```
Q = W_Q x
K = W_K x
```

Since `x` contains sinusoidal position information:

* dot products vary smoothly with distance
* nearby positions → higher similarity
* far positions → lower similarity

No explicit distance computation is needed.

---

## 12. Why this works with linear layers

Key property:

* sine and cosine are **closed under linear combinations**

This allows linear layers to learn:

* previous token
* next token
* fixed relative offsets

Raw position IDs do not allow this.

---

## Final mental model (lock this in)

> **Sinusoidal positional encoding turns sequence order into a multi-scale geometry that self-attention can reason about using dot products alone.**
