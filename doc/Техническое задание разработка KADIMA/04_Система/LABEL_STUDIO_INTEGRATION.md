# 4.5. Label Studio Integration — KADIMA v1.0

> Дата: 2026-03-30 | Статус: draft
> Связанные: 04_Система/NLP_STACK_INTEGRATION.md, 04_Система/ARCHITECTURE.md, 02_Продукт/PRD.md, 01_Концепт/SCOPE.md

---

## 1. Резюме

Label Studio — open-source платформа аннотации данных. Закрывает **3 белых пятна** KADIMA, которые иначе нужно писать с нуля.

| Что закрывает | KADIMA модуль | Label Studio фича |
|---------------|---------------|-------------------|
| Annotation Interface | M15 (P2, optional) | Labeling UI + templates |
| Gold Corpus Creation | M11 input | Аннотация → экспорт → gold corpus |
| NER Training Data | M9 input | NER annotation → CoNLL-U export |
| Multi-modal (будущее) | — | Audio, image, video annotation |

**Лицензия:** Apache 2.0 (Community) — полностью совместим с некоммерческим проектом.

---

## 2. Audit: Label Studio — что можно использовать бесплатно

### 2.1 Community Edition (Apache 2.0, free) ✅

| Фича | Статус | KADIMA потребность |
|-------|--------|-------------------|
| Text NER annotation | ✅ | M9, M11 |
| Text classification | ✅ | M12 (noise classifier) |
| Custom labeling templates (XML) | ✅ | Hebrew-specific templates |
| Import: JSON, CSV, TSV, ZIP | ✅ | Corpus import |
| Export: JSON, CoNLL-U, COCO, Pascal VOC | ✅ | Gold corpus export |
| REST API + Python SDK | ✅ | Integration with pipeline |
| ML backend integration (custom) | ✅ | KADIMA as pre-annotator |
| Webhooks | ✅ | Pipeline automation |
| Docker deployment | ✅ | Self-hosted |
| Multi-project support | ✅ | Multiple corpora |
| Data Manager (filters, search) | ✅ | Corpus browsing |
| Pre-annotated data import | ✅ | KADIMA predictions |
| Predictions from ML models | ✅ | NeoDictaBERT pre-annotations |

### 2.2 Enterprise Only (paid) ❌ — не нужно для v1.0

| Фича | Нужно? | Альтернатива |
|-------|--------|-------------|
| Role-based workflows | Nice-to-have | Community: single-user OK |
| Active learning loops | Nice-to-have | Community: manual + predictions |
| Agreement metrics | Nice-to-have | KADIMA M11 (свой validation) |
| Analytics dashboards | Nice-to-have | KADIMA может строить свои |
| SSO / RBAC | Не нужно | Desktop single-user |

**Вывод:** Community edition покрывает 100% потребностей v1.0.

---

## 3. Audit: spaCy Integration в Label Studio

### 3.1 Что есть

Label Studio ML Backend имеет **готовый spaCy-плагин**:

```
label-studio-ml-backend/label_studio_ml/examples/spacy/
```

**Функционал:**
- NER pre-annotation через spaCy модели
- POS tagging (coming soon)
- Configurable labels через mapping
- Работает с любой spaCy моделью (включая наш pipeline)

**Поддерживаемые labels (по умолчанию):**
CARDINAL, DATE, EVENT, FAC, GPE, LANGUAGE, LAW, LOC, ORG, PERSON, TIME

**Кастомизация:**
- `SPACY_MODEL` env var — указать свою модель
- `_custom_labels_mapping` — маппинг spaCy entities → свои labels

### 3.2 Интеграция с KADIMA pipeline

KADIMA spaCy pipeline (NeoDictaBERT + HebPipe) может служить как ML backend для Label Studio:

```
┌──────────────────────────────────────────────────────┐
│                  Label Studio (UI)                    │
│  Annotator opens task → sees pre-annotations         │
│  Corrects/adds labels → saves annotation             │
└──────────────┬───────────────────────┬───────────────┘
               │ request               │ response
               ▼                       │
┌──────────────────────────────────────┤
│  KADIMA ML Backend (localhost:9090)  │
│                                      │
│  1. Receive task text                │
│  2. Run KADIMA pipeline:             │
│     - HebPipe (M1-M3)               │
│     - NeoDictaBERT (NER)            │
│  3. Return pre-annotations          │
│  4. On annotation submit:           │
│     - Export as gold corpus          │
│     - Retrain NER model             │
└──────────────────────────────────────┘
```

---

## 4. Gap Analysis: KADIMA vs Label Studio

### 4.1 Что KADIMA делает, Label Studio НЕ делает

