# kadima/nlp/components/hebpipe_sent_splitter.py
"""spaCy component: Hebrew sentence splitting via HebPipe (M1).

Wraps kadima.engine.hebpipe_wrappers.HebPipeSentSplitter into a
spaCy pipeline component for integration with spaCy workflows.
"""

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from kadima.engine.hebpipe_wrappers import HebPipeSentSplitter


@Language.factory("kadima_sent_split")
class KadimaSentSplitter:
    """spaCy component for Hebrew sentence splitting.

    Uses HebPipeSentSplitter internally. Sets Doc.sents
    based on M1 output.
    """

    def __init__(self, nlp: Language, name: str = "kadima_sent_split"):
        self.nlp = nlp
        self.name = name
        self._splitter = HebPipeSentSplitter()

    def __call__(self, doc: Doc) -> Doc:
        """Process a spaCy Doc and set sentence boundaries."""
        result = self._splitter.process(doc.text, {})
        if result.data:
            for sent in result.data.sentences:
                # Find the token span and set is_sent_start
                for token in doc:
                    if token.idx == sent.start:
                        token.is_sent_start = True
                        break
        return doc
