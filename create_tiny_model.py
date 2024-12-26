# create_tiny_model.py

from transformers import GPT2Config, GPT2LMHeadModel
import os

# A super tiny config: 1 layer, 1 attention head, very small embedding dim
config = GPT2Config(
    vocab_size=100,    # must match your tokenizer.json
    n_positions=64,
    n_ctx=64,
    n_embd=16,
    n_layer=1,
    n_head=1
)

# Create the model with random weights
model = GPT2LMHeadModel(config)

# Ensure the model folder exists
if not os.path.exists("model"):
    os.makedirs("model")

# Save the model to "model/" folder
model.save_pretrained("model")

print("Created a tiny GPT-like model in `model/` folder!")
