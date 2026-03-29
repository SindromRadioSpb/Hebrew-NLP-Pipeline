# 2.3. Functional Specification — KADIMA v1.0

## Модуль M1: Sentence Splitter

### Вход
Текстовый файл (.txt, UTF-8).

### Выход
```json
{
  "sentences": [
    {"index": 0, "text": "...", "start": 0, "end": 45},
    {"index": 1, "text": "...", "start": 46, "end": 92}
  ],
  "count": 2
}
```

### Правила
1. Boundary: точка `.` после Hebrew буквы/цифры
2. Non-boundary: точка в аббревиатуре (פרופ׳, ד״ר)
3. Non-boundary: точка между цифрами (3.14)
4. Empty fragments: не считать предложениями

### Конфигурация
- `abbreviations`: list пользовательских аббревиатур (по умолчанию: פרופ׳, ד״ר, מר)

---

## Модуль M2: Tokenizer

### Вход
Строка текста.

### Выход
```json
{
  "tokens": [
    {"index": 0, "text": "פלדה", "start": 0, "end": 4},
    {"index": 1, "text": "חזקה.", "start": 5, "end": 10}
  ],
  "count": 2
}
```

### Правила
1. Split: пробел (U+0020)
2. Punctuation: часть токена (פלדה. = 1 токен)
3. Maqaf: compound = 1 токен (אל-חלד)
4. Double spaces: no empty tokens

---

## Модуль M3: Morphological Analyzer

### Вход
Токен.

### Выход
```json
{
  "surface": "הפלדה",
  "base": "פלדה",
  "lemma": "פלדה",
  "pos": "NOUN",
  "features": {"gender": "fem", "number": "sg", "definiteness": "def"},
  "is_det": true,
  "prefix_chain": []
}
```

### Правила
- DET detachment: ה prefix → remove if not part of root
- Prefix stripping: ב/ל/כ/מ/ו → separate
- Lemma: dictionary form (ед.ч.м.р. для noun/adj, inf для verb)

---

## Модуль M8: Term Extractor

### Вход
Corpus (массив документов).

### Выход
```json
{
  "terms": [
    {
      "surface": "חוזק מתיחה",
      "canonical": "חוזק מתיחה",
      "kind": "NOUN_NOUN",
      "freq": 8,
      "doc_freq": 4,
      "pmi": 4.2,
      "llr": 15.6,
      "dice": 0.85,
      "rank": 1,
      "profile": "balanced"
    }
  ],
  "profile": "balanced",
  "total_candidates": 45,
  "filtered": 32
}
```

### Профили
| Профиль | Min freq | Hapax | PMI threshold |
|---------|----------|-------|---------------|
| precise | 3 | excluded | high |
| balanced | 2 | excluded | medium |
| recall | 1 | included | low |

---

## Модуль M11: Validation Framework

### Вход
Gold corpus (expected_*.csv) + Pipeline output.

### Выход
```json
{
  "corpus_id": "he_01",
  "status": "PASS",
  "checks": [
    {"type": "sentence_count", "file": "doc_01", "expected": 5, "actual": 5, "result": "PASS"},
    {"type": "token_count", "file": "doc_01", "expected": 30, "actual": 30, "result": "PASS"},
    {"type": "lemma_freq", "lemma": "פלדה", "expected": 3, "actual": 3, "result": "PASS"}
  ],
  "summary": {"pass": 45, "warn": 2, "fail": 0},
  "acceptance": "PASS"
}
```

### Expectation types
- exact: точное совпадение
- approx: ± tolerance
- present_only: элемент есть
- absent: элемента нет
- higher_than: A > B
- manual_review: ручная проверка
