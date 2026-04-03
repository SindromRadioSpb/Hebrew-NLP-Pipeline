"""Tests for kadima.pipeline.config (Pydantic validation)."""

import pytest
from pydantic import ValidationError
from kadima.pipeline.config import (
    PipelineConfig, ThresholdsConfig, LLMConfig, AnnotationConfig,
    KBConfig, LoggingConfig, StorageConfig, Profile, LogLevel,
    VALID_MODULES, NLP_MODULES, GENERATIVE_MODULES,
    DiacritizerConfig, TranslatorConfig, TTSConfig, STTConfig,
    NERConfig, SentimentConfig, SummarizerConfig, QAConfig,
    MorphGenConfig, TransliteratorConfig, GrammarConfig,
    KeyphraseConfig, ParaphraseConfig,
    load_config,
)


class TestDefaults:
    def test_default_config(self):
        c = PipelineConfig()
        assert c.language == "he"
        assert c.profile == Profile.BALANCED
        assert len(c.modules) == 9
        assert c.thresholds.min_freq == 2

    def test_default_annotation(self):
        c = PipelineConfig()
        assert c.annotation.label_studio_url == "http://localhost:8080"
        assert c.annotation.label_studio_api_key is None

    def test_default_llm(self):
        c = PipelineConfig()
        assert c.llm.enabled is False
        assert c.llm.temperature == 0.7
        assert c.llm.max_tokens == 512


class TestProfileValidation:
    def test_valid_profiles(self):
        for p in ("precise", "balanced", "recall"):
            c = PipelineConfig(profile=p)
            assert c.profile.value == p

    def test_invalid_profile(self):
        with pytest.raises(ValidationError, match="enum"):
            PipelineConfig(profile="invalid")

    def test_case_sensitive(self):
        with pytest.raises(ValidationError):
            PipelineConfig(profile="Balanced")


class TestModuleValidation:
    def test_valid_modules(self):
        c = PipelineConfig(modules=["sent_split", "ngram"])
        assert len(c.modules) == 2

    def test_unknown_module(self):
        with pytest.raises(ValidationError, match="Unknown modules"):
            PipelineConfig(modules=["sent_split", "fake_module"])

    def test_empty_modules(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            PipelineConfig(modules=[])


class TestThresholdsValidation:
    def test_valid_thresholds(self):
        t = ThresholdsConfig(min_freq=5, pmi_threshold=10.0)
        assert t.min_freq == 5

    def test_negative_min_freq(self):
        with pytest.raises(ValidationError):
            ThresholdsConfig(min_freq=-1)

    def test_zero_min_freq(self):
        with pytest.raises(ValidationError):
            ThresholdsConfig(min_freq=0)

    def test_negative_pmi(self):
        with pytest.raises(ValidationError):
            ThresholdsConfig(pmi_threshold=-1.0)


class TestLLMValidation:
    def test_valid_temperature(self):
        c = LLMConfig(temperature=0.0)
        assert c.temperature == 0.0
        c = LLMConfig(temperature=2.0)
        assert c.temperature == 2.0

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=5.0)
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

    def test_max_tokens_range(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=99999)

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            LLMConfig(server_url="ftp://bad")


class TestAnnotationValidation:
    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            AnnotationConfig(label_studio_url="not-a-url")


class TestLanguageValidation:
    def test_valid_languages(self):
        for lang in ("he", "heb", "hebrew", "iw"):
            c = PipelineConfig(language=lang)
            assert c.language == lang

    def test_invalid_language(self):
        with pytest.raises(ValidationError):
            PipelineConfig(language="en")


class TestProfileThresholds:
    def test_profile_override(self):
        t = ThresholdsConfig(
            min_freq=2,
            pmi_threshold=3.0,
            precise={"min_freq": 5, "pmi_threshold": 7.0},
        )
        resolved = t.for_profile("precise")
        assert resolved.min_freq == 5
        assert resolved.pmi_threshold == 7.0

    def test_no_override_returns_self(self):
        t = ThresholdsConfig(min_freq=2)
        resolved = t.for_profile("balanced")
        assert resolved.min_freq == 2

    def test_partial_override(self):
        t = ThresholdsConfig(
            min_freq=2,
            pmi_threshold=3.0,
            recall={"min_freq": 1},
        )
        resolved = t.for_profile("recall")
        assert resolved.min_freq == 1
        assert resolved.pmi_threshold == 3.0  # unchanged


