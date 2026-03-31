"""Tests for kadima.nlp.components.transformer_component (R-1.2, R-1.3, R-1.4)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import spacy

# Register the factory before using it
import kadima.nlp.components.transformer_component  # noqa: F401
from kadima.nlp.components.transformer_component import (
    KadimaTransformer,
    VECTOR_DIM,
    DEFAULT_MODEL,
    create_transformer_component,
)
from kadima.nlp.pipeline import build_pipeline


# ── Metadata tests ──────────────────────────────────────────────────────────

class TestTransformerMetadata:
    def test_default_model_name(self):
        assert DEFAULT_MODEL == "dicta-il/neodictabert"

    def test_vector_dim(self):
        assert VECTOR_DIM == 768

    def test_factory_registered(self):
        """The 'kadima_transformer' factory must be registered in spaCy."""
        assert "kadima_transformer" in spacy.registry.factories


# ── Graceful degradation (R-1.4) ────────────────────────────────────────────

class TestGracefulDegradation:
    def test_no_crash_when_model_unavailable(self):
        """Pipeline must not crash when NeoDictaBERT cannot be loaded."""
        nlp = spacy.blank("he")
        with patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            side_effect=OSError("model not found"),
        ):
            transformer = KadimaTransformer(
                nlp=nlp,
                name="kadima_transformer",
                model_name="nonexistent/model",
                device="cpu",
            )
        assert not transformer.is_available

    def test_no_crash_when_transformers_missing(self):
        """Pipeline must work when transformers is not installed."""
        nlp = spacy.blank("he")
        with patch(
            "kadima.nlp.components.transformer_component._TRANSFORMERS_AVAILABLE",
            False,
        ):
            transformer = KadimaTransformer(
                nlp=nlp,
                name="kadima_transformer",
                model_name=DEFAULT_MODEL,
            )
        assert not transformer.is_available

    def test_noop_on_unavailable(self):
        """__call__ returns doc unchanged when model is unavailable."""
        nlp = spacy.blank("he")
        with patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            side_effect=RuntimeError("no VRAM"),
        ):
            transformer = KadimaTransformer(nlp=nlp, name="t", model_name="x")

        doc = nlp("שלום עולם")
        result = transformer(doc)
        assert result is doc  # returned unchanged

    def test_cuda_falls_back_to_cpu(self):
        """If CUDA requested but unavailable, uses CPU without crash."""
        nlp = spacy.blank("he")
        with patch(
            "kadima.nlp.components.transformer_component._TORCH_AVAILABLE",
            True,
        ), patch(
            "kadima.nlp.components.transformer_component.torch"
        ) as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            with patch(
                "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
                side_effect=RuntimeError("no VRAM"),
            ):
                transformer = KadimaTransformer(
                    nlp=nlp, name="t", model_name="x", device="cuda"
                )
        assert not transformer.is_available


# ── Pipeline builder (R-1.3) ────────────────────────────────────────────────

class TestPipelineBuilder:
    def test_build_without_transformer(self):
        """build_pipeline(use_transformer=False) is backward compatible."""
        nlp = build_pipeline(use_transformer=False)
        assert "kadima_transformer" not in nlp.pipe_names
        assert "kadima_sent_split" in nlp.pipe_names

    def test_build_with_transformer_adds_component(self):
        """build_pipeline(use_transformer=True) inserts transformer first."""
        with patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            side_effect=OSError("test"),
        ):
            nlp = build_pipeline(
                use_transformer=True,
                transformer_config={"model_name": "nonexistent/model"},
            )
        # Component added even if model failed to load (graceful degradation)
        assert "kadima_transformer" in nlp.pipe_names
        assert nlp.pipe_names[0] == "kadima_transformer"

    def test_build_with_transformer_no_crash_on_model_error(self):
        """Pipeline works end-to-end even when transformer model is unavailable."""
        with patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            side_effect=OSError("test"),
        ):
            nlp = build_pipeline(
                use_transformer=True,
                transformer_config={"model_name": "nonexistent/model"},
            )
        doc = nlp("שלום עולם")
        assert len(doc) > 0

    def test_build_default_components_present(self):
        """Default pipeline has sent_split and morph."""
        nlp = build_pipeline(use_transformer=False)
        assert "kadima_sent_split" in nlp.pipe_names
        assert "kadima_morph" in nlp.pipe_names


# ── KadimaTransformer with mocked model ─────────────────────────────────────

class TestTransformerWithMockedModel:
    """Tests using a fully mocked transformers stack to verify vector assignment."""

    def _make_transformer_with_mock(self) -> tuple:
        """Return (nlp, transformer, mock_model, mock_tokenizer)."""
        import torch

        nlp = spacy.blank("he")

        # Build a realistic mock tokenizer output
        mock_encoding = {
            "input_ids": torch.tensor([[1, 100, 200, 2]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]]),
        }
        mock_offset = torch.tensor([[0, 0], [0, 5], [6, 11], [0, 0]])

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {**mock_encoding, "offset_mapping": mock_offset.unsqueeze(0)}

        mock_hidden = torch.randn(1, 4, VECTOR_DIM)
        mock_output = MagicMock()
        mock_output.last_hidden_state = mock_hidden
        mock_model = MagicMock()
        mock_model.return_value = mock_output
        mock_model.to.return_value = mock_model  # chaining: model.to(device) returns model
        mock_model.parameters.return_value = iter([torch.zeros(1).to("cpu")])

        with patch(
            "kadima.nlp.components.transformer_component.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ), patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            return_value=mock_model,
        ):
            transformer = KadimaTransformer(
                nlp=nlp, name="kadima_transformer", model_name=DEFAULT_MODEL
            )

        return nlp, transformer, mock_model, mock_tokenizer

    def test_is_available_when_model_loaded(self):
        _, transformer, _, _ = self._make_transformer_with_mock()
        assert transformer.is_available

    def test_doc_tensor_set_after_call(self):
        """After __call__, doc.tensor should be a numpy array."""
        nlp, transformer, _, _ = self._make_transformer_with_mock()
        doc = nlp("שלום עולם")
        # manually call transformer
        result = transformer(doc)
        assert result is doc
        assert isinstance(doc.tensor, np.ndarray)

    def test_tensor_shape(self):
        """doc.tensor shape: (n_tokens, VECTOR_DIM)."""
        nlp, transformer, _, _ = self._make_transformer_with_mock()
        doc = nlp("שלום עולם")
        transformer(doc)
        assert doc.tensor.ndim == 2
        assert doc.tensor.shape[1] == VECTOR_DIM

    def test_transformer_data_extension(self):
        """doc._.transformer_data is set after inference."""
        nlp, transformer, _, _ = self._make_transformer_with_mock()
        doc = nlp("שלום עולם")
        transformer(doc)
        assert doc._.transformer_data is not None
        assert doc._.transformer_data["model"] == DEFAULT_MODEL


# ── Integration: full pipeline with mocked transformer ───────────────────────

class TestPipelineIntegration:
    def test_pipeline_processes_text_without_vectors(self):
        """Full pipeline run without transformer — backward compatible."""
        nlp = build_pipeline(use_transformer=False)
        doc = nlp("ברוך הבא לירושלים")
        assert len(doc) > 0

    def test_pipeline_with_transformer_no_vram(self):
        """Full pipeline run with transformer unavailable — no crash."""
        with patch(
            "kadima.nlp.components.transformer_component.AutoModel.from_pretrained",
            side_effect=RuntimeError("CUDA out of memory"),
        ):
            nlp = build_pipeline(
                use_transformer=True,
                transformer_config={"model_name": DEFAULT_MODEL},
            )
        doc = nlp("שלום עולם")
        assert len(doc) > 0
