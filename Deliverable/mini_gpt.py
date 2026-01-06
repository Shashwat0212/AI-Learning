import torch
import torch.nn as nn
import math

# ==========================================================
# STEP 0: CONFIGURATION OBJECT
# ==========================================================
# This class only stores hyperparameters.
# Think of it like a struct that defines the *shape* of the model.
class GPTConfig:
    vocab_size = 1000      # Total number of unique tokens
    block_size = 16        # Maximum sequence length (context window)
    embedding_dim = 64     # Size of token embeddings (a.k.a. model width)
    num_heads = 4          # Number of attention heads


# ==========================================================
# STEP 1: TOKEN + POSITION EMBEDDINGS
# ==========================================================
class EmbeddingStem(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()

        # Converts token IDs -> dense vectors
        self.token_embedding = nn.Embedding(
            num_embeddings=config.vocab_size,
            embedding_dim=config.embedding_dim
        )

        # Converts position indices -> dense vectors
        self.position_embedding = nn.Embedding(
            num_embeddings=config.block_size,
            embedding_dim=config.embedding_dim
        )

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        token_ids shape: (batch_size, sequence_length)

        Example input:
        token_ids = [[5, 17, 23, 9]]
        """

        # ------------------------------------------
        # STEP 1.1: Read input shape
        # ------------------------------------------
        batch_size, seq_len = token_ids.shape
        # Example: (2, 8)

        # ------------------------------------------
        # STEP 1.2: Token embeddings
        # ------------------------------------------
        token_vectors = self.token_embedding(token_ids)
        # Shape changes:
        # (B, T) -> (B, T, C)
        # Example:
        # [[5,17]] -> [[[0.12, -0.44, ...], [...]]]

        # WHY?
        # Neural networks operate on continuous vectors, not integers.

        # ------------------------------------------
        # STEP 1.3: Position indices
        # ------------------------------------------
        positions = torch.arange(seq_len, device=token_ids.device)
        # Shape: (T,)
        # Example: [0, 1, 2, 3]

        # ------------------------------------------
        # STEP 1.4: Position embeddings
        # ------------------------------------------
        position_vectors = self.position_embedding(positions)
        # Shape: (T, C)

        # Add batch dimension
        position_vectors = position_vectors.unsqueeze(0)
        # Shape: (1, T, C)

        # ------------------------------------------
        # STEP 1.5: Combine token + position info
        # ------------------------------------------
        combined_embeddings = token_vectors + position_vectors
        # Shape: (B, T, C)

        # WHY?
        # Transformers have no inherent notion of order.
        # Position embeddings inject word order information.

        return combined_embeddings


# ==========================================================
# STEP 2: CAUSAL SELF-ATTENTION
# ==========================================================
class CausalSelfAttention(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()

        assert config.embedding_dim % config.num_heads == 0

        self.num_heads = config.num_heads
        self.head_dim = config.embedding_dim // config.num_heads

        # Single projection for Query, Key, Value
        self.qkv_projection = nn.Linear(
            config.embedding_dim,
            3 * config.embedding_dim
        )

        # Output projection
        self.output_projection = nn.Linear(
            config.embedding_dim,
            config.embedding_dim
        )

        # Lower-triangular mask for causal attention
        self.register_buffer(
            "causal_mask",
            torch.tril(torch.ones(config.block_size, config.block_size))
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: (B, T, C)
        """
        batch_size, seq_len, embed_dim = x.shape

        # ------------------------------------------
        # STEP 2.1: Compute Q, K, V
        # ------------------------------------------
        qkv = self.qkv_projection(x)
        # Shape: (B, T, 3C)

        queries, keys, values = qkv.chunk(3, dim=-1)
        # Each: (B, T, C)

        # WHY?
        # Q = what am I looking for?
        # K = what do I contain?
        # V = what information do I pass?

        # ------------------------------------------
        # STEP 2.2: Split into heads
        # ------------------------------------------
        queries = queries.view(batch_size, seq_len, self.num_heads, self.head_dim)
        keys = keys.view(batch_size, seq_len, self.num_heads, self.head_dim)
        values = values.view(batch_size, seq_len, self.num_heads, self.head_dim)

        # Transpose for attention math
        queries = queries.transpose(1, 2)
        keys = keys.transpose(1, 2)
        values = values.transpose(1, 2)
        # Shape: (B, H, T, D)

        # ------------------------------------------
        # STEP 2.3: Attention scores
        # ------------------------------------------
        attention_scores = (queries @ keys.transpose(-2, -1))
        attention_scores /= math.sqrt(self.head_dim)
        # Shape: (B, H, T, T)

        # WHY scaling?
        # Prevents softmax saturation for large dimensions.

        # ------------------------------------------
        # STEP 2.4: Apply causal mask
        # ------------------------------------------
        attention_scores = attention_scores.masked_fill(
            self.causal_mask[:seq_len, :seq_len] == 0,
            float("-inf")
        )

        # WHY?
        # Prevents looking at future tokens during training.

        # ------------------------------------------
        # STEP 2.5: Softmax -> probabilities
        # ------------------------------------------
        attention_weights = torch.softmax(attention_scores, dim=-1)

        # ------------------------------------------
        # STEP 2.6: Weighted sum of values
        # ------------------------------------------
        attended_values = attention_weights @ values
        # Shape: (B, H, T, D)

        # ------------------------------------------
        # STEP 2.7: Merge heads
        # ------------------------------------------
        attended_values = attended_values.transpose(1, 2).contiguous()
        attended_values = attended_values.view(batch_size, seq_len, embed_dim)

        # Final linear projection
        return self.output_projection(attended_values)


# ==========================================================
# STEP 3: FEED-FORWARD NETWORK (MLP)
# ==========================================================
class FeedForward(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()

        self.expand = nn.Linear(config.embedding_dim, 4 * config.embedding_dim)
        self.activation = nn.GELU()
        self.contract = nn.Linear(4 * config.embedding_dim, config.embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # (B, T, C) -> (B, T, 4C) -> (B, T, C)
        return self.contract(self.activation(self.expand(x)))


# ==========================================================
# STEP 4: TRANSFORMER BLOCK
# ==========================================================
class TransformerBlock(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()

        self.layer_norm_1 = nn.LayerNorm(config.embedding_dim)
        self.attention = CausalSelfAttention(config)

        self.layer_norm_2 = nn.LayerNorm(config.embedding_dim)
        self.feed_forward = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # ------------------------------------------
        # STEP 4.1: Attention with residual
        # ------------------------------------------
        x = x + self.attention(self.layer_norm_1(x))

        # WHY residuals?
        # Helps gradient flow and stabilizes deep training.

        # ------------------------------------------
        # STEP 4.2: MLP with residual
        # ------------------------------------------
        x = x + self.feed_forward(self.layer_norm_2(x))

        return x


# ==========================================================
# STEP 5: MINI GPT MODEL
# ==========================================================
class MiniGPT(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()

        self.embedding = EmbeddingStem(config)
        self.transformer = TransformerBlock(config)
        self.final_norm = nn.LayerNorm(config.embedding_dim)

        # Maps embeddings -> vocabulary logits
        self.language_model_head = nn.Linear(
            config.embedding_dim,
            config.vocab_size,
            bias=False
        )

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        # ------------------------------------------
        # STEP 5.1: Embed tokens
        # ------------------------------------------
        x = self.embedding(token_ids)
        # Shape: (B, T, C)

        # ------------------------------------------
        # STEP 5.2: Transformer block
        # ------------------------------------------
        x = self.transformer(x)

        # ------------------------------------------
        # STEP 5.3: Final normalization
        # ------------------------------------------
        x = self.final_norm(x)

        # ------------------------------------------
        # STEP 5.4: Vocabulary projection
        # ------------------------------------------
        logits = self.language_model_head(x)
        # Shape: (B, T, vocab_size)

        return logits


# ==========================================================
# STEP 6: EXAMPLE RUN
# ==========================================================
if __name__ == "__main__":
    torch.manual_seed(42)

    config = GPTConfig()
    model = MiniGPT(config)

    # Example input: batch of 2 sequences, length 8
    input_tokens = torch.randint(0, config.vocab_size, (2, 8))

    output_logits = model(input_tokens)

    print("Input shape:", input_tokens.shape)
    print("Output logits shape:", output_logits.shape)
