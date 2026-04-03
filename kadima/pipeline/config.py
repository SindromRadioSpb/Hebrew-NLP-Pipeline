# kadima/pipeline/config.py
"""Pipeline configuration: Pydantic models + validated YAML loader.

Provides strict config validation with:
- Pydantic v2 models with extra="forbid" (typos caught at load time)
- JSON Schema export for editor autocompletion and CI validation
- Profile-aware threshold resolution
- Module-specific config generation

Example:
    >>> from kadima.pipeline.config import load_config
    >>> config = load_config()  # loads ~/.kadima/config.yaml or defaults
    >>> config.profile
    <Profile.BALANCED: 'balanced'>
    >>> config.get_module_config("ngram")
    {'min_n': 2, 'max_n': 5, 'min_freq': 2}
"""

import os
import json
import yaml
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# Path to bundled default config
_DEFAULT_YAML = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "config.default.yaml"
)


# ── Enums ────────────────────────────────────────────────────────────────────

class Profile(str, Enum):
    """Профиль pipeline: баланс между точностью и полнотой."""

    PRECISE = "precise"
    BALANCED = "balanced"
    RECALL = "recall"


class LogLevel(str, Enum):
    """Уровень логирования."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


NLP_MODULES = frozenset([
    "sent_split", "tokenizer", "morph_analyzer", "ngram", "np_chunk",
    "canonicalize", "am", "term_extract", "noise",
])

GENERATIVE_MODULES = frozenset([
    "diacritizer", "translator", "tts", "stt", "ner", "sentiment",
    "summarizer", "qa", "morph_gen", "transliterator", "grammar",
    "keyphrase", "paraphrase",
])

VALID_MODULES = NLP_MODULES | GENERATIVE_MODULES


# ── Sub-configs ──────────────────────────────────────────────────────────────

class AnnotationConfig(BaseModel):
    """Конфигурация интеграции с Label Studio."""

    model_config = ConfigDict(extra="forbid")

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
    """Конфигурация LLM (llama.cpp, Dicta-LM)."""

    model_config = ConfigDict(extra="forbid")

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
    """Конфигурация Knowledge Base (embedding model, автогенерация)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    embedding_model: str = "neodictabert"
    auto_generate_definitions: bool = False


class LoggingConfig(BaseModel):
    """Конфигурация логирования: уровень и путь к файлу."""

    model_config = ConfigDict(extra="forbid")

    level: LogLevel = LogLevel.INFO
    file: Optional[str] = "~/.kadima/logs/kadima.log"


class StorageConfig(BaseModel):
    """Конфигурация хранилища: путь к БД, автобэкап."""

    model_config = ConfigDict(extra="forbid")

    db_path: str = "~/.kadima/kadima.db"
    auto_backup: bool = True


# ── Generative module configs (M13-M25) ────────────────────────────────────

class DeviceEnum(str, Enum):
    """Устройство для инференса."""

    CPU = "cpu"
    CUDA = "cuda"


class DiacritizerConfig(BaseModel):
    """M13: Дикритизация (никуд). backend: phonikud (ONNX) | dicta (transformers)."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="phonikud", pattern=r"^(phonikud|dicta)$")
    device: DeviceEnum = DeviceEnum.CUDA


class TranslatorConfig(BaseModel):
    """M14: Перевод. backend: mbart | opus | nllb."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="mbart", pattern=r"^(mbart|opus|nllb)$")
    device: DeviceEnum = DeviceEnum.CUDA
    default_tgt_lang: str = "en"


class TTSConfig(BaseModel):
    """M15: Синтез речи. backend: xtts | mms | piper."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="xtts", pattern=r"^(xtts|mms|piper)$")
    device: DeviceEnum = DeviceEnum.CUDA
    output_dir: str = "~/.kadima/audio"


class STTConfig(BaseModel):
    """M16: Распознавание речи. backend: whisper | faster_whisper."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="whisper", pattern=r"^(whisper|faster_whisper)$")
    device: DeviceEnum = DeviceEnum.CUDA
    model_size: str = Field(default="large-v3", pattern=r"^(tiny|base|small|medium|large-v[23])$")


class NERConfig(BaseModel):
    """M17: NER. backend: neodictabert | heq_ner | alephbert | hebert | rules."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="heq_ner", pattern=r"^(neodictabert|heq_ner|alephbert|hebert|rules)$")
    device: DeviceEnum = DeviceEnum.CUDA


class SentimentConfig(BaseModel):
    """M18: Анализ тональности. backend: hebert."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="hebert", pattern=r"^(hebert)$")
    device: DeviceEnum = DeviceEnum.CUDA


