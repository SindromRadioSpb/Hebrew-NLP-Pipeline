# Методика: he_24 — Stopword filtering

## Процесс: Stopword Removal

### Вход
Массив токенов/лемм.

### Stopword list (еврейские)
Местоимения: הוא, היא, הם, הן.
Предлоги: של, על, ב, ל, את, בין, עם,כמו.
Союзы: ו, או, אבל, כי, אם.
Другие: כל, גם, רק,לא, יש.

### Правила
1. Stopwords исключаются из term candidates.
2. Content words (חוזק, חומר, פלדה) — сохраняются.
3. Влияние: corpus со stopwords даст меньше terms, чем corpus без stopwords.

### Acceptance criterion
- Stopwords NOT in term list: absent.
- Content words in term list: present_only.
- stopword_heavy file → fewer terms than content_heavy: comparison.
