# kadima/nlp/components/transformer_component.py
"""R-1.2: NeoDictaBERT transformer backbone для spaCy pipeline.

Загружает dicta-il/neodictabert через transformers, кладёт контекстные
embeddings (768-dim) в doc[i].vector для каждого токена.

Graceful degradation: если модель недоступна (нет VRAM, нет модели,
ImportError) — логирует warning и работает как no-op (R-1.4).

Example:
    >>> import spacy
    >>> nlp = spacy.blank("he")
    >>> nlp.add_pipe("kadima_transformer", first=True)
    >>> doc = nlp("שלום עולם")
    >>> doc[0].has_vector  # True если модель доступна
"""

import logging
from typing import Any, Optional

import numpy as np
import spacy
from spacy.language import Language
from spacy.tokens import Doc

logger = logging.getLogger(__name__)

_TRANSFORMERS_AVAILABLE = False
try:
    from transformers import AutoModel, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

_TORCH_AVAILABLE = False
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    pass

DEFAULT_MODEL = "dicta-il/neodictabert"
VECTOR_DIM = 768


@Language.factory(
    "kadima_transformer",
    default_config={
        "model_name": DEFAULT_MODEL,
        "max_length": 512,
        "device": "cpu",
        "fp16": False,
    },
)
class KadimaTransformer:
    """NeoDictaBERT transformer backbone для spaCy pipeline.

    Attributes:
        model_name: HuggingFace model ID.
        max_length: Max token length for transformer input.
        device: "cpu" или "cuda".
        fp16: Использовать half-precision (меньше VRAM).
    """

    def __init__(
        self,
        nlp: Language,
        name: str,
        model_name: str = DEFAULT_MODEL,
        max_length: int = 512,
        device: str = "cpu",
        fp16: bool = False,
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.device_str = device
        self.fp16 = fp16
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._loaded = False

        # Set custom extension for vector storage if not already set
        if not Doc.has_extension("transformer_data"):
            Doc.set_extension("transformer_data", default=None)

        self._try_load()

    def _try_load(self) -> None:
        """Attempt to load NeoDictaBERT. Falls back gracefully on any error (R-1.4)."""
        if not _TRANSFORMERS_AVAILABLE:
            logger.warning(
                "transformers not installed — KadimaTransformer will be a no-op. "
                "Install with: pip install transformers"
            )
            return
        if not _TORCH_AVAILABLE:
            logger.warning(
                "torch not installed — KadimaTransformer will be a no-op. "
                "Install with: pip install torch"
            )
            return

        try:
            device = self._resolve_device()
            logger.info("Loading transformer model: %s on %s", self.model_name, device)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            if self.fp16 and device != "cpu":
                self._model = self._model.half()
            self._model = self._model.to(device)
            self._model.eval()
            self._loaded = True
            logger.info("Transformer %s loaded successfully", self.model_name)
        except Exception as e:
            logger.warning(
                "NeoDictaBERT unavailable (%s). "
                "Pipeline will work without transformer embeddings.",
                e,
            )
            self._model = None
            self._tokenizer = None

    def _resolve_device(self) -> str:
        """Resolve device string, falling back to CPU if CUDA is unavailable."""
        if self.device_str == "cuda":
            if _TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            logger.warning("CUDA requested but unavailable — using CPU")
            return "cpu"
        return self.device_str

    @property
    def is_available(self) -> bool:
        """True if transformer model was loaded successfully."""
        return self._loaded and self._model is not None

    def __call__(self, doc: Doc) -> Doc:
        """Add transformer embeddings to doc tokens.

        If model is unavailable, returns doc unchanged (graceful degradation).

        Args:
            doc: spaCy Doc object.

        Returns:
            Doc with token vectors set (or unchanged if model unavailable).
        """
        if not self.is_available or not doc.text.strip():
            return doc

        try:
            vectors = self._get_token_vectors(doc)
            # Assign vectors to tokens via numpy array on doc
            # spaCy requires setting the entire tensor at once
            doc.tensor = vectors
            # Also store per-token: set user_data for easy access
            doc._.transformer_data = {
                "model": self.model_name,
                "shape": vectors.shape,
            }
        except Exception as e:
            logger.warning("Transformer inference failed for doc: %s", e)

        return doc

    def _get_token_vectors(self, doc: Doc) -> np.ndarray:
        """Run NeoDictaBERT on doc text, return per-token embeddings.

        Args:
            doc: spaCy Doc.

        Returns:
            float32 array of shape (n_tokens, VECTOR_DIM).
        """
        import torch

        text = doc.text
        encoding = self._tokenizer(
            text,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            return_offsets_mapping=True,
        )
        offset_mapping = encoding.pop("offset_mapping")[0].tolist()

        device = next(self._model.parameters()).device
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = self._model(**encoding)

        # Last hidden state: (1, seq_len, 768)
        hidden = outputs.last_hidden_state[0].cpu().float().numpy()

        # Map subword tokens → spaCy tokens by character offset
        n_tokens = len(doc)
        token_vectors = np.zeros((n_tokens, VECTOR_DIM), dtype=np.float32)
        counts = np.zeros(n_tokens, dtype=np.int32)

        for subword_idx, (char_start, char_end) in enumerate(offset_mapping):
            if char_start == char_end:  # special tokens
                continue
            for tok_idx, token in enumerate(doc):
                tok_start = token.idx
                tok_end = token.idx + len(token.text)
                # Overlap check
                if char_start < tok_end and char_end > tok_start:
                    token_vectors[tok_idx] += hidden[subword_idx]
                    counts[tok_idx] += 1

        # Average over subword tokens
        mask = counts > 0
        token_vectors[mask] /= counts[mask, np.newaxis]

        return token_vectors


def create_transformer_component(
    model_name: str = DEFAULT_MODEL,
    max_length: int = 512,
    device: str = "cpu",
    fp16: bool = False,
) -> "KadimaTransformer":
    """Factory function for creating a KadimaTransformer outside of spaCy.

    Args:
        model_name: HuggingFace model ID.
        max_length: Max token length.
        device: "cpu" or "cuda".
        fp16: Half precision.

    Returns:
        Configured KadimaTransformer instance.
    """
    nlp = spacy.blank("he")
    return KadimaTransformer(
        nlp=nlp,
        name="kadima_transformer",
        model_name=model_name,
        max_length=max_length,
        device=device,
        fp16=fp16,
    )
