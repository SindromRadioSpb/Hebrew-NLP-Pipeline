# 4.7. Semantic Annotation & Knowledge Management — Gap Analysis

> Дата: 2026-03-30 | Статус: analysis
> Связанные: 04_Система/LABEL_STUDIO_INTEGRATION.md, 04_Система/NLP_STACK_INTEGRATION.md, 02_Продукт/PRD.md

---

## 1. Вопрос

Есть ли в KADIMA запланированная функциональность:
- Интеллектуальная помощь при аннотации (recommender system)
- Управление знаниями / knowledge bases (entity linking, ontologies)
- Active learning (модель учится на ходу от коррекций аннотатора)?

**Короткий ответ: нет. Это белое пятно.**

---

## 2. Что у нас уже есть

| Функция | Модуль | Инструмент | Что делает |
|---------|--------|-----------|------------|
| Аннотация UI | M15 | Label Studio | Разметка текста, NER, classification |
| Pre-annotation | M15 + ML backend | KADIMA pipeline | Предсказания перед аннотацией |
| Validation | M11 | KADIMA | PASS/WARN/FAIL отчёты |
| Corpus management | M14 | KADIMA | Import/export, statistics |
| NER (pre-trained) | M9 | NeoDictaBERT | Распознавание сущностей |

**Чего НЕТ:**
- ❌ Recommender system (умные подсказки, не просто pre-annotations)
- ❌ Knowledge base / entity linking
- ❌ Active learning (автоматический выбор что аннотировать)
- ❌ Relation extraction annotation
- ❌ Coreference annotation
- ❌ Multi-layer annotation (NER + relations + coref в одном документе)

---

## 3. INCEpTION — аудит

### 3.1 Что INCEpTION даёт

| Фича | INCEpTION | Label Studio | KADIMA v1.0 |
|------|-----------|-------------|-------------|
| NER annotation | ✅ | ✅ | ✅ |
| Relation annotation | ✅ (нативно) | ⚠️ (limited) | ❌ |
| Coreference annotation | ✅ (нативно) | ❌ | ❌ |
| **Recommender system** | ✅ (ML suggestions) | ⚠️ (pre-annotations only) | ⚠️ |
| **Knowledge base linking** | ✅ (Wikidata, SPARQL) | ❌ | ❌ |
| **Active learning** | ✅ (Enterprise-like) | Enterprise only | ❌ |
| Multi-layer annotation | ✅ (все слои в одном doc) | ⚠️ (per-project) | ❌ |
| Ontology management | ✅ | ❌ | ❌ |
| UIMA/WebAnno format | ✅ | ❌ | ❌ |
| REST API | ✅ | ✅ | ✅ |
| Docker | ✅ | ✅ | ✅ |
| Лицензия | Apache 2.0 | Apache 2.0 | — |
| Язык | Java (Spring) | Python (Django) | Python |
| Сложность установки | Высокая (Java, WAR) | Средняя (pip/docker) | — |

### 3.2 Ключевое отличие INCEpTION

```
Label Studio:   Аннотатор видит текст → сам размечает → сохраняет
                (или видит pre-annotation → исправляет)

INCEpTION:      Аннотатор видит текст → система ПРЕДЛАГАЕТ аннотации
                → аннотатор подтверждает/отклоняет/редактирует
                → система УЧИТСЯ на коррекциях → предлагает лучше
```

**Recommender** = не «вот вам предсказание», а «вот вам 3 варианта, выберите лучший или исправьте». Это interactive, а не static.

### 3.3 Лицензия

Apache 2.0 — ✅ совместим с некоммерческим проектом. Полностью open-source.

---

## 4. Gap Analysis: что INCEpTION умеет, а мы не предусмотрели

### 4.1 Функциональные пробелы

| Проблема | Уровень критичности | KADIMA сейчас | INCEpTION | Решение |
|----------|---------------------|---------------|-----------|---------|
| **Recommender system** | 🔴 Высокий | ❌ | ✅ | См. §5 |
| **Relation extraction annotation** | 🟡 Средний | ❌ | ✅ | LS template v1.x |
| **Coreference annotation** | 🟡 Средний | ❌ (HebPipe beta) | ✅ | v2.0 |
| **Knowledge base linking** | 🟡 Средний | ❌ | ✅ | См. §5 |
| **Active learning** | 🟠 Низкий-средний | ❌ | ✅ | v2.0 (Dicta-LM) |
| **Ontology management** | 🟠 Низкий | ❌ | ✅ | Не нужно для v1.0 |

### 4.2 Почему INCEpTION не подходит как замена Label Studio

| Критерий | INCEpTION | Label Studio | Вывод |
|----------|-----------|-------------|-------|
| Multi-modal (audio, image, video) | ❌ только текст | ✅ все модальности | LS лучше для масштабирования |
| Hebrew RTL support | ⚠️ ограниченный | ✅ через CSS | LS лучше |
| Стек | Java + Spring + WAR | Python + Django | LS совместим с нашим стеком |
| ML backend integration | Свой recommender API | Open ML backend SDK | LS гибче |
| Сообщество | Академическое | Большое, коммерческое | LS активнее |

**Вывод:** INCEpTION сильнее в семантике, Label Studio сильнее в масштабировании и интеграции. Заменять одно другим не нужно. Нужно **взять лучшее из INCEpTION** и реализовать в KADIMA.