class SummarizerConfig(BaseModel):
    """M19: Суммаризация. backend: mt5."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="mt5", pattern=r"^(mt5)$")
    device: DeviceEnum = DeviceEnum.CUDA
    max_length: int = Field(default=150, ge=10, le=1024)
    min_length: int = Field(default=30, ge=5, le=512)


class QAConfig(BaseModel):
    """M20: Извлечение ответов. backend: alephbert."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="alephbert", pattern=r"^(alephbert)$")
    device: DeviceEnum = DeviceEnum.CUDA


class MorphGenConfig(BaseModel):
    """M21: Генерация морфологических форм (правила, без ML)."""

    model_config = ConfigDict(extra="forbid")

    gender: str = Field(default="masculine", pattern=r"^(masculine|feminine)$")
    binyan: str = Field(default="paal", pattern=r"^(paal|nifal|piel|pual|hifil|hufal|hitpael)$")


class TransliteratorConfig(BaseModel):
    """M22: Транслитерация (правила + lookup, без ML)."""

    model_config = ConfigDict(extra="forbid")

    mode: str = Field(default="latin", pattern=r"^(latin|male|haser|phonetic)$")


class GrammarConfig(BaseModel):
    """M23: Грамматическая коррекция. backend: llm | mt5."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="llm", pattern=r"^(llm|mt5)$")
    device: DeviceEnum = DeviceEnum.CUDA


class KeyphraseConfig(BaseModel):
    """M24: Извлечение ключевых фраз. backend: yake | keybert."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="yake", pattern=r"^(yake|keybert)$")
    top_n: int = Field(default=10, ge=1, le=100)
    language: str = "he"


