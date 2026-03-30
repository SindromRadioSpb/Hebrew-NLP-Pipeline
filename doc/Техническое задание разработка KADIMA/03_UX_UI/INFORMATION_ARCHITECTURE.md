# 3.1. Information Architecture — KADIMA

## Главный экран (Dashboard)
- Corpus list (левая панель)
- Active corpus details (центр)
- Pipeline status (правая панель)
- Quick actions: New Run, Import, Export

## Разделы навигации
1. **Corpora** — управление корпусами (import, list, statistics)
2. **Pipeline** — настройка и запуск pipeline (M1–M8 config)
3. **Results** — результаты extraction (terms, n-grams, NP)
4. **Validation** — gold corpus, expected, review sheets
5. **Annotation** — POS/NER/NP annotation interface
6. **Export** — экспорт результатов (CSV, JSON, TBX, TMX)
7. **Settings** — pipeline config, profiles, thresholds

## Объектная модель UI
- Corpus → Documents → Sentences → Tokens → Lemmas
- Pipeline Run → Results → Terms/Ngrams/NP
- Validation Run → Expected → Actual → Review Sheet
- Annotation → Labels → Spans → Relations