| Функция | KADIMA | Label Studio | Решение |
|---------|--------|-------------|---------|
| Sentence splitting (M1) | ✅ | ❌ | KADIMA |
| Tokenization (M2) | ✅ | ❌ | KADIMA |
| Morphological analysis (M3) | ✅ | ❌ | KADIMA |
| N-gram extraction (M4) | ✅ | ❌ | KADIMA |
| NP chunk extraction (M5) | ✅ | ❌ | KADIMA |
| Canonicalization (M6) | ✅ | ❌ | KADIMA |
| Association measures (M7) | ✅ | ❌ | KADIMA |
| Term extraction (M8) | ✅ | ❌ | KADIMA |
| Validation framework (M11) | ✅ | ❌ (enterprise: partial) | KADIMA |
| Corpus statistics (M14) | ✅ | ❌ | KADIMA |
| TM projection (M16) | ✅ | ❌ | KADIMA |

### 4.2 Что Label Studio делает, KADIMA НЕ делает (или делает плохо)

| Функция | Label Studio | KADIMA v1.0 | Решение |
|---------|-------------|-------------|---------|
| Annotation UI | ✅ готовый | ❌ не начинали (M15 = P2) | **Использовать LS** |
| Gold corpus creation | ✅ аннотация → экспорт | ❌ ручной CSV | **Использовать LS** |
| NER annotation | ✅ NER template | ❌ нет UI | **Использовать LS** |
| Multi-user annotation | ✅ | ❌ single-user | LS Community |
| Audio annotation | ✅ | ❌ | LS (будущее) |
| Image annotation | ✅ | ❌ | LS (будущее) |
| Video annotation | ✅ | ❌ | LS (будущее) |
| Active learning (auto-select) | Enterprise only | ❌ | Phase 2+ |
| ML pre-annotation | ✅ | ❌ | KADIMA = LS ML backend |

### 4.3 Что НИКТО не закрывает (белые пятна)

| Проблема | KADIMA | Label Studio | Решение |
|----------|--------|-------------|---------|
| Hebrew-specific tokenization | ✅ | ❌ | KADIMA |
| Hebrew morphology | ✅ | ❌ | KADIMA + HebPipe |
| Hebrew term extraction | ✅ | ❌ | KADIMA (M8) |
| Association measures (PMI, LLR) | ✅ | ❌ | KADIMA (M7) |
| Gold corpus → validation report | ✅ | ❌ | KADIMA (M11) |
| TM candidate projection | ✅ | ❌ | KADIMA (M16) |

---

## 5. Архитектура интеграции

### 5.1 Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────────────────┐        ┌──────────────────────────┐   │
│  │   Label Studio (UI)  │◄──────►│  KADIMA Desktop (PyQt)   │   │
│  │                      │  API   │                          │   │
│  │  - Annotation tasks  │        │  - Pipeline control      │   │
│  │  - NER labeling      │        │  - Results view          │   │
│  │  - Gold corpus mgmt  │        │  - Validation reports    │   │
│  │  - Multi-modal (fut) │        │  - Term extraction       │   │
│  └──────────┬───────────┘        └────────────┬─────────────┘   │
│             │                                 │                 │
│             │  predictions/annotations         │  gold corpus    │
│             ▼                                 ▼                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              KADIMA ML Backend (localhost:9090)           │   │
│  │                                                          │   │
│  │  label-studio-ml-backend SDK                             │   │
│  │       │                                                  │   │
│  │       ▼                                                  │   │
│  │  ┌── spaCy Pipeline ──────────────────────────────────┐  │   │
│  │  │  NeoDictaBERT ← HebPipe M1-M3 ← spaCy lang/he     │  │   │
│  │  │  NER predictions → Label Studio                     │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  KADIMA Engine (M4-M8, M11, M14, M16):                  │   │
│  │  - Term extraction, AM, validation                       │   │
│  │  - Runs via REST API, results back to LS or KADIMA UI    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SQLite Storage                         │   │
│  │  label_studio.sqlite3  +  kadima.db                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow: Closed Loop

```
1. KADIMA pipeline прогоняет корпус → создаёт pre-annotations
                │
                ▼
2. Pre-annotations импортируются в Label Studio (JSON import)
                │
                ▼
3. Аннотатор проверяет/корректирует в LS UI
                │
                ▼
4. Экспорт аннотаций из LS → CoNLL-U / JSON
                │
                ▼
5. Аннотации → Gold Corpus для KADIMA M11 (validation)
           → Training Data для дообучения NER (M9)
                │
                ▼
6. Дообученная модель → лучше pre-annotations → шаг 1
```

### 5.3 Label Studio Templates для иврита