class ParaphraseConfig(BaseModel):
    """M25: Парафраз. backend: mt5 | llm."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="mt5", pattern=r"^(mt5|llm)$")
    device: DeviceEnum = DeviceEnum.CUDA
    num_variants: int = Field(default=3, ge=1, le=10)


# ── Profile thresholds ──────────────────────────────────────────────────────

class ThresholdsOverrides(BaseModel):
    """Пороговые значения для конкретного профиля."""

    model_config = ConfigDict(extra="forbid")

    min_freq: Optional[int] = Field(default=None, ge=1)
    pmi_threshold: Optional[float] = Field(default=None, ge=0.0)
    hapax_filter: Optional[bool] = None
    min_n: Optional[int] = Field(default=None, ge=1, le=5)
    max_n: Optional[int] = Field(default=None, ge=1, le=10)
    np_mode: Optional[str] = Field(default=None, pattern=r"^(auto|rules|embeddings)$")
    np_sim_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    np_max_span: Optional[int] = Field(default=None, ge=1, le=10)
    term_mode: Optional[str] = Field(default=None, pattern=r"^(distinct|canonical|clustered|related)$")
    term_extractor_backend: Optional[str] = Field(default=None, pattern=r"^(statistical|alephbert)$")
    noise_filter_enabled: Optional[bool] = None
    pos_filter_enabled: Optional[bool] = None


class ThresholdsConfig(BaseModel):
    """Пороги pipeline: минимальная частота, PMI, фильтрация hapax, n-gram range, NP chunk settings."""

    model_config = ConfigDict(extra="forbid")

    min_freq: int = Field(default=2, ge=1)
    pmi_threshold: float = Field(default=3.0, ge=0.0)
    hapax_filter: bool = True
    min_n: int = Field(default=2, ge=1, le=5)
    max_n: int = Field(default=5, ge=1, le=10)
    np_mode: str = Field(default="auto", pattern=r"^(auto|rules|embeddings)$")
    np_sim_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    np_max_span: int = Field(default=4, ge=1, le=10)
    term_mode: str = Field(default="canonical", pattern=r"^(distinct|canonical|clustered|related)$")
    term_extractor_backend: str = Field(default="statistical", pattern=r"^(statistical|alephbert)$")
    noise_filter_enabled: bool = True
    pos_filter_enabled: bool = True

    # Profile overrides (schema-typed, not Dict[str, Any])
    precise: Optional[ThresholdsOverrides] = None
    balanced: Optional[ThresholdsOverrides] = None
    recall: Optional[ThresholdsOverrides] = None

    def for_profile(self, profile: str | Profile) -> "ThresholdsConfig":
        """Return thresholds with profile-specific overrides applied.

        Args:
            profile: Профиль (precise, balanced, recall).

        Returns:
            New ThresholdsConfig с перекрытыми значениями.
        """
        profile_name = profile.value if isinstance(profile, Profile) else profile
        overrides = getattr(self, profile_name, None)
        if not overrides:
            return self
        base = self.model_dump(exclude_none=True)
        base.pop("precise", None)
        base.pop("balanced", None)
        base.pop("recall", None)
        override_vals = overrides.model_dump(exclude_none=True)
        base.update(override_vals)
        return ThresholdsConfig(**base)


# ── Main config ──────────────────────────────────────────────────────────────

class PipelineConfig(BaseModel):
    """Основная конфигурация pipeline: язык, профиль, модули, пороги."""

    model_config = ConfigDict(extra="forbid")

    language: str = "he"
    profile: Profile = Profile.BALANCED
    modules: List[str] = Field(default_factory=lambda: [
        "sent_split", "tokenizer", "morph_analyzer", "ngram", "np_chunk",
        "canonicalize", "am", "term_extract", "noise",
    ])
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    # Generative module configs (M13-M25)
    diacritizer: DiacritizerConfig = Field(default_factory=DiacritizerConfig)
    translator: TranslatorConfig = Field(default_factory=TranslatorConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    ner: NERConfig = Field(default_factory=NERConfig)
    sentiment: SentimentConfig = Field(default_factory=SentimentConfig)
    summarizer: SummarizerConfig = Field(default_factory=SummarizerConfig)
    qa: QAConfig = Field(default_factory=QAConfig)
    morph_gen: MorphGenConfig = Field(default_factory=MorphGenConfig)
    transliterator: TransliteratorConfig = Field(default_factory=TransliteratorConfig)
    grammar: GrammarConfig = Field(default_factory=GrammarConfig)
    keyphrase: KeyphraseConfig = Field(default_factory=KeyphraseConfig)
    paraphrase: ParaphraseConfig = Field(default_factory=ParaphraseConfig)

    # Integration configs
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
        """Получить конфигурацию конкретного модуля с учётом профиля.

        Args:
            module_name: Имя модуля (sent_split, tokenizer, ...).

        Returns:
            Dict с параметрами модуля. Пустой dict если модуль не имеет
            специфических настроек.
        """
        thresholds = self.thresholds.for_profile(self.profile)
        profile = self.profile.value

        configs = {
            "sent_split": {
                "language": self.language,
            },
            "tokenizer": {
                "language": self.language,
            },
            "morph_analyzer": {
                "language": self.language,
            },
            "ngram": {
                "min_n": thresholds.min_n,
                "max_n": thresholds.max_n,
                "min_freq": thresholds.min_freq,
            },
            "np_chunk": {
                "language": self.language,
                "min_freq": thresholds.min_freq,
                "mode": thresholds.np_mode,
                "sim_threshold": thresholds.np_sim_threshold,
                "max_span": thresholds.np_max_span,
            },
            "canonicalize": {
                "language": self.language,
            },
            "am": {
                "min_freq": thresholds.min_freq,
            },
            "term_extract": {
                "profile": profile,
                "min_freq": thresholds.min_freq,
                "pmi_threshold": thresholds.pmi_threshold,
                "hapax_filter": thresholds.hapax_filter,
                "term_mode": thresholds.term_mode,
                "term_extractor_backend": thresholds.term_extractor_backend,
                "noise_filter_enabled": thresholds.noise_filter_enabled,
                "pos_filter_enabled": thresholds.pos_filter_enabled,
            },
            "noise": {
                "min_freq": thresholds.min_freq,
                "hapax_filter": thresholds.hapax_filter,
            },
        }

        if module_name in configs:
            return configs[module_name]

        # Generative modules — return sub-config as dict
        _generative_fields = {
            "diacritizer", "translator", "tts", "stt", "ner", "sentiment",
            "summarizer", "qa", "morph_gen", "transliterator", "grammar",
            "keyphrase", "paraphrase",
        }
        if module_name in _generative_fields:
            sub_config = getattr(self, module_name)
            return sub_config.model_dump()

        return {}


# ── Loader ───────────────────────────────────────────────────────────────────

def _load_yaml(path: str) -> Dict[str, Any]:
    """Загрузить YAML файл.

    Args:
        path: Путь к YAML файлу.

    Returns:
        Содержимое как dict.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: Optional[str] = None) -> PipelineConfig:
    """Загрузить и провалидировать конфигурацию pipeline из YAML.

    Поиск конфига (если path не указан):
      1. ~/.kadima/config.yaml
      2. config/config.default.yaml (бандлим)

    Args:
        path: Путь к config.yaml. Если None — автопоиск.

    Returns:
        Валидированный PipelineConfig.

    Raises:
        pydantic.ValidationError: Если значения невалидны.
        yaml.YAMLError: Если YAML синтаксически сломан.
    """
    user_path = os.path.expanduser("~/.kadima/config.yaml")

    if path:
        # Explicit path — must exist
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config not found: {path}")
        raw = _load_yaml(path)
        logger.info("Config loaded from explicit path: %s", path)
    elif os.path.exists(user_path):
        # User config
        raw = _load_yaml(user_path)
        logger.info("Config loaded from %s", user_path)
    elif os.path.exists(_DEFAULT_YAML):
        # Bundled default
        raw = _load_yaml(_DEFAULT_YAML)
        logger.info("User config not found, using bundled defaults: %s", _DEFAULT_YAML)
    else:
        # Pure defaults
        logger.info("No config files found, using hardcoded defaults")
        return PipelineConfig()

    p = raw.get("pipeline", raw)  # support both nested and flat formats

    # Collect generative module configs from top-level YAML sections
    generative_kwargs = {}
    for mod_name in GENERATIVE_MODULES:
        if mod_name in raw:
            generative_kwargs[mod_name] = raw[mod_name]

    config = PipelineConfig(
        language=p.get("language", "he"),
        profile=p.get("profile", "balanced"),
        modules=p.get("modules", PipelineConfig.model_fields["modules"].default),
        thresholds=p.get("thresholds", {}),
        **generative_kwargs,
        annotation=raw.get("annotation", {}),
        llm=raw.get("llm", {}),
        kb=raw.get("kb", {}),
        logging=raw.get("logging", {}),
        storage=raw.get("storage", {}),
    )

    logger.info(
        "Config validated: profile=%s, modules=%d, thresholds.min_freq=%d",
        config.profile.value, len(config.modules), config.thresholds.min_freq,
    )

    return config