---

## 5. Рекомендация: гибридный подход

### 5.1 Стратегия

**Не подключаем INCEpTION как отдельный инструмент** (лишняя инфраструктура, Java-стек). Вместо этого **реализуем 3 ключевые фичи INCEpTION внутри KADIMA**:

| Фича INCEpTION | Как реализуем в KADIMA | Модуль | Phase |
|-----------------|----------------------|--------|-------|
| Recommender system | KADIMA ML backend → Label Studio с multi-suggestion | M15+ | v1.x |
| Knowledge base | SQLite KB + entity linking через NeoDictaBERT embeddings | M19 (new) | v1.x |
| Active learning | Dicta-LM 3.0 + uncertainty sampling | M20 (new) | v2.0 |

### 5.2 M19: Knowledge Base & Entity Linking

```
┌─────────────────────────────────────────────────┐
│              KADIMA Knowledge Base               │
│                                                  │
│  Term DB (SQLite):                               │
│  - surface, canonical, lemma, POS                │
│  - definition (generated by Dicta-LM)            │
│  - related_terms (embedding similarity)           │
│  - external_links (Wikidata, DBpedia — optional)  │
│                                                  │
│  Entity Linking:                                 │
│  - NeoDictaBERT embeddings → cluster terms        │
│  - Surface → canonical → definition               │
│  - Cross-reference with gold corpus               │
└─────────────────────────────────────────────────┘
```

**Зачем:**
- Термины имеют определения и связи — это knowledge base
- Entity linking: «פלדה אל-חלד» → canonical: «פלדה אל-חלד» → definition: «нержавеющая сталь»
- Связи между терминами (синонимы, гипонимы, тематические группы)

### 5.3 M15+: Recommender System (enhanced Label Studio ML backend)

Вместо static pre-annotations — **multi-suggestion recommender**:

```python
# KADIMA Recommender Backend для Label Studio
class KadimaRecommenderBackend(LabelStudioMLBase):
    """INCEpTION-style recommender: предлагает 3 варианта аннотации."""
    
    def predict(self, tasks, **kwargs):
        predictions = []
        for task in tasks:
            text = task['data']['text']
            doc = self.nlp(text)
            
            results = []
            for ent in doc.ents:
                # Вместо одного предсказания — ранжированный список
                top_candidates = self._get_top_candidates(ent, doc)
                for rank, (label, score) in enumerate(top_candidates):
                    results.append({
                        'from_name': 'label',
                        'to_name': 'text',
                        'type': 'labels',
                        'value': {
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'text': ent.text,
                            'labels': [label],
                            'score': score
                        },
                        'meta': {'rank': rank + 1}  # 1st, 2nd, 3rd suggestion
                    })
            
            predictions.append({'result': results})
        return predictions
```

### 5.4 M20: Active Learning (v2.0)

```
Цикл active learning:
1. KADIMA pipeline делает predictions на unlabeled данных
2. Система выбирает НАИБОЛЕЕ НЕУВЕРЕННЫЕ примеры (uncertainty sampling)
3. Аннотатор размечает эти примеры в Label Studio
4. Дообучение модели на новых аннотациях
5. Снова шаг 1 (улучшенная модель → лучше predictions)
```

---

## 6. Сравнение: INCEpTION vs Label Studio + KADIMA enhancements

| Функция | INCEpTION (standalone) | Label Studio + KADIMA enhancements |
|---------|----------------------|-----------------------------------|
| NER annotation | ✅ | ✅ |
| Relation annotation | ✅ | ⚠️ через LS custom template (v1.x) |
| Coreference | ✅ | ⚠️ через LS + KADIMA M9 (v2.0) |
| Recommender | ✅ встроенный | ✅ KADIMA ML backend (multi-suggestion) |
| Knowledge base | ✅ встроенный | ✅ KADIMA M19 (SQLite + embeddings) |
| Active learning | ✅ | ✅ KADIMA M20 (v2.0) |
| Multi-modal | ❌ | ✅ (audio, image, video) |
| Hebrew support | ⚠️ | ✅ (RTL, custom templates) |
| Инфраструктура | Java + DB | Python + SQLite (уже есть) |
| Интеграция с pipeline | Отдельный REST | Нативная (один стек) |

---

## 7. Что нужно добавить в документацию KADIMA

### 7.1 SCOPE.md — новые модули

| Модуль | Описание | Приоритет |
|--------|----------|-----------|
| M19. Knowledge Base | Term definitions, entity linking, semantic relations | P1 (v1.x) |
| M20. Active Learning | Uncertainty sampling, iterative annotation | P2 (v2.0) |

### 7.2 VISION.md — расширение аудитории

Добавить сегмент «Knowledge managers» — специалисты, которые строят онтологии и терминологические базы знаний для иврита.

---

## 8. Источники

| Ресурс | URL | Лицензия |
|--------|-----|----------|
| INCEpTION | https://github.com/inception-project/inception | Apache 2.0 |
| INCEpTION Website | https://inception-project.github.io | — |
| INCEpTION Demo | https://morbo.ukp.informatik.tu-darmstadt.de/demo | — |
| Label Studio ML Backend | https://github.com/HumanSignal/label-studio-ml-backend | Apache 2.0 |
