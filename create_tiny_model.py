import os
from transformers import GPT2Config, GPT2LMHeadModel, GPT2TokenizerFast

# 1) Load a real GPT-2 tokenizer from Hugging Face
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

# Save the tokenizer to local "model/" so we can load it offline
if not os.path.exists("model"):
    os.makedirs("model")
tokenizer.save_pretrained("model")

# 2) Create a minimal GPT-2 config
#    - Use tokenizer.vocab_size so model aligns with the actual GPT-2 vocab (~50257).
#    - Use small layer/heads for a "tiny" random model.
config = GPT2Config(
    vocab_size=tokenizer.vocab_size,  # typically 50257 for GPT2
    n_positions=256,  
    n_ctx=256,
    n_embd=16,  # extremely small embed dim
    n_layer=1,
    n_head=1
)

# 3) Create a random GPT-2 model with that config
model = GPT2LMHeadModel(config)

# 4) Save model weights into the same "model/" folder
model.save_pretrained("model")

print("Finished creating a tiny GPT-2–style model + real GPT2 tokenizer in `model/` folder.")
