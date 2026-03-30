# kadima/utils/hebrew.py
"""Hebrew-specific text utilities.

Helpers for RTL text, niqqud stripping, maqaf handling, etc.
"""

import re
import unicodedata


# Hebrew Unicode range: 0x0590–0x05FF, 0xFB1D–0xFB4F
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')

# Niqqud (vowel points): U+05B0–U+05BD, U+05BF, U+05C1–U+05C2, U+05C4–U+05C5, U+05C7
NIQQUD_PATTERN = re.compile(r'[\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]')

# Maqaf (Hebrew hyphen): U+05BE
MAQAF = '\u05BE'


def strip_niqqud(text: str) -> str:
    """Remove vowel points from Hebrew text."""
    return NIQQUD_PATTERN.sub('', text)


def is_hebrew(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    return bool(HEBREW_PATTERN.search(text))


def count_hebrew_words(text: str) -> int:
    """Count Hebrew words (split on spaces and maqaf)."""
    clean = strip_niqqud(text)
    words = re.split(rf'[\s{MAQAF}]+', clean)
    return len([w for w in words if w and is_hebrew(w)])


def normalize_maqaf(text: str) -> str:
    """Normalize hyphens to Hebrew maqaf."""
    return text.replace('-', MAQAF)
