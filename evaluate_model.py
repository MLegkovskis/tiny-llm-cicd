"""
evaluate_model.py

Evaluates a trained language model by calculating perplexity on a validation dataset.
Also runs a few predefined prompts to check if the output is reasonable.

Usage:
    python evaluate_model.py --model-dir ./model --data-file data/validation_data.txt
"""

import os
import argparse
import torch
import math
import json
from transformers import AutoModelForCausalLM, AutoTokenizer


def calculate_perplexity(model, tokenizer, validation_file, max_length=128):
    """
    Calculate perplexity on a validation dataset.
    Lower perplexity indicates better model performance.
    """
    model.eval()
    
    # Read validation data
    with open(validation_file, "r", encoding="utf-8") as f:
        validation_texts = f.read().strip().split("\n")
    
    if not validation_texts:
        print("Warning: Validation file is empty.")
        return float('inf')
    
    total_loss = 0.0
    total_tokens = 0
    
    with torch.no_grad():
        for text in validation_texts:
            # Tokenize input
            encodings = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
            input_ids = encodings.input_ids
            
            # Get model output with labels for loss calculation
            outputs = model(input_ids=input_ids, labels=input_ids)
            loss = outputs.loss
            
            # Add to running total
            total_loss += loss.item() * input_ids.size(1)
            total_tokens += input_ids.size(1)
    
    # Calculate perplexity
    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)
    
    print(f"Evaluation on {len(validation_texts)} samples:")
    print(f"Average Loss: {avg_loss:.4f}")
    print(f"Perplexity: {perplexity:.4f}")
    
    return perplexity


def generate_sample_responses(model, tokenizer, prompts, max_length=100):
    """
    Generate responses for a set of predefined prompts.
    """
    model.eval()
    results = []
    
    for prompt in prompts:
        # Encode the prompt
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        
        # Generate output
        output = model.generate(
            input_ids,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        # Decode the output
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Store result
        results.append({
            "prompt": prompt,
            "response": generated_text
        })
        
        print(f"\nPrompt: {prompt}")
        print(f"Response: {generated_text}")
    
    return results


def main(model_dir, validation_file, output_file=None, perplexity_threshold=1000.0):
    """
    Main evaluation function.
    
    Args:
        model_dir: Directory containing the model and tokenizer
        validation_file: File containing validation data
        output_file: Optional file to save evaluation results
        perplexity_threshold: Maximum acceptable perplexity value
    
    Returns:
        True if evaluation passes, False otherwise
    """
    print(f"Loading model and tokenizer from {model_dir}...")
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)
    
    # Sample prompts for generation
    sample_prompts = [
        "The future of renewable energy is",
        "Climate change mitigation requires",
        "The most efficient way to reduce carbon emissions is"
    ]
    
    # Calculate perplexity
    perplexity = calculate_perplexity(model, tokenizer, validation_file)
    
    # Generate sample responses
    print("\nGenerating sample responses...")
    samples = generate_sample_responses(model, tokenizer, sample_prompts)
    
    # Prepare evaluation results
    evaluation_results = {
        "perplexity": perplexity,
        "perplexity_threshold": perplexity_threshold,
        "sample_generations": samples,
        "evaluation_passed": perplexity <= perplexity_threshold
    }
    
    # Save results if output file is specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(evaluation_results, f, indent=2)
        print(f"Evaluation results saved to {output_file}")
    
    # Check if evaluation passes
    if perplexity <= perplexity_threshold:
        print(f"\nEvaluation PASSED: Perplexity {perplexity:.4f} <= {perplexity_threshold}")
        return True
    else:
        print(f"\nEvaluation FAILED: Perplexity {perplexity:.4f} > {perplexity_threshold}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a language model")
    parser.add_argument(
        "--model-dir",
        type=str,
        default="./model",
        help="Directory containing the model and tokenizer"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/validation_data.txt",
        help="File containing validation data"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="evaluation_results.json",
        help="File to save evaluation results"
    )
    parser.add_argument(
        "--perplexity-threshold",
        type=float,
        default=1000.0,
        help="Maximum acceptable perplexity value"
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    success = main(
        model_dir=args.model_dir,
        validation_file=args.data_file,
        output_file=args.output_file,
        perplexity_threshold=args.perplexity_threshold
    )
    
    # Exit with appropriate code
    exit(0 if success else 1)
