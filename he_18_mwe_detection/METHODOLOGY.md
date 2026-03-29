# Методика: he_18 — Multi-word expressions

## Процесс: MWE Detection

### Вход
N-gram candidates.

### Типы MWE
1. **Technical MWE**: בדיקה לא הרסנית, חומר מרוכב מסיבי פחמן, טמפרטורת חדר, לחץ אטמוספירי.
   - Фиксированные технические термины.
2. **Idiomatic MWE**: ללכת חלק כמו משי, לשים את כל הביצים בסל אחד, לעלות על שרטון.
   - Фразеологизмы, значение ≠ сумма частей.

### Правила
1. MWE = последовательность токенов, функционирующих как единица.
2. Технические MWE — обязательно detect.
3. Идиомы — optional (зависит от домена).

### Acceptance criterion
- Technical MWE detected: present_only.
- Idioms: manual_review.
