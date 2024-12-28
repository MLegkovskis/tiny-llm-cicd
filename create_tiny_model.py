"""
create_tiny_model.py

Generates or trains a minimal GPT-2 model, optionally pushing/pulling
from a GCS bucket to skip re-training in future runs.

Usage examples:

    # Train locally, write model to ./model
    python create_tiny_model.py --train --force-train \
        --data-file data/training_data.txt --model-dir ./model

    # In Docker, default to /app/model
    python create_tiny_model.py --train --force-train \
        --data-file data/training_data.txt
"""

import os
import argparse
import subprocess
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from transformers import (
    GPT2Config,
    GPT2LMHeadModel,
    GPT2TokenizerFast,
    AdamW
)


class TinyTextDataset(Dataset):
    """
    A minimal dataset reading lines from a text file and tokenizing them.
    """

    def __init__(self, tokenizer, data_file, block_size=64):
        self.examples = []
        with open(data_file, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n")

        for line in lines:
            tokenized = tokenizer.encode(
                line, truncation=True, max_length=block_size
            )
            self.examples.append(tokenized)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        # Return a 1D tensor for a single sequence
        return torch.tensor(self.examples[idx], dtype=torch.long)


def collate_fn(batch, pad_token_id):
    """
    Collate function to handle variable-length sequences by padding.
    """
    # batch is a list of tensors, each shape [seq_len]
    # We pad them to the max length in the batch.
    return pad_sequence(batch, batch_first=True, padding_value=pad_token_id)


def download_model_from_gcs(bucket_path, local_model_dir):
    """
    Download model artifacts from GCS if they exist.
    Example: gsutil -m cp -r gs://my-bucket/tiny-llm-model /app/model
    """
    print(f"Attempting to download model from {bucket_path} ...")
    try:
        subprocess.check_call(
            ["gsutil", "-m", "cp", "-r", bucket_path, local_model_dir]
        )
        print("Model downloaded from GCS successfully.")
        return True
    except subprocess.CalledProcessError:
        print("No existing model found in GCS (or download failed).")
        return False


def upload_model_to_gcs(local_model_dir, bucket_path):
    """
    Upload model artifacts to GCS for reuse.
    Example: gsutil -m cp -r /app/model gs://my-bucket/tiny-llm-model
    """
    print(f"Uploading model to {bucket_path} ...")
    subprocess.check_call(
        ["gsutil", "-m", "cp", "-r", local_model_dir, bucket_path]
    )
    print("Model uploaded to GCS successfully.")


def train_tiny_model(model, tokenizer, data_file, epochs=2, batch_size=2):
    """
    Train the model on a tiny dataset with dynamic padding.
    """
    # Ensure the tokenizer has a pad token
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    dataset = TinyTextDataset(tokenizer, data_file, block_size=64)

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_fn(b, tokenizer.pad_token_id)
    )

    model.train()
    optimizer = AdamW(model.parameters(), lr=1e-3)

    for epoch in range(epochs):
        for step, batch in enumerate(loader):
            # batch has shape [B, T] due to our collate_fn
            outputs = model(input_ids=batch, labels=batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            if step % 10 == 0:
                print(f"Epoch {epoch+1}, step {step}, loss = {loss.item()}")
    print("Training complete.")


def main(
    train: bool = False,
    force_train: bool = False,
    gcs_path: str = "",
    data_file: str = "data/training_data.txt",
    model_dir: str = "/app/model",
):
    """
    Entry point for creating or training a tiny GPT-2 model.

    :param train: Whether to attempt training if no model found on GCS.
    :param force_train: If True, always train even if GCS model is available.
    :param gcs_path: GCS path to pull/push model. e.g. gs://my-bucket/tiny-llm-model
    :param data_file: Path to training text file.
    :param model_dir: Where to store/load the model (default /app/model for Docker).
                     Locally you might use ./model instead to avoid permission issues.
    """
    print("Starting create_tiny_model.py ...")
    print(f"Model directory: {model_dir}")

    os.makedirs(model_dir, exist_ok=True)

    # If we have a GCS path and we're not forcing training, try to reuse a model
    if gcs_path and not force_train:
        success = download_model_from_gcs(gcs_path, model_dir)
        if success:
            print("Using existing model from GCS. Skipping training.")
            return

    # If no model found or training is forced => create from scratch
    print("No existing GCS model (or training forced). Creating GPT-2 config.")

    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    tokenizer.save_pretrained(model_dir)

    config = GPT2Config(
        vocab_size=tokenizer.vocab_size,
        n_positions=256,
        n_ctx=256,
        n_embd=16,
        n_layer=1,
        n_head=1
    )
    model = GPT2LMHeadModel(config)

    if train or force_train:
        print("Training a tiny GPT-2 model on your data ...")
        train_tiny_model(model, tokenizer, data_file, epochs=2, batch_size=2)

    model.save_pretrained(model_dir)
    print(f"Model + tokenizer saved to {model_dir}")

    # Upload back to GCS if we have a path
    if gcs_path:
        upload_model_to_gcs(model_dir, gcs_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train", action="store_true",
        help="Enable tiny training step."
    )
    parser.add_argument(
        "--force-train", action="store_true",
        help="Always train even if a model exists on GCS."
    )
    parser.add_argument(
        "--gcs-path", type=str, default="",
        help="GCS path to pull/push model. e.g. gs://my-bucket/tiny-llm-model"
    )
    parser.add_argument(
        "--data-file", type=str, default="data/training_data.txt",
        help="Path to the training text file."
    )
    parser.add_argument(
        "--model-dir", type=str, default="/app/model",
        help="Where to store/load the model. Use a local path if not in Docker."
    )
    args = parser.parse_args()

    main(
        train=args.train,
        force_train=args.force_train,
        gcs_path=args.gcs_path,
        data_file=args.data_file,
        model_dir=args.model_dir
    )
