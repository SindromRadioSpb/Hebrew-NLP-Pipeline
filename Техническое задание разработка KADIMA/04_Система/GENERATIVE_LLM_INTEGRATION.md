# 4.6. Generative LLM Integration — KADIMA v1.x / v2.0

> Дата: 2026-03-30 | Статус: analysis
> Связанные: 04_Система/NLP_STACK_INTEGRATION.md, 01_Концепт/VISION.md, 01_Концепт/SCOPE.md

---

## 1. Текущее состояние: белое пятно

### 1.1 Что в документации

**VISION.md, явно:**
> Не входит: LLM training (использует готовые модели)

**SCOPE.md:** Модули M1–M17 — все связаны с NLP-анализом (токенизация, морфология, извлечение терминов). Генеративная модель **нигде не упомянута**.

### 1.2 Вывод

**Да, это белое пятно.** KADIMA v1.0 — это «аналитический» продукт: берём текст → разбираем → извлекаем → валидируем. Генерация текста не предусмотрена. Но для масштабирования это критический пробел.

---

## 2. Аудит рынка: Hebrew Generative Models (open-source)

### 2.1 Dicta-LM 3.0 — текущий SOTA для иврита

| Параметр | Dicta-LM 3.0 |
|----------|-------------|
| Организация | DICTA (Israel) |
| Лицензия | Apache 2.0 ✅ |
| Размеры | 1.7B / 12B (Nemotron) / 24B |
| Варианты | Base / Instruct / Thinking |
| Контекст | 65K токенов |
| Языки | Иврит + Английский |
| Квантизация | FP8, W4A16, GGUF |
| Tool-calling | ✅ (24B Thinking) |
| Дата | Dec 2025 |
| SOTA Hebrew benchmarks | ✅ лучший в своём weight-class |

**Коллекция на HuggingFace:** `dicta-il/dictalm-30-collection`

| Модель | VRAM (FP16) | VRAM (Q4) | VRAM (GGUF Q4) | Подходит для RTX 3070? |
|--------|-------------|-----------|-----------------|----------------------|
| DictaLM-3.0-1.7B-Instruct | ~3.5 GB | ~1.2 GB | ~1 GB | ✅ легко |
| DictaLM-3.0-Nemotron-12B-Instruct | ~24 GB | ~7 GB | ~6.5 GB | ⚠️ гранично (Q4) |
| DictaLM-3.0-24B-Thinking | ~48 GB | ~14 GB | ~13 GB | ❌ не влезает |

### 2.2 Альтернативы

| Модель | Иврит SOTA? | Размер | Лицензия | Иврит-специализация |
|--------|------------|--------|----------|-------------------|
| **Dicta-LM 3.0** | ✅ #1 | 1.7B–24B | Apache 2.0 | Нативная, SOTA |
| Llama 3.3 / 4 | ⚠️ мультиязычный | 8B–70B | Llama License | Общий, иврит — побочный |
| Qwen 2.5 / 3 | ⚠️ мультиязычный | 0.5B–72B | Apache 2.0 | Общий, иврит — побочный |
| Mistral / Mixtral | ⚠️ слабый иврит | 7B–8x22B | Apache 2.0 | Европейские языки, иврит слабый |
| HebrewGPT (296M) | ❌ мелкий | 296M | MIT | Только генерация, без instruct |
| Aya 23 (Cohere) | ⚠️ мультиязычный | 8B–35B | CC BY 4.0 | 23 языка, иврит не фокус |

**Вывод:** Dicta-LM 3.0 — **безусловный лидер** для иврита. Специализированная модель, SOTA на Hebrew benchmarks, Apache 2.0, GGUF для llama.cpp. Нет конкурентов в open-source Hebrew generative space.

---

## 3. Анализ: зачем KADIMA генеративная модель

### 3.1 Внутренние потребности продукта (v1.x)

| Задача | Без LLM | С Dicta-LM |
|--------|---------|------------|
| Генерация определений терминов | ❌ нет | ✅ LLM генерирует по контексту |
| QA: ответы на вопросы о корпусе | ❌ нет | ✅ RAG: corpus → LLM → ответ |
| Автоматическая валидация (M11 assist) | Правила | LLM проверяет семантику |
| Генерация review-комментариев | ❌ нет | ✅ LLM объясняет почему PASS/FAIL |
| Объяснение морфологии | ❌ нет | ✅ LLM объясняет на иврите |
| Term definition enrichment | ❌ нет | ✅ LLM дополняет определения |
| Corpus summarization | ❌ нет | ✅ LLM резюмирует корпус |

### 3.2 Сценарий: Ульпан / обучение ивриту

