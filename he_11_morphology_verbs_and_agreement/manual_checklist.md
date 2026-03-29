# he_11_morphology_verbs_and_agreement — Manual Checklist

## Цель
Проверка лемматизации глаголов и согласования род/число.

## Профиль
balanced

## Что проверять
1. Past verbs: כתב, עבד, בנה, פתר — correct lemma
2. Present participles: כותב/כותבת — same lemma?
3. Agreement: מערכת גדולה/מערכות גדולות — correct
4. Ambiguity: מנהל (noun/verb)

## Exact expectations
- Все past verbs present в verbs_past.txt
- Agreement pairs present в agreement_adj.txt
- Sentence count per file: 10

## Relational
- Lemma identity across forms
- Agreement correctness

## Manual review
- מנהל — noun vs verb ambiguity
- יסודי/יסודית — lemma identity
- כותב/כותבת — gendered participle lemma
- דו"ח — quote mark handling

## Баг
- Past verb missing
- Agreement pair missing

## Stale gold
- Lemma choice for ambiguous forms

## Особенности
- Morphological ambiguity documented in notes
- Exact values cautious for ambiguous forms