class TestLoadConfig:
    def test_load_default_yaml(self, tmp_path):
        config = load_config("config/config.default.yaml")
        assert config.profile == Profile.BALANCED
        assert len(config.modules) == 9
        assert config.annotation.label_studio_url == "http://localhost:8080"
        assert config.logging.level == LogLevel.INFO

    def test_missing_file_raises(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_no_path_returns_defaults(self):
        # When no path given and no user config exists, returns defaults
        config = load_config()
        assert config.language == "he"
        assert config.profile == Profile.BALANCED

    def test_custom_config(self, tmp_path):
        import yaml
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text(yaml.dump({
            "pipeline": {
                "profile": "precise",
                "thresholds": {"min_freq": 5},
            },
            "llm": {"enabled": True, "temperature": 1.5},
        }))
        config = load_config(str(cfg_path))
        assert config.profile == Profile.PRECISE
        assert config.thresholds.min_freq == 5
        assert config.llm.enabled is True
        assert config.llm.temperature == 1.5

    def test_invalid_config_raises(self, tmp_path):
        import yaml
        cfg_path = tmp_path / "bad.yaml"
        cfg_path.write_text(yaml.dump({"pipeline": {"profile": "invalid"}}))
        with pytest.raises(ValidationError):
            load_config(str(cfg_path))


class TestLoggingConfig:
    def test_valid_levels(self):
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            c = LoggingConfig(level=level)
            assert c.level.value == level

    def test_invalid_level(self):
        with pytest.raises(ValidationError):
            LoggingConfig(level="VERBOSE")


class TestGetModuleConfig:
    def test_known_modules(self):
        c = PipelineConfig()
        for mod in ("ngram", "term_extract", "noise"):
            cfg = c.get_module_config(mod)
            assert isinstance(cfg, dict)
            assert "min_freq" in cfg

    def test_unknown_module_returns_empty(self):
        c = PipelineConfig()
        assert c.get_module_config("unknown") == {}

    def test_profile_applied(self):
        c = PipelineConfig(profile="precise", thresholds={
            "min_freq": 2,
            "precise": {"min_freq": 10},
        })
        cfg = c.get_module_config("term_extract")
        assert cfg["min_freq"] == 10  # precise override


class TestValidModulesConstants:
    def test_nlp_modules_count(self):
        assert len(NLP_MODULES) == 9

    def test_generative_modules_count(self):
        assert len(GENERATIVE_MODULES) == 13

    def test_valid_modules_is_union(self):
        assert VALID_MODULES == NLP_MODULES | GENERATIVE_MODULES

    def test_no_overlap(self):
        assert NLP_MODULES & GENERATIVE_MODULES == set()

    def test_generative_module_names(self):
        expected = {
            "diacritizer", "translator", "tts", "stt", "ner", "sentiment",
            "summarizer", "qa", "morph_gen", "transliterator", "grammar",
            "keyphrase", "paraphrase",
        }
        assert GENERATIVE_MODULES == expected


class TestGenerativeModuleValidation:
    def test_generative_modules_accepted(self):
        """All generative module names pass validation in modules list."""
        for mod in GENERATIVE_MODULES:
            c = PipelineConfig(modules=["sent_split", mod])
            assert mod in c.modules

    def test_all_modules_combined(self):
        c = PipelineConfig(modules=sorted(VALID_MODULES))
        assert len(c.modules) == 22


class TestDiacritizerConfig:
    def test_defaults(self):
        c = DiacritizerConfig()
        assert c.backend == "phonikud"
        assert c.device == "cuda"

    def test_valid_backends(self):
        for b in ("phonikud", "dicta"):
            c = DiacritizerConfig(backend=b)
            assert c.backend == b

    def test_invalid_backend(self):
        with pytest.raises(ValidationError):
            DiacritizerConfig(backend="invalid")

    def test_cpu_device(self):
        c = DiacritizerConfig(device="cpu")
        assert c.device == "cpu"

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            DiacritizerConfig(extra_field="bad")


class TestTranslatorConfig:
    def test_defaults(self):
        c = TranslatorConfig()
        assert c.backend == "mbart"
        assert c.default_tgt_lang == "en"

    def test_valid_backends(self):
        for b in ("mbart", "opus", "nllb"):
            c = TranslatorConfig(backend=b)
            assert c.backend == b

    def test_invalid_backend(self):
        with pytest.raises(ValidationError):
            TranslatorConfig(backend="deepl")


class TestSTTConfig:
    def test_defaults(self):
        c = STTConfig()
        assert c.backend == "auto"
        assert c.model_size == "large-v3"

    def test_valid_backends(self):
        for backend in ("auto", "whisper", "faster-whisper"):
            c = STTConfig(backend=backend)
            assert c.backend == backend

    def test_valid_model_sizes(self):
        for s in ("tiny", "base", "small", "medium", "large-v2", "large-v3"):
            c = STTConfig(model_size=s)
            assert c.model_size == s

    def test_invalid_model_size(self):
        with pytest.raises(ValidationError):
            STTConfig(model_size="huge")

    def test_invalid_backend(self):
        with pytest.raises(ValidationError):
            STTConfig(backend="faster_whisper")


class TestSummarizerConfig:
    def test_defaults(self):
        c = SummarizerConfig()
        assert c.max_length == 150
        assert c.min_length == 30

    def test_length_bounds(self):
        with pytest.raises(ValidationError):
            SummarizerConfig(max_length=5)
        with pytest.raises(ValidationError):
            SummarizerConfig(min_length=2)


class TestMorphGenConfig:
    def test_defaults(self):
        c = MorphGenConfig()
        assert c.gender == "masculine"
        assert c.binyan == "paal"

    def test_valid_binyanim(self):
        for b in ("paal", "nifal", "piel", "pual", "hifil", "hufal", "hitpael"):
            c = MorphGenConfig(binyan=b)
            assert c.binyan == b

    def test_invalid_binyan(self):
        with pytest.raises(ValidationError):
            MorphGenConfig(binyan="invalid")


class TestKeyphraseConfig:
    def test_defaults(self):
        c = KeyphraseConfig()
        assert c.top_n == 10
        assert c.language == "he"

    def test_top_n_bounds(self):
        with pytest.raises(ValidationError):
            KeyphraseConfig(top_n=0)
        with pytest.raises(ValidationError):
            KeyphraseConfig(top_n=200)


class TestParaphraseConfig:
    def test_defaults(self):
        c = ParaphraseConfig()
        assert c.num_variants == 3

    def test_num_variants_bounds(self):
        with pytest.raises(ValidationError):
            ParaphraseConfig(num_variants=0)
        with pytest.raises(ValidationError):
            ParaphraseConfig(num_variants=20)


class TestGetGenerativeModuleConfig:
    def test_diacritizer_config(self):
        c = PipelineConfig()
        cfg = c.get_module_config("diacritizer")
        assert cfg["backend"] == "phonikud"
        assert "device" in cfg

    def test_translator_config(self):
        c = PipelineConfig()
        cfg = c.get_module_config("translator")
        assert cfg["backend"] == "mbart"
        assert cfg["default_tgt_lang"] == "en"

    def test_keyphrase_config(self):
        c = PipelineConfig()
        cfg = c.get_module_config("keyphrase")
        assert cfg["backend"] == "yake"
        assert cfg["top_n"] == 10

    def test_custom_generative_config(self):
        c = PipelineConfig(diacritizer={"backend": "dicta", "device": "cpu"})
        cfg = c.get_module_config("diacritizer")
        assert cfg["backend"] == "dicta"
        assert cfg["device"] == "cpu"

    def test_all_generative_return_nonempty(self):
        c = PipelineConfig()
        for mod in GENERATIVE_MODULES:
            cfg = c.get_module_config(mod)
            assert isinstance(cfg, dict)
            assert len(cfg) > 0, f"{mod} returned empty config"


class TestLoadConfigGenerative:
    def test_load_default_yaml_with_generative(self):
        config = load_config("config/config.default.yaml")
        assert config.diacritizer.backend == "phonikud"
        assert config.translator.backend == "mbart"
        assert config.keyphrase.top_n == 10
        assert config.paraphrase.num_variants == 3

    def test_custom_yaml_with_generative(self, tmp_path):
        import yaml
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text(yaml.dump({
            "pipeline": {"profile": "balanced"},
            "diacritizer": {"backend": "dicta", "device": "cpu"},
            "keyphrase": {"backend": "keybert", "top_n": 5, "language": "he"},
        }))
        config = load_config(str(cfg_path))
        assert config.diacritizer.backend == "dicta"
        assert config.diacritizer.device == "cpu"
        assert config.keyphrase.backend == "keybert"
        assert config.keyphrase.top_n == 5


class TestCoreDependencies:
    """R-1.1: Verify core NLP dependencies are importable (spacy-transformers, transformers)."""

    def test_spacy_importable(self):
        import spacy
        assert spacy.__version__

    def test_transformers_importable(self):
        """transformers is now a core dependency (R-1.1)."""
        import transformers
        assert transformers.__version__

    def test_spacy_transformers_importable(self):
        """spacy-transformers is now a core dependency (R-1.1)."""
        import spacy_transformers  # noqa: F401 — import itself is the assertion
        import importlib.metadata
        version = importlib.metadata.version("spacy-transformers")
        assert version

    def test_numpy_importable(self):
        """numpy is now a core dependency (R-1.5)."""
        import numpy as np
        assert np.__version__

    def test_scipy_importable(self):
        """scipy is now a core dependency (R-1.5)."""
        import scipy
        assert scipy.__version__

    def test_pandas_importable(self):
        """pandas is now a core dependency (R-1.5)."""
        import pandas as pd
        assert pd.__version__
