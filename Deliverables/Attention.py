import numpy as np

np.set_printoptions(precision=3, suppress=True)

X = np.array([
    [1, 0, 1, 0], 
    [0, 2, 0, 2], 
    [1, 1, 1, 1]
])
print("Input Matrix X:")
print(X)

np.random.seed(42)
W_q = np.random.rand(4, 4)
W_k = np.random.rand(4, 4)
W_v = np.random.rand(4, 4)
print("\nWeight Matrix W_q:")
print(W_q)
print("\nWeight Matrix W_k:")
print(W_k)
print("\nWeight Matrix W_v:")
print(W_v)

Q = X @ W_q
K = X @ W_k
V = X @ W_v
print("\nQuery Matrix Q:")
print(Q)
print("\nKey Matrix K:")
print(K)
print("\nValue Matrix V:")
print(V)

d_k = Q.shape[-1]
scores = Q @ K.T
scaled_scores = scores / np.sqrt(d_k)
print("\nScaled Scores:")
print(scaled_scores)

def softmax(x):
    x_shifted = x - np.max(x, axis=-1, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


attention_weights = softmax(scaled_scores)
print("Attention Weights:\n", attention_weights)
print("Row sums:\n", attention_weights.sum(axis=-1))


output = attention_weights @ V
print("Attention Output:\n", output)