Преднастроенные templates:

**NER для иврита:**
```xml
<View>
  <Labels name="label" toName="text">
    <Label value="PERSON" background="#9254DE"/>
    <Label value="LOCATION" background="#D3F261"/>
    <Label value="ORG" background="#ADC6FF"/>
    <Label value="DATE" background="#D4380D"/>
    <Label value="QUANTITY" background="#FFC069"/>
    <Label value="MATERIAL" background="#5CDBD3"/>
    <Label value="TERM" background="#389E0D"/>
  </Labels>
  <Text name="text" value="$text" 
        style="direction: rtl; text-align: right; font-size: 18px;"/>
</View>
```

**Term Review (для валидации терминов):**
```xml
<View>
  <Header value="Term Review"/>
  <Text name="term" value="$term_surface" 
        style="direction: rtl; font-size: 20px; font-weight: bold;"/>
  <Text name="context" value="$context"
        style="direction: rtl;"/>
  <Choices name="decision" toName="term" choice="single" showInline="true">
    <Choice value="valid_term" hint="Действительный термин"/>
    <Choice value="invalid_term" hint="Не является термином"/>
    <Choice value="needs_canonical" hint="Нужна каноническая форма"/>
    <Choice value="uncertain" hint="Требуется дополнительная проверка"/>
  </Choices>
</View>
```

**POS/Morphology Annotation:**
```xml
<View>
  <Labels name="pos" toName="text">
    <Label value="NOUN" background="#FFA39E"/>
    <Label value="VERB" background="#D4380D"/>
    <Label value="ADJ" background="#FFC069"/>
    <Label value="ADV" background="#AD8B00"/>
    <Label value="PREP" background="#D3F261"/>
    <Label value="DET" background="#389E0D"/>
    <Label value="CONJ" background="#5CDBD3"/>
    <Label value="PRON" background="#096DD9"/>
  </Labels>
  <Text name="text" value="$text"
        style="direction: rtl; text-align: right; font-size: 18px;"/>
</View>
```

---

## 6. Интеграция: KADIMA как ML Backend для Label Studio

### 6.1 Код ML Backend

```python
# ml_backends/kadima_spacy_backend.py
from label_studio_ml.model import LabelStudioMLBase
import spacy

class KadimaNERBackend(LabelStudioMLBase):
    """KADIMA pipeline как ML backend для Label Studio."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Загружаем KADIMA spaCy pipeline с NeoDictaBERT
        self.nlp = spacy.load("he_kadima_pipeline")
        
        # Маппинг: KADIMA entities → LS labels
        self.label_map = {
            "PERSON": "PERSON",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "ORG": "ORG",
            "DATE": "DATE",
            "QUANTITY": "QUANTITY",
            # KADIMA-specific
            "MATERIAL": "MATERIAL",
            "TERM": "TERM",
        }

    def predict(self, tasks, **kwargs):
        """Предсказания для Label Studio."""
        predictions = []
        
        for task in tasks:
            text = task['data']['text']
            doc = self.nlp(text)
            
            results = []
            for ent in doc.ents:
                label = self.label_map.get(ent.label_, ent.label_)
                results.append({
                    'from_name': 'label',
                    'to_name': 'text',
                    'type': 'labels',
                    'value': {
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'text': ent.text,
                        'labels': [label],
                        'score': 0.85  # confidence
                    }
                })
            
            predictions.append({
                'result': results,
                'score': 0.85
            })
        
        return predictions

    def fit(self, event, data, **kwargs):
        """Обучение на аннотациях из Label Studio."""
        # Экспорт аннотаций → training data
        # Дообучение spaCy NER component
        # Сохранение обновлённой модели
        if event == 'ANNOTATION_CREATED':
            self._retrain_ner(data)
        return {'status': 'ok'}
```

### 6.2 Docker Compose

```yaml
# docker-compose.kadima-ls.yml
version: '3.8'

services:
  label-studio:
    image: heartexlabs/label-studio:latest
    ports:
      - "8080:8080"
    volumes:
      - ./ls_data:/label-studio/data
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_ML_BACKENDS=http://kadima-ml:9090

  kadima-ml:
    build:
      context: ./ml_backends
      dockerfile: Dockerfile
    ports:
      - "9090:9090"
    environment:
      - LABEL_STUDIO_URL=http://label-studio:8080
      - LABEL_STUDIO_API_KEY=${LS_API_KEY}
      - SPACY_MODEL=he_kadima_pipeline
    volumes:
      - ./kadima_models:/app/models
```

---

## 7. Масштабирование: Multi-modal

### 7.1 Что Label Studio даёт бесплатно

