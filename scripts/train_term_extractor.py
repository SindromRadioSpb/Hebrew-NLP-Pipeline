#!/usr/bin/env python
"""T7-3: Train AlephBERT Token Classification for term extraction.

Usage:
    # Export training data from KADIMA DB
    python scripts/train_term_extractor.py export --db ~/.kadima/kadima.db --output data/term_training

    # Train model
    python scripts/train_term_extractor.py train --data data/term_training --output models/term_extractor_v1

    # Evaluate
    python scripts/train_term_extractor.py eval --model models/term_extractor_v1 --data data/term_training

Training data format (CoNLL-U style):
    Each line: token \t label
    Empty line = sentence boundary
    Labels: B-TERM, I-TERM, O
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_training_data(db_path: str, output_dir: str, min_freq: int = 2) -> int:
    """Экспортировать термины из KADIMA DB в training формат.

    Источники данных:
    1. terms table — confirmed terms (positive examples)
    2. ngrams table — rejected terms (negative examples)
    3. annotation exports — human-reviewed terms

    Args:
        db_path: Path to kadima.db
        output_dir: Directory for training files
        min_freq: Minimum frequency for term inclusion

    Returns:
        Number of exported examples.
    """
    import sqlite3

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    examples = []

    # 1. Export confirmed terms (positive)
    try:
        cursor = conn.execute("""
            SELECT surface, canonical, kind, freq
            FROM terms
            WHERE freq >= ?
            ORDER BY freq DESC
        """, (min_freq,))

        for row in cursor:
            surface, canonical, kind, freq = row
            examples.append({
                "text": surface,
                "label": "TERM",
                "source": "confirmed_term",
                "freq": freq,
            })
        logger.info("Exported %d confirmed terms", len(examples))
    except sqlite3.OperationalError as e:
        logger.warning("Could not export terms: %s", e)

    # 2. Export n-grams as context (for O labels)
    try:
        cursor = conn.execute("""
            SELECT tokens, freq
            FROM ngrams
            WHERE freq < ?
            ORDER BY freq DESC
            LIMIT 1000
        """, (min_freq,))

        for row in cursor:
            tokens_str, freq = row
            if isinstance(tokens_str, str):
                tokens = tokens_str.split()
            else:
                tokens = []
            if tokens:
                examples.append({
                    "text": " ".join(tokens),
                    "label": "O",
                    "source": "low_freq_ngram",
                    "freq": freq,
                })
        logger.info("Exported %d negative examples", len([e for e in examples if e["label"] == "O"]))
    except sqlite3.OperationalError as e:
        logger.warning("Could not export ngrams: %s", e)

    conn.close()

    # Save as JSON (easier to work with than CoNLL-U for token classification)
    output_file = output_path / "training_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)

    # Also save CoNLL-U format for compatibility
    conllu_file = output_path / "training_data.conllu"
    with open(conllu_file, "w", encoding="utf-8") as f:
        for ex in examples:
            tokens = ex["text"].split()
            label = ex["label"]
            if label == "TERM":
                # B-TERM for first token, I-TERM for rest
                for i, tok in enumerate(tokens):
                    tag = "B-TERM" if i == 0 else "I-TERM"
                    f.write(f"{tok}\t{tag}\n")
            else:
                for tok in tokens:
                    f.write(f"{tok}\tO\n")
            f.write("\n")  # sentence boundary

    logger.info("Training data saved to %s (%d examples)", output_dir, len(examples))
    return len(examples)


def train_model(
    data_dir: str,
    output_dir: str,
    model_name: str = "onlplab/alephbert-base",
    num_epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 128,
):
    """Fine-tune AlephBERT for term extraction.

    Args:
        data_dir: Directory with training_data.json
        output_dir: Where to save the fine-tuned model
        model_name: Base model to fine-tune
        num_epochs: Training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        max_length: Max token length
    """
    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForTokenClassification,
            TrainingArguments,
            Trainer,
            DataCollatorForTokenClassification,
        )
        from datasets import Dataset
    except ImportError:
        print("Error: Required packages not installed.")
        print("pip install torch transformers datasets")
        sys.exit(1)

    # Load data — support both JSON and CoNLL-U formats
    data_path = Path(data_dir) / "training_data.json"
    conllu_path = Path(data_dir) / "nemo_train.conllu"

    examples = []

    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            examples = json.load(f)
    elif conllu_path.exists():
        # Parse CoNLL-U format (token\tlabel per line, empty line = sentence)
        current_tokens = []
        current_labels = []
        with open(conllu_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    if current_tokens:
                        examples.append({
                            "text": " ".join(current_tokens),
                            "label": "TERM" if "B-TERM" in current_labels else "O",
                            "source": "nemo_corpus",
                        })
                        current_tokens = []
                        current_labels = []
                else:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        current_tokens.append(parts[0])
                        current_labels.append(parts[1])
        # Don't forget last sentence
        if current_tokens:
            examples.append({
                "text": " ".join(current_tokens),
                "label": "TERM" if "B-TERM" in current_labels else "O",
                "source": "nemo_corpus",
            })
    else:
        print(f"Error: Training data not found in {data_dir}")
        print("Expected: training_data.json or nemo_train.conllu")
        sys.exit(1)

    if not examples:
        print("Error: No training examples found")
        sys.exit(1)

    print(f"Loaded {len(examples)} training examples")

    # Prepare tokenized dataset
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Label mapping
    label2id = {"O": 0, "B-TERM": 1, "I-TERM": 2}
    id2label = {v: k for k, v in label2id.items()}

    def tokenize_and_align_labels(example):
        tokens = example["text"].split()
        labels = []

        if example["label"] == "TERM":
            for i, _ in enumerate(tokens):
                labels.append(label2id["B-TERM"] if i == 0 else label2id["I-TERM"])
        else:
            labels = [label2id["O"]] * len(tokens)

        # Truncate
        if len(tokens) > max_length - 2:  # [CLS] ... [SEP]
            tokens = tokens[:max_length - 2]
            labels = labels[:max_length - 2]

        encoding = tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )

        # Align labels
        word_ids = encoding.word_ids()
        aligned_labels = [-100] * len(encoding["input_ids"])  # -100 = ignore
        for i, word_idx in enumerate(word_ids):
            if word_idx is not None and word_idx < len(labels):
                aligned_labels[i] = labels[word_idx]

        encoding["labels"] = aligned_labels
        return encoding

    # Create dataset
    dataset = Dataset.from_list(examples)
    tokenized_dataset = dataset.map(
        tokenize_and_align_labels,
        remove_columns=dataset.column_names,
    )

    # Split train/eval
    split = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split["train"]
    eval_dataset = split["test"]

    print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

    # Load model
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
    )

    # Training args
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        save_total_limit=3,
    )

    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer)

    # Compute metrics
    import numpy as np
    from seqeval.metrics import f1_score, precision_score, recall_score
    from seqeval.scheme import IOB2

    def compute_metrics(eval_preds):
        logits, labels = eval_preds
        predictions = np.argmax(logits, axis=-1)

        # Convert to label strings
        true_labels = [[id2label[l] for l in label if l != -100] for label in labels]
        pred_labels = [[id2label[p] for p, l in zip(pred, label) if l != -100] for pred, label in zip(predictions, labels)]

        return {
            "f1": f1_score(true_labels, pred_labels, scheme=IOB2),
            "precision": precision_score(true_labels, pred_labels, scheme=IOB2),
            "recall": recall_score(true_labels, pred_labels, scheme=IOB2),
        }

    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(f"Starting training for {num_epochs} epochs...")
    trainer.train()

    # Save
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save label mapping
    label_config = {
        "label2id": label2id,
        "id2label": id2label,
        "model_name": model_name,
        "num_epochs": num_epochs,
        "training_examples": len(examples),
    }
    with open(Path(output_dir) / "label_config.json", "w") as f:
        json.dump(label_config, f, indent=2)

    print(f"Model saved to {output_dir}")

    # Final evaluation
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")


def evaluate_model(model_dir: str, data_dir: str):
    """Evaluate fine-tuned model on test data."""
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForTokenClassification
    except ImportError:
        print("Error: Required packages not installed.")
        sys.exit(1)

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir)

    # Load test data
    data_path = Path(data_dir) / "training_data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    print(f"Evaluating on {len(examples)} examples...")

    correct = 0
    total = 0
    tp = fp = fn = 0

    for ex in examples:
        tokens = ex["text"].split()
        inputs = tokenizer(tokens, return_tensors="pt", is_split_into_words=True, truncation=True)

        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)[0]

        # Check predictions
        for i, pred_id in enumerate(predictions):
            if i >= len(tokens):
                break
            pred_label = model.config.id2label[int(pred_id)]
            expected = "B-TERM" if ex["label"] == "TERM" and i == 0 else "O"

            is_term_pred = pred_label in ("B-TERM", "I-TERM")
            is_term_expected = ex["label"] == "TERM"

            if is_term_pred == is_term_expected:
                correct += 1
            else:
                if is_term_pred and not is_term_expected:
                    fp += 1
                elif not is_term_pred and is_term_expected:
                    fn += 1
            total += 1

    accuracy = correct / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    print(f"Accuracy: {accuracy:.4f} ({correct}/{total})")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Train AlephBERT term extractor")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export training data from DB")
    export_parser.add_argument("--db", required=True, help="Path to kadima.db")
    export_parser.add_argument("--output", required=True, help="Output directory")
    export_parser.add_argument("--min-freq", type=int, default=2, help="Minimum term frequency")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train AlephBERT model")
    train_parser.add_argument("--data", required=True, help="Training data directory")
    train_parser.add_argument("--output", required=True, help="Model output directory")
    train_parser.add_argument("--model", default="onlplab/alephbert-base", help="Base model name")
    train_parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    train_parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    train_parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")

    # Eval command
    eval_parser = subparsers.add_parser("eval", help="Evaluate model")
    eval_parser.add_argument("--model", required=True, help="Model directory")
    eval_parser.add_argument("--data", required=True, help="Test data directory")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.command == "export":
        count = export_training_data(args.db, args.output, args.min_freq)
        print(f"Exported {count} examples to {args.output}")

    elif args.command == "train":
        train_model(
            data_dir=args.data,
            output_dir=args.output,
            model_name=args.model,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
        )

    elif args.command == "eval":
        evaluate_model(args.model, args.data)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()