Это **отдельный рынок**, но KADIMA может стать платформой:

| Фича | Как работает | Модуль |
|------|-------------|--------|
| Грамматический помощник | Стudent вводит предложение → LLM проверяет грамматику, объясняет ошибки | Dicta-LM Instruct |
| Генерация упражнений | LLM генерирует предложения с заданными конструкциями (смихут, биньян) | Dicta-LM Base |
| Морфологический разбор с объяснением | KADIMA M3 разбирает → LLM объясняет понятно | M3 + Dicta-LM |
| Чтение текстов с подсказками | Текст → клик на слово → LLM даёт контекстное определение | Dicta-LM Instruct |
| Переводческий ассистент | EN↔HE перевод с объяснением нюансов | Dicta-LM Instruct |
| Flashcard generation | LLM генерирует карточки из корпуса терминов | Dicta-LM Base |

### 3.3 Масштабирование

| Направление | Нужен LLM? | Dicta-LM подходит? |
|-------------|-----------|-------------------|
| Text analysis (v1.0) | Нет | — |
| Term definitions (v1.x) | Да | ✅ |
| QA over corpus (v1.x) | Да | ✅ RAG |
| Ulpan / Education (v2.0) | Да | ✅ |
| Audio transcription assist (v2.0) | Частично | ✅ пост-обработка |
| Document understanding (v2.0) | Да | ✅ |
| Full chatbot (v3.0) | Да | ✅ |

---

## 4. Технический анализ: совместимость с нашей инфраструктурой

### 4.1 Железо пользователя

| Компонент | Есть | Dicta-LM 1.7B | Dicta-LM 12B (Q4) |
|-----------|------|---------------|-------------------|
| RTX 3070 8 GB VRAM | ✅ | ✅ ~1 GB | ⚠️ ~6.5 GB |
| RAM 32 GB | ✅ | ✅ | ✅ (offload) |
| WSL2 RAM 3.8 GB + swap | ⚠️ | ✅ | ⚠️ |
| llama.cpp | ✅ (уже в стеке) | ✅ GGUF | ✅ GGUF |

### 4.2 Интеграция с текущим стеком

```
┌───────────────────────────────────────────────────────────┐
│                    KADIMA Stacks                          │
│                                                           │
│  ANALYSIS STACK (v1.0):                                  │
│  spaCy + HebPipe + NeoDictaBERT → term extraction        │
│                                                           │
│  GENERATION STACK (v1.x / v2.0): ← NEW                  │
│  llama.cpp + Dicta-LM 3.0 → text generation              │
│                                                           │
│  BRIDGE:                                                 │
│  KADIMA Pipeline results → RAG prompt → Dicta-LM         │
│  (термины + контекст → LLM → определения/объяснения)     │
└───────────────────────────────────────────────────────────┘
```

### 4.3 Dicta-LM через llama.cpp

```bash
# Скачивание GGUF модели
# 1.7B instruct — лёгкая, для CPU/GPU
wget https://huggingface.co/dicta-il/DictaLM-3.0-1.7B-Instruct-GGUF/resolve/main/DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf

# 12B Nemotron instruct — для GPU с 8 GB VRAM
wget https://huggingface.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF/resolve/main/DictaLM-3.0-Nemotron-12B-Instruct-Q4_K_M.gguf

# Запуск через llama.cpp server
./llama-server -m DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf -ngl 35 --port 8081
```

### 4.4 Интеграция в Label Studio (future)

Dicta-LM может стать ML backend для Label Studio — генерация подсказок при аннотации:

```python
# label-studio ML backend: LLM-assisted annotation
class DictaLMAnnotationBackend(LabelStudioMLBase):
    def predict(self, tasks, **kwargs):
        # KADIMA pipeline → pre-annotations
        # Dicta-LM → generate suggested corrections/explanations
        ...
```

---

## 5. Модельный выбор: рекомендация

### 5.1 Для v1.x (текущее железо, RTX 3070)

| Задача | Модель | Формат | VRAM | Latency |
|--------|--------|--------|------|---------|
| Term definitions | DictaLM-3.0-1.7B-Instruct | GGUF Q4 | ~1 GB | <1 сек |
| Grammar explanations | DictaLM-3.0-1.7B-Instruct | GGUF Q4 | ~1 GB | <1 сек |
| QA over corpus | DictaLM-3.0-1.7B-Instruct | GGUF Q4 | ~1 GB | 1-2 сек |
| Complex reasoning | DictaLM-3.0-Nemotron-12B-Instruct | GGUF Q4 | ~6.5 GB | 3-5 сек |

