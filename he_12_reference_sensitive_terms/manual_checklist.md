# he_12_reference_sensitive_terms — Manual Checklist

## Цель
Проверка scoring-sensitive метрик: domain terms vs general phrases. Keyness/termhood зависят от reference corpus.

## Профиль
balanced

## Что проверять
1. "מהנדס מכונות" > "איש עבודה" по ranking
2. "תהליך יציקה" > "תהליך עבודה"
3. "מערכת ניטור רציפה" > "מערכת פשוטה"
4. "חומר רגיל" — absent

## Exact expectations
- "מהנדס מכונות" — present
- "תהליך יציקה" — freq ≥ 2
- "חומר רגיל" — ABSENT
- Sentence count: 12/10

## Relational expectations
- Domain > generic in ALL pairs
- Domain terms in top-3, generic in present_only

## Manual review
- Keyness — reference-dependent, no exact values
- Termhood — model-dependent, no exact values
- Weirdness — implementation-sensitive, no exact values
- EXPLANATION: exact values not claimed because metrics depend on external reference corpus

## Баг
- Domain term missing
- Generic term outranks domain term
- "חומר רגיל" present when it shouldn't be

## Stale gold
- Frequency differences ±1

## Особенности
- Keyness/termhood values intentionally left as manual_review
- This is CORRECT behavior — not a bug
