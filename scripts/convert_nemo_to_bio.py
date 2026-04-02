#!/usr/bin/env python
"""Convert NEMO-Corpus BMES format to BIO format for term extraction training.

NEMO format (BMES):
    S-ORG  — Single token entity
    B-ORG  — Begin of multi-token entity
    M-ORG  — Middle of multi-token entity
    E-ORG  — End of multi-token entity
    O      — Outside

BIO format (for token classification):
    B-TERM — Begin of term
    I-TERM — Inside/continuation of term
    O      — Outside

Usage:
    python scripts/convert_nemo_to_bio.py \
        --input data/nemo-corpus/data/ud/gold/morph_gold_train.bmes \
        --output data/term_training/nemo_train.conllu

    # Convert all splits
    python scripts/convert_nemo_to_bio.py --all
"""

import argparse
import os
from pathlib import Path
from typing import List, Tuple


def convert_bmes_to_bio(bmes_tag: str) -> str:
    """Convert BMES tag to BIO tag for term extraction.

    Args:
        bmes_tag: NEMO tag (S-ORG, B-ORG, M-ORG, E-ORG, O)

    Returns:
        BIO tag (B-TERM, I-TERM, O)
    """
    if bmes_tag == "O":
        return "O"

    # Handle compound tags like O^O (multiple analyses)
    if "^" in bmes_tag:
        # Take the first non-O analysis, or O if all are O
        parts = bmes_tag.split("^")
        for part in parts:
            if part != "O":
                return convert_bmes_to_bio(part)
        return "O"

    # S-XXX → B-TERM (single token entity)
    if bmes_tag.startswith("S-"):
        return "B-TERM"

    # B-XXX → B-TERM (begin of entity)
    if bmes_tag.startswith("B-"):
        return "B-TERM"

    # M-XXX → I-TERM (middle of entity)
    if bmes_tag.startswith("M-"):
        return "I-TERM"

    # E-XXX → I-TERM (end of entity)
    if bmes_tag.startswith("E-"):
        return "I-TERM"

    return "O"


def convert_file(input_path: str, output_path: str) -> Tuple[int, int, int]:
    """Convert a single NEMO BMES file to BIO format.

    Args:
        input_path: Path to NEMO .bmes file
        output_path: Path to output .conllu file

    Returns:
        (total_tokens, term_tokens, sentences)
    """
    total_tokens = 0
    term_tokens = 0
    sentences = 0

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            line = line.strip()

            # Empty line = sentence boundary
            if not line:
                outfile.write("\n")
                sentences += 1
                continue

            # Format: token TAG or token TAG^TAG^...
            parts = line.split()
            if len(parts) < 2:
                continue

            token = parts[0]
            bmes_tag = parts[1]

            bio_tag = convert_bmes_to_bio(bmes_tag)

            outfile.write(f"{token}\t{bio_tag}\n")
            total_tokens += 1
            if bio_tag != "O":
                term_tokens += 1

    return total_tokens, term_tokens, sentences


def convert_all_splits(nemo_dir: str, output_dir: str) -> None:
    """Convert all NEMO train/dev/test splits.

    Args:
        nemo_dir: Path to NEMO-Corpus/data/ud/gold
        output_dir: Path to output directory
    """
    splits = [
        ("morph_gold_train.bmes", "nemo_train.conllu"),
        ("morph_gold_dev.bmes", "nemo_dev.conllu"),
        ("morph_gold_test.bmes", "nemo_test.conllu"),
    ]

    os.makedirs(output_dir, exist_ok=True)

    for input_file, output_file in splits:
        input_path = os.path.join(nemo_dir, input_file)
        output_path = os.path.join(output_dir, output_file)

        if not os.path.exists(input_path):
            print(f"  Skipping {input_file} (not found)")
            continue

        total, terms, sents = convert_file(input_path, output_path)
        print(f"  {input_file} → {output_file}")
        print(f"    {total} tokens, {terms} term tokens ({terms/total*100:.1f}%), {sents} sentences")


def main():
    parser = argparse.ArgumentParser(description="Convert NEMO-Corpus BMES to BIO format")
    parser.add_argument("--input", help="Input .bmes file path")
    parser.add_argument("--output", help="Output .conllu file path")
    parser.add_argument("--all", action="store_true", help="Convert all splits (train/dev/test)")
    parser.add_argument("--nemo-dir", default="data/nemo-corpus/data/ud/gold",
                        help="Path to NEMO-Corpus gold data directory")
    parser.add_argument("--output-dir", default="data/term_training",
                        help="Output directory for converted files")

    args = parser.parse_args()

    if args.all:
        print("Converting all NEMO-Corpus splits...")
        convert_all_splits(args.nemo_dir, args.output_dir)
        print("Done!")
    elif args.input and args.output:
        print(f"Converting {args.input} → {args.output}")
        total, terms, sents = convert_file(args.input, args.output)
        print(f"Done! {total} tokens, {terms} term tokens ({terms/total*100:.1f}%), {sents} sentences")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()