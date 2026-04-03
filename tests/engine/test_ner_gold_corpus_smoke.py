"""Gold-corpus smoke tests for M17 NER on Hebrew fixtures."""

from pathlib import Path

import pytest

from kadima.engine.ner_extractor import NERExtractor
from kadima.engine.base import ProcessorStatus


_RAW_DIR = Path("tests/data/he_17_named_entities/raw")


def _load_fixture(name: str) -> str:
    return (_RAW_DIR / name).read_text(encoding="utf-8").strip()


def _run_heq_ner(text: str):
    result = NERExtractor().process(text, {"backend": "heq_ner", "device": "cpu"})
    if result.status != ProcessorStatus.READY:
        pytest.skip(f"M17 not ready: {result.error}")
    if result.data.backend != "heq_ner":
        pytest.skip(f"HeQ-NER unavailable in current environment: {result.data.note}")
    return result.data.entities


def test_gold_corpus_geo_entities_cover_multitoken_locations() -> None:
    entities = _run_heq_ner(_load_fixture("entities_geo.txt"))
    texts = {entity.text for entity in entities if entity.label in {"GPE", "LOC"}}
    assert any("תל אביב" in text for text in texts)
    assert any("דימונה" in text for text in texts)
    assert any("אילת" in text for text in texts)
    assert any("ירושלים" in text for text in texts)


def test_gold_corpus_org_entities_cover_anchor_organizations() -> None:
    entities = _run_heq_ner(_load_fixture("entities_org.txt"))
    org_texts = {entity.text for entity in entities if entity.label == "ORG"}
    assert any("הטכניון" in text for text in org_texts)
    assert any("משרד הביטחון" in text for text in org_texts)
    assert any("רפאל" in text for text in org_texts)
    assert any("התעשייה האווירית" in text for text in org_texts)


def test_gold_corpus_person_entities_keep_titles_and_person_names() -> None:
    entities = _run_heq_ner(_load_fixture("entities_person.txt"))
    labels = {entity.label for entity in entities}
    person_texts = {entity.text for entity in entities if entity.label == "PER"}
    assert "TTL" in labels
    assert any("כהן" in text for text in person_texts)
    assert any("לוי" in text for text in person_texts)
