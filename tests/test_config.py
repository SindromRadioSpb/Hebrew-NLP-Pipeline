"""Tests for kadima.pipeline.config (Pydantic validation)."""

import pytest
from pydantic import ValidationError
from kadima.pipeline.config import (
    PipelineConfig, ThresholdsConfig, LLMConfig, AnnotationConfig,
    KBConfig, LoggingConfig, StorageConfig, Profile, LogLevel,
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

    def test_missing_file_returns_defaults(self, tmp_path):
        config = load_config(str(tmp_path / "nonexistent.yaml"))
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
