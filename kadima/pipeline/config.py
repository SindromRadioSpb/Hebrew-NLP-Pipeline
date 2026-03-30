# kadima/pipeline/config.py
"""Pipeline configuration: Pydantic models + validated YAML loader."""

import os
import yaml
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────

class Profile(str, Enum):
    PRECISE = "precise"
    BALANCED = "balanced"
    RECALL = "recall"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


VALID_MODULES = frozenset([
    "sent_split", "tokenizer", "morph_analyzer", "ngram", "np_chunk",
    "canonicalize", "am", "term_extract", "noise",
])


# ── Sub-configs ──────────────────────────────────────────────────────────────

class AnnotationConfig(BaseModel):
    label_studio_url: str = "http://localhost:8080"
    label_studio_api_key: Optional[str] = None
    ml_backend_url: str = "http://localhost:9090"

    @field_validator("label_studio_url", "ml_backend_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Проверить что URL начинается с http:// или https://."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://, got: {v}")
        return v


class LLMConfig(BaseModel):
    enabled: bool = False
    server_url: str = "http://localhost:8081"
    model: str = "dictalm-3.0-1.7b-instruct"
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("server_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Проверить что URL начинается с http:// или https://."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://, got: {v}")
        return v


class KBConfig(BaseModel):
    enabled: bool = False
    embedding_model: str = "neodictabert"
    auto_generate_definitions: bool = False


class LoggingConfig(BaseModel):
    level: LogLevel = LogLevel.INFO
    file: Optional[str] = "~/.kadima/logs/kadima.log"


class StorageConfig(BaseModel):
    db_path: str = "~/.kadima/kadima.db"
    auto_backup: bool = True


# ── Profile thresholds ──────────────────────────────────────────────────────

class ThresholdsConfig(BaseModel):
    min_freq: int = Field(default=2, ge=1)
    pmi_threshold: float = Field(default=3.0, ge=0.0)
    hapax_filter: bool = True

    # Profile overrides
    precise: Optional[Dict[str, Any]] = None
    balanced: Optional[Dict[str, Any]] = None
    recall: Optional[Dict[str, Any]] = None

    def for_profile(self, profile: str | Profile) -> "ThresholdsConfig":
        """Return thresholds with profile-specific overrides applied."""
        profile_name = profile.value if isinstance(profile, Profile) else profile
        overrides = getattr(self, profile_name, None)
        if not overrides:
            return self
        base = self.model_dump(exclude_none=True)
        base.pop("precise", None)
        base.pop("balanced", None)
        base.pop("recall", None)
        base.update(overrides)
        return ThresholdsConfig(**base)


# ── Main config ──────────────────────────────────────────────────────────────

class PipelineConfig(BaseModel):
    language: str = "he"
    profile: Profile = Profile.BALANCED
    modules: List[str] = Field(default_factory=lambda: [
        "sent_split", "tokenizer", "morph_analyzer", "ngram", "np_chunk",
        "canonicalize", "am", "term_extract", "noise",
    ])
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    annotation: AnnotationConfig = Field(default_factory=AnnotationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    kb: KBConfig = Field(default_factory=KBConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Проверить что язык входит в допустимый список."""
        allowed = ("he", "heb", "hebrew", "iw")
        if v not in allowed:
            raise ValueError(f"language must be one of {allowed}, got: {v}")
        return v

    @field_validator("modules")
    @classmethod
    def validate_modules(cls, v: List[str]) -> List[str]:
        """Проверить что все модули из допустимого набора и список не пуст."""
        unknown = set(v) - VALID_MODULES
        if unknown:
            raise ValueError(
                f"Unknown modules: {unknown}. "
                f"Valid: {sorted(VALID_MODULES)}"
            )
        if not v:
            raise ValueError("modules list must not be empty")
        return v

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Module-specific configuration from resolved thresholds."""
        thresholds = self.thresholds.for_profile(self.profile)
        return {
            "ngram": {
                "min_n": 2, "max_n": 5,
                "min_freq": thresholds.min_freq,
            },
            "term_extract": {
                "profile": self.profile.value,
                "min_freq": thresholds.min_freq,
                "pmi_threshold": thresholds.pmi_threshold,
                "hapax_filter": thresholds.hapax_filter,
            },
            "noise": {
                "min_freq": thresholds.min_freq,
                "hapax_filter": thresholds.hapax_filter,
            },
        }.get(module_name, {})


# ── Loader ───────────────────────────────────────────────────────────────────

def load_config(path: Optional[str] = None) -> PipelineConfig:
    """Load and validate pipeline configuration from YAML.

    Args:
        path: Path to config.yaml. Defaults to ~/.kadima/config.yaml.

    Returns:
        Validated PipelineConfig instance.

    Raises:
        pydantic.ValidationError: If config contains invalid values.
        FileNotFoundError: If explicit path doesn't exist.
    """
    config_path = path or os.path.expanduser("~/.kadima/config.yaml")

    if not os.path.exists(config_path):
        logger.info("No config at %s, using defaults", config_path)
        return PipelineConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    p = raw.get("pipeline", raw)  # support both nested and flat formats

    config = PipelineConfig(
        language=p.get("language", "he"),
        profile=p.get("profile", "balanced"),
        modules=p.get("modules", PipelineConfig.model_fields["modules"].default),
        thresholds=p.get("thresholds", {}),
        annotation=raw.get("annotation", {}),
        llm=raw.get("llm", {}),
        kb=raw.get("kb", {}),
        logging=raw.get("logging", {}),
        storage=raw.get("storage", {}),
    )

    logger.info(
        "Config loaded: profile=%s, modules=%d, thresholds.min_freq=%d",
        config.profile.value, len(config.modules), config.thresholds.min_freq,
    )

    return config
