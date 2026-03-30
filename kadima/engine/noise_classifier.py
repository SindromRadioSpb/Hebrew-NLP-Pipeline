# kadima/engine/noise_classifier.py
"""M12: Noise Classifier — punct, number, latin, etc."""

import time
import re
from typing import Any, Dict, List
from dataclasses import dataclass

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
    """M12: Token noise classification.

    Classifies each token by noise type: Hebrew text, numbers, Latin text,
    punctuation, chemical formulas, quantities, math symbols.

    Attributes:
        Input: List[Token]
        Output: NoiseResult (List[NoiseLabel])

    Example:
        >>> from kadima.engine.noise_classifier import NoiseClassifier
        >>> from kadima.engine.hebpipe_wrappers import Token
        >>> clf = NoiseClassifier()
        >>> tokens = [Token(0,"חוזק",0,4), Token(1,"7.5",4,7), Token(2,"MPa",7,10)]
        >>> result = clf.process(tokens, {})
        >>> [l.noise_type for l in result.data.labels]
        ['non_noise', 'number', 'latin']
    """

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