**Рекомендация:** начать с **1.7B Instruct** (лёгкая, быстрая, влезает с запасом). 12B Nemotron — для сложных задач, если будет мало 1.7B.

### 5.2 Для v2.0 (апгрейд железа / cloud)

| Задача | Модель | Формат |
|--------|--------|--------|
| Ulpan assistant | DictaLM-3.0-Nemotron-12B-Instruct | FP8 / GGUF |
| Full chatbot | DictaLM-3.0-24B-Thinking | FP8 |
| Tool-calling agent | DictaLM-3.0-24B-Thinking | FP8 |

---

## 6. Рекомендации

### 6.1 Что делать сейчас (v1.0 planning)

1. **Не добавлять LLM в v1.0 scope** — это раздует MVP и отсрочит релиз
2. **Заложить архитектурный шов** — API endpoint для LLM, но пока не реализовывать
3. **Добавить в ROADMAP Phase 4** — LLM integration как v1.1

### 6.2 Что заложить в архитектуру сейчас

В `ARCHITECTURE.md` добавить слой:

```
Engine Layer (v1.0):
  spaCy Pipeline → M1-M8 → Results

Engine Layer (v1.x, архитектурный шов):
  spaCy Pipeline → M1-M8 → Results
  Dicta-LM Service → text generation, QA, explanations
  RAG Bridge → corpus context → LLM prompt → enriched results
```

### 6.3 Roadmap

| Phase | Что | Модель | Когда |
|-------|-----|--------|-------|
| v1.0 | Ничего (только шов) | — | Month 3 |
| v1.1 | Term definitions + grammar explanations | DictaLM 1.7B | Month 5 |
| v1.2 | QA over corpus (RAG) | DictaLM 1.7B / 12B | Month 7 |
| v2.0 | Ulpan mode + chatbot | DictaLM 12B / 24B | Month 9+ |

### 6.4 Что НЕ нужно

- Не обучать свою LLM — Dicta-LM 3.0 уже SOTA
- Не тянуть 24B на десктоп — cloud deployment для v2.0
- Не дублировать HuggingFace — скачиваем готовые модели
- Не конкурировать с Dicta — партнёрство / использование

---

## 7. Итоговая таблица: полнота стека KADIMA

| Компонент | v1.0 | v1.x | v2.0 |
|-----------|------|------|------|
| Токенизация (M1-M2) | ✅ HebPipe | ✅ | ✅ |
| Морфология (M3) | ✅ HebPipe | ✅ | ✅ |
| Term extraction (M4-M8) | ✅ KADIMA | ✅ | ✅ |
| NER (M9) | ⚠️ NeoDictaBERT | ✅ | ✅ |
| Validation (M11) | ✅ KADIMA | ✅ | ✅ |
| Annotation (M15) | ✅ Label Studio | ✅ | ✅ |
| TM projection (M16) | ✅ KADIMA | ✅ | ✅ |
| **Генеративная модель** | ❌ **белое пятно** | ✅ **Dicta-LM 1.7B** | ✅ **Dicta-LM 12B/24B** |
| **Ulpan / Education** | ❌ | ❌ | ✅ **Dicta-LM + RAG** |
| Audio annotation | ❌ | ⚠️ Label Studio | ✅ |
| Image / OCR | ❌ | ❌ | ✅ |

---

## 8. Источники

| Ресурс | URL | Лицензия |
|--------|-----|----------|
| Dicta-LM 3.0 Collection | https://huggingface.co/collections/dicta-il/dictalm-30-collection | Apache 2.0 |
| Dicta-LM 3.0 24B Base | https://huggingface.co/dicta-il/DictaLM-3.0-24B-Base | Apache 2.0 |
| Dicta-LM 3.0 12B Instruct | https://huggingface.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct | Apache 2.0 |
| Dicta-LM 3.0 1.7B Instruct | https://huggingface.co/dicta-il/DictaLM-3.0-1.7B-Instruct | Apache 2.0 |
| Dicta-LM 3.0 Thinking GGUF | https://huggingface.co/dicta-il/DictaLM-3.0-24B-Thinking-GGUF | Apache 2.0 |
| Dicta-LM 3.0 Paper | https://arxiv.org/abs/2602.02104 | — |
| Hebrew LLM Leaderboard | https://huggingface.co/spaces/hebrew-llm-leaderboard/leaderboard | — |
| Dicta-LM 2.0 Collection | https://huggingface.co/collections/dicta-il/dicta-lm-20-collection | Apache 2.0 |
| Dicta-LM 2.0 Instruct | https://huggingface.co/dicta-il/dictalm2.0-instruct | Apache 2.0 |
