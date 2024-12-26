# api/app.py

import os
from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Configure Flask to serve static files from ../frontend
FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_FOLDER)

# Serve index.html at "/"
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# Serve any other static file in ../frontend/ if needed:
@app.route("/<path:filename>")
def frontend_static(filename):
    return send_from_directory(app.static_folder, filename)

# -------------------------
# LLM API below
# -------------------------

# Load system prompt
with open(os.path.join(os.path.dirname(__file__), "system_prompt.txt"), "r") as f:
    system_prompt = f.read().strip()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

@app.route("/generate", methods=["POST"])
def generate_text():
    data = request.json or {}
    user_input = data.get("prompt", "")

    combined_prompt = f"{system_prompt}\nUser: {user_input}\nBot:"

    input_ids = tokenizer.encode(combined_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_length=100,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    if "Bot:" in generated_text:
        response_text = generated_text.split("Bot:", 1)[-1].strip()
    else:
        response_text = generated_text

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
