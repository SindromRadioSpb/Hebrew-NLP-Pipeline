"""Tests for M8 term extractor backends (T7-3)."""

import pytest
from kadima.engine.term_extractor_backends import (
    M8Backend,
    StatisticalBackend,
    AlephBERTBackend,
    ExtractedTerm,
    ExtractionResult,
    get_backend,
    list_backends,
    register_backend,
)


class TestExtractedTerm:
    def test_defaults(self):
        term = ExtractedTerm(surface="פלדה", canonical="פלדה")
        assert term.surface == "פלדה"
        assert term.kind == "UNKNOWN"
        assert term.freq == 1
        assert term.cluster_id == -1
        assert term.confidence == 0.0

    def test_with_values(self):
        term = ExtractedTerm(
            surface="חוזק מתיחה",
            canonical="חוזק מתיחה",
            kind="NOUN_NOUN",
            freq=5,
            pmi=4.2,
            confidence=0.95,
        )
        assert term.freq == 5
        assert term.confidence == 0.95


class TestExtractionResult:
    def test_defaults(self):
        result = ExtractionResult()
        assert result.terms == []
        assert result.backend == "statistical"
        assert result.model_version == ""

    def test_with_terms(self):
        terms = [
            ExtractedTerm(surface="פלדה", canonical="פלדה", freq=3),
            ExtractedTerm(surface="בטון", canonical="בטון", freq=2),
        ]
        result = ExtractionResult(terms=terms, total_candidates=10, filtered=2)
        assert len(result.terms) == 2
        assert result.total_candidates == 10


class TestStatisticalBackend:
    def test_backend_name(self):
        backend = StatisticalBackend()
        assert backend.backend_name == "statistical"

    def test_is_available(self):
        backend = StatisticalBackend()
        assert backend.is_available() is True

    def test_get_info(self):
        backend = StatisticalBackend()
        info = backend.get_info()
        assert info["name"] == "statistical"
        assert info["available"] is True
        assert "rule-based" in info["model_version"]

    def test_extract_returns_empty(self):
        backend = StatisticalBackend()
        result = backend.extract("test text", {})
        assert result.backend == "statistical"
        assert result.terms == []
        assert result.model_version == "rule-based"


class TestAlephBERTBackend:
    def test_backend_name(self):
        backend = AlephBERTBackend()
        assert backend.backend_name == "alephbert"

    def test_is_available_returns_bool(self):
        backend = AlephBERTBackend()
        result = backend.is_available()
        assert isinstance(result, bool)

    def test_get_info(self):
        backend = AlephBERTBackend()
        info = backend.get_info()
        assert info["name"] == "alephbert"
        assert isinstance(info["available"], bool)

    def test_extract_unavailable_returns_empty(self):
        """If model not loaded, should return empty result gracefully."""
        backend = AlephBERTBackend()
        if not backend.is_available():
            result = backend.extract("test", {})
            assert result.backend == "alephbert"
            assert result.terms == []


class TestRegistry:
    def test_get_backend_statistical(self):
        backend = get_backend("statistical")
        assert isinstance(backend, StatisticalBackend)

    def test_get_backend_alephbert(self):
        backend = get_backend("alephbert")
        assert isinstance(backend, AlephBERTBackend)

    def test_get_backend_invalid(self):
        with pytest.raises(ValueError, match="Unknown term extractor backend"):
            get_backend("invalid_backend")

    def test_list_backends(self):
        backends = list_backends()
        names = [b["name"] for b in backends]
        assert "statistical" in names
        assert "alephbert" in names

    def test_register_custom_backend(self):
        class CustomBackend(M8Backend):
            @property
            def backend_name(self):
                return "custom"

            def extract(self, text, config):
                return ExtractionResult(backend="custom")

            def is_available(self):
                return True

        register_backend(CustomBackend())
        backend = get_backend("custom")
        assert backend.backend_name == "custom"