| Модальность | Community | Примеры задач |
|-------------|-----------|--------------|
| **Text** | ✅ | NER, classification, POS, sentiment |
| **Audio** | ✅ | Transcription, speaker diarization, emotion |
| **Image** | ✅ | Classification, object detection, segmentation |
| **Video** | ✅ | Classification, object tracking |
| **Time series** | ✅ | Classification, event recognition |
| **Multi-modal** | ✅ | Audio+text, image+text |

### 7.2 Сценарии масштабирования KADIMA через Label Studio

**Phase 1 (v1.0): Text only**
- Hebrew NER annotation
- Term validation
- Gold corpus creation

**Phase 2 (v1.x): Text + Audio**
- Hebrew audio transcription annotation
- Audio → text alignment
- Label Studio: speaker diarization template

**Phase 3 (v2.0): Text + Image**
- OCR annotation (Hebrew documents)
- Image classification for document types
- Label Studio: OCR template + classification

### 7.3 Архитектура масштабирования

```
v1.0: KADIMA (text pipeline) ←→ Label Studio (text annotation)
                                    │
v1.x: + Audio ML Backend          │ ← расширяем LS backend
      (Whisper / NeMo ASR)         │
                                    │
v2.0: + Image ML Backend          │
      (Tesseract / PaddleOCR)      │
```

---

## 8. Что НЕ нужно писать (экономия)

| Модуль | Было: писать с нуля | Стало: Label Studio |
|--------|--------------------|--------------------|
| M15. Annotation Interface | PyQt UI (~2-3 месяца) | ✅ готовый |
| Gold Corpus Creator | парсер CSV + UI (~1 месяц) | ✅ LS annotation → export |
| NER Annotation UI | (~2 месяца) | ✅ LS NER template |
| Multi-user support | (v2.0, ~3 месяца) | ✅ LS Community |
| Audio annotation | (v3.0, ~4 месяца) | ✅ LS + ASR backend |

**Итого экономия:** 8-12 человеко-месяцев UI-разработки.

---

## 9. Что ОСТАЁТСЯ писать (KADIMA core)

| Модуль | Причина |
|--------|---------|
| M1–M3 (HebPipe integration) | LS не делает NLP |
| M4–M8 (term extraction) | LS не извлекает термины |
| M6 (canonicalization) | LS не канонизирует |
| M7 (association measures) | LS не считает PMI/LLR |
| M11 (validation framework) | LS не делает PASS/WARN/FAIL отчёты |
| M14 (corpus manager) | LS не считает статистику корпуса |
| M16 (TM projection) | LS не проецирует в TM |
| ML backend wrapper | тонкий слой: LS ↔ KADIMA pipeline |
| Hebrew templates | XML config для LS |

---

## 10. Обновление документации KADIMA

### 10.1 SCOPE.md — M15 переопределяется

**Было:**
> M15. Annotation Interface — Visual annotation (P2)

**Стало:**
> M15. Annotation Interface — Label Studio Community (open-source, Apache 2.0). Не пишем — используем готовое. KADIMA интегрируется как ML backend для pre-annotation. Custom Hebrew templates настроены.

### 10.2 ROADMAP.md — добавить Phase 0

**Phase 0: Label Studio Setup (Week 0–1)**
- Установить Label Studio (Docker / pip)
- Настроить Hebrew NER template
- Настроить Term Review template
- Подключить KADIMA ML backend (spaCy NER)
- Smoke test: аннотация → экспорт → gold corpus

### 10.3 BACKLOG.md — новый Epic 7

**Epic 7: Label Studio Integration (P1)**
- LS installation & configuration
- Hebrew NER template
- Hebrew Term Review template
- KADIMA ML backend (label-studio-ml-backend SDK)
- Pre-annotation workflow (KADIMA → LS)
- Gold corpus export (LS → KADIMA M11)
- NER training data pipeline (LS → spaCy training)

---

## 11. Источники

| Ресурс | URL | Лицензия |
|--------|-----|----------|
| Label Studio | https://github.com/HumanSignal/label-studio | Apache 2.0 |
| LS ML Backend | https://github.com/HumanSignal/label-studio-ml-backend | Apache 2.0 |
| LS spaCy example | https://github.com/HumanSignal/label-studio-ml-backend/tree/master/label_studio_ml/examples/spacy | Apache 2.0 |
| LS Templates | https://labelstud.io/templates | Apache 2.0 |
| LS Playground | https://labelstud.io/playground | Apache 2.0 |
| LS API Docs | https://labelstud.io/guide/api | Apache 2.0 |
| LS Editions Compare | https://labelstud.io/guide/label_studio_compare | — |
