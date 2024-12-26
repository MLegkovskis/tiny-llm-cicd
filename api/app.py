# api/app.py

import os
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# Load the system prompt from file
with open(os.path.join(os.path.dirname(__file__), "system_prompt.txt"), "r") as f:
    system_prompt = f.read().strip()

# Path to model folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model")

# Load a truly tiny GPT-like model from local folder
# This will produce mostly random or nonsense text, but it *is* a valid transformer architecture.
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

@app.route("/")
def home():
    return "Tiny LLM Chatbot Demo is up!"

@app.route("/generate", methods=["POST"])
def generate_text():
    data = request.json or {}
    user_input = data.get("prompt", "")

    # Combine system prompt + user input
    combined_prompt = f"{system_prompt}\nUser: {user_input}\nBot:"

    # Encode prompt
    input_ids = tokenizer.encode(combined_prompt, return_tensors="pt")

    # Generate up to 50 tokens
    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_length=100,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

    # Attempt to parse out the "Bot:" portion for a more direct reply
    # E.g. everything after "Bot:" if it exists
    if "Bot:" in generated_text:
        response_text = generated_text.split("Bot:", 1)[-1].strip()
    else:
        response_text = generated_text

    return jsonify({"response": response_text})

if __name__ == "__main__":
    # Run on port 8000 by default
    app.run(host="0.0.0.0", port=8000)
