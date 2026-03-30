# Методика: he_09 — Смешанный домен

## Процесс: Domain Discrimination

### Вход
Корпус с текстами из разных доменов: инженерный (domain_steel), общий (domain_general), шум (domain_noise).

### Правила
1. **Domain terms** (domain_steel): тмператуורתהתכה, תהליךייצור — должны выделяться как strong terms.
2. **General words** (domain_general): מחקר, תוצאות, מסקנות — не должны доминировать в term list.
3. **Noise in domain** (domain_noise): таблицы, данные — должны быть отфильтрованы или ослаблены.

### Принцип
Term extraction должен предпочитать domain-specific expressions общим словам.
Frequency alone ≠ termhood. המחשבבדק (research checked) — high freq, low termhood.

### Acceptance criterion
- Strong domain terms present: present_only.
- General words weaker than domain terms: lower_than.
- Domain discrimination works across files.
