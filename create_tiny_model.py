"""
create_tiny_model.py

Downloads or fine-tunes a distilgpt2 model, optionally pushing/pulling
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
from torch.optim import AdamW
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_linear_schedule_with_warmup
)


class TextDataset(Dataset):
    """
    A dataset reading lines from a text file and tokenizing them.
    """

    def __init__(self, tokenizer, data_file, block_size=128):
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


def fine_tune_model(model, tokenizer, data_file, epochs=1, batch_size=4, learning_rate=5e-5):
    """
    Fine-tune the distilgpt2 model on a dataset.
    """
    # Ensure the tokenizer has a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataset = TextDataset(tokenizer, data_file, block_size=128)
    
    # Create DataLoader with dynamic padding
    def collate_fn(batch):
        # Pad sequences to the maximum length in the batch
        max_len = max([len(item) for item in batch])
        padded_batch = []
        for item in batch:
            padded = item.tolist() + [tokenizer.pad_token_id] * (max_len - len(item))
            padded_batch.append(torch.tensor(padded))
        return torch.stack(padded_batch)
    
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn
    )

    # Set up optimizer and learning rate scheduler
    optimizer = AdamW(model.parameters(), lr=learning_rate)
    total_steps = len(loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=0,
        num_training_steps=total_steps
    )

    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for step, batch in enumerate(loader):
            # Move batch to device (CPU in this case)
            inputs = batch
            
            # Forward pass
            outputs = model(input_ids=inputs, labels=inputs)
            loss = outputs.loss
            total_loss += loss.item()
            
            # Backward pass
            loss.backward()
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            if step % 10 == 0:
                print(f"Epoch {epoch+1}, step {step}, loss = {loss.item()}")
        
        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch+1} completed. Average loss: {avg_loss:.4f}")
    
    print("Fine-tuning complete.")


def main(
    train: bool = False,
    force_train: bool = False,
    gcs_path: str = "",
    data_file: str = "data/training_data.txt",
    model_dir: str = "/app/model",
):
    """
    Entry point for downloading or fine-tuning a distilgpt2 model.

    :param train: Whether to attempt fine-tuning if no model found on GCS.
    :param force_train: If True, always fine-tune even if GCS model is available.
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

    # If no model found or training is forced => download distilgpt2
    print("No existing GCS model (or training forced). Downloading distilgpt2...")

    # Download the pre-trained model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    model = AutoModelForCausalLM.from_pretrained("distilgpt2")
    
    # Save the tokenizer first
    tokenizer.save_pretrained(model_dir)
    
    # Fine-tune if requested
    if train or force_train:
        print("Fine-tuning distilgpt2 on your data...")
        fine_tune_model(model, tokenizer, data_file, epochs=1, batch_size=4)

    # Save the model
    model.save_pretrained(model_dir)
    print(f"Model + tokenizer saved to {model_dir}")

    # Upload back to GCS if we have a path
    if gcs_path:
        upload_model_to_gcs(model_dir, gcs_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train", action="store_true",
        help="Enable fine-tuning step."
    )
    parser.add_argument(
        "--force-train", action="store_true",
        help="Always fine-tune even if a model exists on GCS."
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
