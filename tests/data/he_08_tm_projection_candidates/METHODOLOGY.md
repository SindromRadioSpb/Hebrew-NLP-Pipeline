# Методика: he_08 — TM Projection Candidates

## Процесс: TM Candidate Surface Generation

### Вход
Извлечённые термины с поверхностными формами.

### Назначение
Подготовка candidates для последующей ручной проверки TM (Translation Memory) materialization.

### Правила
1. **Surface stability**: поверхностная форма термина должна быть детерминированной.
   - חוזק_מתיחה всегда = חוזק_מתיחה, не משנה контекст.
2. **Deduplication**: варианты одной формы → один candidate.
   - בדיקתאיכות / בדיקתהאיכות → один canonical.
3. **Normalized form**: candidate отображается в нормализованной форме.
   - без DET, без лишних пробелов, lowercase.
4. **Repeated terms**: если термин повторяется N раз — показать один candidate с freq=N.

### TM Materialization (описание, не реализация)
- TM entry создаётся ОТДЕЛЬНЫМ процессом после extraction.
- Extraction гарантирует только: stable surfaces, correct freq, deduplication.
- Не утверждается автоматическое создание TM rows.

### Acceptance criterion
- Surface stability: determinism check.
- Deduplication: correct grouping.
- freq accuracy: exact.
