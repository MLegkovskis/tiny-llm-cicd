# create_tiny_model.py
import os
from transformers import GPT2Config, GPT2LMHeadModel, GPT2TokenizerFast

print("Creating a tiny GPT-2 style model + GPT-2 tokenizer...")

# Load a real GPT-2 tokenizer from Hugging Face
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

# We'll save it to /app/model in the container
MODEL_DIR = "/app/model"
os.makedirs(MODEL_DIR, exist_ok=True)
tokenizer.save_pretrained(MODEL_DIR)

# Create a minimal GPT-2 config (random weights)
config = GPT2Config(
    vocab_size=tokenizer.vocab_size,
    n_positions=256,
    n_ctx=256,
    n_embd=16,
    n_layer=1,
    n_head=1
)

model = GPT2LMHeadModel(config)
model.save_pretrained(MODEL_DIR)

print("Done! Model & tokenizer saved to /app/model.")
