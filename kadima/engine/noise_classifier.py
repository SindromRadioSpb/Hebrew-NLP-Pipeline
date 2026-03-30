# kadima/engine/noise_classifier.py
"""M12: Noise Classifier — punct, number, latin, etc."""

import time
import re
from typing import Any, Dict, List
from dataclasses import dataclass

import logging
from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import Token


@dataclass
class NoiseLabel:
    surface: str
    noise_type: str  # punct | number | latin | chemical | quantity | math | non_noise


@dataclass
class NoiseResult:
    labels: List[NoiseLabel]


class NoiseClassifier(Processor):
    """M12: Token noise classification."""

    @property
    def name(self) -> str:
        return "noise"

    @property
    def module_id(self) -> str:
        return "M12"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(isinstance(t, Token) for t in input_data)

    def process(self, input_data: List[Token], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            labels = []
            for token in input_data:
                surface = token.surface
                if re.match(r'^[\u0590-\u05FF]+$', surface):
                    labels.append(NoiseLabel(surface=surface, noise_type="non_noise"))
                elif re.match(r'^[0-9.,%]+$', surface):
                    labels.append(NoiseLabel(surface=surface, noise_type="number"))
                elif re.match(r'^[a-zA-Z]+$', surface):
                    labels.append(NoiseLabel(surface=surface, noise_type="latin"))
                elif re.match(r'^[^\w\s]+$', surface):
                    labels.append(NoiseLabel(surface=surface, noise_type="punct"))
                else:
                    labels.append(NoiseLabel(surface=surface, noise_type="non_noise"))

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=NoiseResult(labels=labels),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
