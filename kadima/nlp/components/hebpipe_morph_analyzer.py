# kadima/nlp/components/hebpipe_morph_analyzer.py
"""spaCy component: Hebrew morphological analysis via HebPipe (M3).

Wraps kadima.engine.hebpipe_wrappers.HebPipeMorphAnalyzer into a
spaCy pipeline component.
"""

import logging

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from kadima.engine.hebpipe_wrappers import HebPipeMorphAnalyzer, Token

logger = logging.getLogger(__name__)


@Language.factory("kadima_morph")
class KadimaMorphAnalyzer:
    """spaCy component for Hebrew morphological analysis.

    Uses HebPipeMorphAnalyzer internally. Sets token morphological
    features via spaCy's morph attribute.
    """

    def __init__(self, nlp: Language, name: str = "kadima_morph"):
        self.nlp = nlp
        self.name = name
        self._analyzer = HebPipeMorphAnalyzer()

    def __call__(self, doc: Doc) -> Doc:
        """Process a spaCy Doc and set morphological attributes."""
        tokens = [
            Token(
                index=i,
                surface=token.text,
                start=token.idx,
                end=token.idx + len(token.text),
                is_punct=token.is_punct,
            )
            for i, token in enumerate(doc)
        ]
        result = self._analyzer.process(tokens, {})
        if result.data:
            for i, analysis in enumerate(result.data.analyses):
                if i < len(doc):
                    doc[i].lemma_ = analysis.lemma
                    doc[i].pos_ = self._map_pos(analysis.pos)
            logger.debug("Morph analyzed %d tokens", len(result.data.analyses))
        else:
            logger.warning("Morph analysis returned no data for %d tokens", len(tokens))
        return doc

    @staticmethod
    def _map_pos(pos: str) -> int:
        """Map Hebrew POS tag to spaCy POS tag."""
        from spacy.symbols import NOUN, VERB, ADJ, ADV, DET, ADP, CCONJ, SCONJ, PRON, NUM, PUNCT, PROPN, AUX
        mapping = {
            "NOUN": NOUN, "VERB": VERB, "ADJ": ADJ, "ADV": ADV,
            "DET": DET, "ADP": ADP, "CCONJ": CCONJ, "SCONJ": SCONJ,
            "PRON": PRON, "NUM": NUM, "PUNCT": PUNCT, "PROPN": PROPN,
            "AUX": AUX,
        }
        return mapping.get(pos, NOUN)
