# tests/conftest.py
"""Pytest fixtures для KADIMA тестов."""

import os
import pytest
import sqlite3
from pathlib import Path

# Путь к тестовым данным
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def sample_hebrew_text():
    """Один документ на иврите для smoke test."""
    return "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה מאד."


@pytest.fixture
def sample_tokens():
    """Список токенов для unit-тестов."""
    from kadima.engine.hebpipe_wrappers import Token
    return [
        Token(index=0, surface="פלדה", start=0, end=4),
        Token(index=1, surface="חזקה", start=5, end=9),
        Token(index=2, surface="משמשת", start=10, end=16),
        Token(index=3, surface="בבניין.", start=17, end=24),
    ]


@pytest.fixture
def pipeline_config():
    """Дефолтная конфигурация pipeline."""
    from kadima.pipeline.config import PipelineConfig
    return PipelineConfig(profile="balanced", min_freq=2)


@pytest.fixture
def tmp_db(tmp_path):
    """Временная SQLite БД для тестов."""
    db_path = str(tmp_path / "test_kadima.db")
    from kadima.data.db import run_migrations
    run_migrations(db_path)
    return db_path


@pytest.fixture
def gold_corpus_he_01():
    """Gold corpus he_01 для acceptance test."""
    corpus_dir = os.path.join(TEST_DATA_DIR, "he_01_sentence_token_lemma_basics")
    if not os.path.exists(corpus_dir):
        pytest.skip(f"Gold corpus not found: {corpus_dir}")
    return corpus_dir


@pytest.fixture
def all_gold_corpora():
    """Все 26 gold corpora."""
    corpora = []
    for name in sorted(os.listdir(TEST_DATA_DIR)):
        path = os.path.join(TEST_DATA_DIR, name)
        if os.path.isdir(path) and name.startswith("he_"):
            corpora.append(path)
    if not corpora:
        pytest.skip("No gold corpora found in tests/data/")
    return corpora


@pytest.fixture
def mock_llm_client(monkeypatch):
    """Мок llama.cpp сервера для тестов без GPU."""
    class MockLlamaCppClient:
        def is_loaded(self):
            return True

        def generate(self, prompt, max_tokens=512, temperature=0.7):
            return "זהו מבחן. זהו טקסט שנוצר על ידי מודל מזויף."

        def chat(self, messages, max_tokens=512):
            return "תשובה לבדיקה."

    monkeypatch.setattr("kadima.llm.client.LlamaCppClient", MockLlamaCppClient)
    return MockLlamaCppClient()


@pytest.fixture
def mock_ls_client(monkeypatch):
    """Мок Label Studio для тестов без Docker."""
    class MockLabelStudioClient:
        def health_check(self):
            return True

        def create_project(self, name, label_config, description=""):
            return 1

        def import_tasks(self, project_id, tasks):
            return list(range(len(tasks)))

        def export_annotations(self, project_id, export_type="JSON"):
            return []

        def get_project_stats(self, project_id):
            return {"total": 0, "completed": 0, "skipped": 0}

    monkeypatch.setattr("kadima.annotation.ls_client.LabelStudioClient", MockLabelStudioClient)
    return MockLabelStudioClient()


@pytest.fixture
def hebrew_ner_template():
    """Загруженный Hebrew NER template."""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "hebrew_ner.xml"
    )
    if not os.path.exists(template_path):
        pytest.skip("hebrew_ner.xml not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
