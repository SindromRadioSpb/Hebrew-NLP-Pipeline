# he_08_tm_projection_candidates — Manual Checklist

## Цель корпуса
Подготовка поверхностей для ручной проверки TM: стабильные surfaces, дедупликация, normalized forms.

## Рекомендуемый профиль
balanced

## Что проверять первым
1. "תהליך זיקוק" — stable surface across both files
2. "מגדל זיקוק" — cross-document consistency
3. "זיקוק אטמוספרי" vs "זיקוק תת־וואקום" — dedup candidates
4. "המוצר הסופי" — normalized form consistency

## Exact expectations
- "תהליך זикוק" — freq ≥ 3, doc_freq = 2
- "מגדל זיקוק" — freq ≥ 3, doc_freq = 2
- "תהליך פיצוח" — freq ≥ 2, doc_freq = 2

## Relational expectations
- TM candidates > generic words
- Cross-document surfaces consistent

## Manual review items
- Surface stability for TM projection
- Deduplication: similar but distinct surfaces
- Normalized forms: consistent spelling
- ВАЖНО: не утверждать автоматическое создание TM rows

## Что считать багом
- "תהליך זיקוק" не проиндексирован
- Surface inconsistency между файлами

## Что считать stale gold
- Frequency differences ±1

## Что считать допустимой особенностью
- Different ranking for rare TM candidates
- Morphological variants treated differently
