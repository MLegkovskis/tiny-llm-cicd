import os
from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_FOLDER)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:filename>")
def frontend_static(filename):
    return send_from_directory(app.static_folder, filename)


# system_prompt is still loaded from /app/api/system_prompt.txt
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    system_prompt = f.read().strip()

# Path to the model inside container
MODEL_PATH = "/app/model"
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
            max_new_tokens=50,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=1.0,
            pad_token_id=tokenizer.eos_token_id
        )

    # Only decode newly generated tokens
    generated_ids = output[0][input_ids.shape[1]:]
    response_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    if "Bot:" in response_text:
        response_text = response_text.split("Bot:", 1)[-1].strip()

    return jsonify({"response": response_text})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring and liveness probes"""
    return jsonify({
        "status": "ok",
        "model": os.path.basename(MODEL_PATH),
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
