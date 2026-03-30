# kadima/engine/base.py
"""Базовый интерфейс Processor ABC + PipelineResult dataclass."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ProcessorStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessorResult:
    """Результат работы одного Processor."""
    module_name: str
    status: ProcessorStatus
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class PipelineResult:
    """Результат полного pipeline run."""
    corpus_id: int
    profile: str
    module_results: Dict[str, ProcessorResult] = field(default_factory=dict)
    terms: List[Any] = field(default_factory=list)
    ngrams: List[Any] = field(default_factory=list)
    np_chunks: List[Any] = field(default_factory=list)
    total_time_ms: float = 0.0
    status: ProcessorStatus = ProcessorStatus.READY


class Processor(ABC):
    """Базовый интерфейс для всех модулей Engine Layer."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def module_id(self) -> str: ...

    @abstractmethod
    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult: ...

    def validate_input(self, input_data: Any) -> bool:
        return True

    def get_status(self) -> ProcessorStatus:
        return ProcessorStatus.READY
