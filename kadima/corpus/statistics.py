# kadima/corpus/statistics.py
"""M14: Token/lemma/freq statistics."""

import logging
from typing import Dict, Any, List
from collections import Counter

logger = logging.getLogger(__name__)


def compute_statistics(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Вычислить статистику по корпусу.

    Args:
        documents: [{"filename": str, "raw_text": str}, ...]

    Returns:
        Словарь со статистикой
    """
    total_chars = 0
    total_words = 0
    total_sentences = 0
    all_words = []

    for doc in documents:
        text = doc.get("raw_text", "")
        total_chars += len(text)

        # Sentence count (by period + newline)
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
        total_sentences += len(sentences)

        # Word count (by whitespace)
        words = text.split()
        total_words += len(words)
        all_words.extend(words)

    # Word frequency
    word_freq = Counter(all_words)
    unique_words = len(word_freq)
    hapax_count = sum(1 for _, c in word_freq.items() if c == 1)

    # Top 20
    top_words = word_freq.most_common(20)

    return {
        "document_count": len(documents),
        "total_characters": total_chars,
        "total_words": total_words,
        "total_sentences": total_sentences,
        "unique_words": unique_words,
        "hapax_count": hapax_count,
        "hapax_ratio": round(hapax_count / max(unique_words, 1), 4),
        "avg_words_per_doc": round(total_words / max(len(documents), 1), 1),
        "top_words": [{"word": w, "freq": c} for w, c in top_words],
    }