# ── JSON Schema export ───────────────────────────────────────────────────────

def export_json_schema(pretty: bool = True) -> str:
    """Экспортировать JSON Schema всех конфигурационных моделей.

    Полезно для:
    - Editor autocompletion (VS Code YAML extension)
    - CI валидации config.yaml
    - Документации

    Args:
        pretty: Форматировать с отступами.

    Returns:
        JSON Schema как строка.
    """
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://kadima.dev/config.schema.json",
        "title": "KADIMA Pipeline Configuration",
        "description": "Configuration schema for KADIMA Hebrew NLP term extraction pipeline.",
        "type": "object",
        "properties": {
            "pipeline": PipelineConfig.model_json_schema(),
            "diacritizer": DiacritizerConfig.model_json_schema(),
            "translator": TranslatorConfig.model_json_schema(),
            "tts": TTSConfig.model_json_schema(),
            "stt": STTConfig.model_json_schema(),
            "ner": NERConfig.model_json_schema(),
            "sentiment": SentimentConfig.model_json_schema(),
            "summarizer": SummarizerConfig.model_json_schema(),
            "qa": QAConfig.model_json_schema(),
            "morph_gen": MorphGenConfig.model_json_schema(),
            "transliterator": TransliteratorConfig.model_json_schema(),
            "grammar": GrammarConfig.model_json_schema(),
            "keyphrase": KeyphraseConfig.model_json_schema(),
            "paraphrase": ParaphraseConfig.model_json_schema(),
            "annotation": AnnotationConfig.model_json_schema(),
            "llm": LLMConfig.model_json_schema(),
            "kb": KBConfig.model_json_schema(),
            "logging": LoggingConfig.model_json_schema(),
            "storage": StorageConfig.model_json_schema(),
        },
    }

    indent = 2 if pretty else None
    return json.dumps(schema, indent=indent, ensure_ascii=False)


def save_json_schema(path: str = "config/config.schema.json") -> None:
    """Сохранить JSON Schema в файл.

    Args:
        path: Путь для сохранения.
    """
    schema_str = export_json_schema()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(schema_str)
    logger.info("JSON Schema saved to %s", path)


def validate_config_file(path: str) -> List[str]:
    """Проверить YAML-конфиг без загрузки pipeline.

    Для использования в CI и pre-commit hooks.

    Args:
        path: Путь к config.yaml.

    Returns:
        Список ошибок (пустой если всё ок).
    """
    errors: List[str] = []

    if not os.path.exists(path):
        return [f"File not found: {path}"]

    try:
        raw = _load_yaml(path)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    try:
        p = raw.get("pipeline", raw)
        generative_kwargs = {}
        for mod_name in GENERATIVE_MODULES:
            if mod_name in raw:
                generative_kwargs[mod_name] = raw[mod_name]

        PipelineConfig(
            language=p.get("language", "he"),
            profile=p.get("profile", "balanced"),
            modules=p.get("modules", PipelineConfig.model_fields["modules"].default),
            thresholds=p.get("thresholds", {}),
            **generative_kwargs,
            annotation=raw.get("annotation", {}),
            llm=raw.get("llm", {}),
            kb=raw.get("kb", {}),
            logging=raw.get("logging", {}),
            storage=raw.get("storage", {}),
        )
    except Exception as e:
        errors.append(str(e))

    return errors
