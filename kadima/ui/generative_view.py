# kadima/ui/generative_view.py
"""GenerativeView — 6-tab view for on-demand generative NLP modules.

Tabs: Sentiment (M18) · TTS (M15) · STT (M16) · Translate (M14) ·
      Diacritize (M13) · NER (M17)

Threading: GenerativeWorker(QRunnable) via QThreadPool.globalInstance().
All engine imports are lazy and wrapped in try/except ImportError.
"""
from __future__ import annotations

import csv
import logging
import shutil
import traceback
from pathlib import Path
from typing import Any, Optional

try:
    from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QProgressBar,
        QPushButton,
        QSizePolicy,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_TTS_VOICE_MODE_DEFAULT = "default"
_TTS_VOICE_MODE_PRESET = "preset"
_TTS_VOICE_MODE_CLONE = "clone"

# ---------------------------------------------------------------------------
# Engine module lazy imports — one block per module
# ---------------------------------------------------------------------------

try:
    from kadima.engine.sentiment_analyzer import SentimentAnalyzer as _SentimentCls
except ImportError:
    _SentimentCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.tts_synthesizer import (
        TTSSynthesizer as _TTSCls,
        get_f5tts_voice_presets_dir as _get_f5tts_voice_presets_dir,
        list_f5tts_voice_presets as _list_f5tts_voice_presets,
    )
except ImportError:
    _TTSCls = None  # type: ignore[assignment,misc]
    _get_f5tts_voice_presets_dir = None  # type: ignore[assignment,misc]
    _list_f5tts_voice_presets = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.stt_transcriber import STTTranscriber as _STTCls
except ImportError:
    _STTCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.translator import Translator as _TranslatorCls
except ImportError:
    _TranslatorCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.diacritizer import Diacritizer as _DiacrCls
except ImportError:
    _DiacrCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.ner_extractor import NERExtractor as _NERCls
except ImportError:
    _NERCls = None  # type: ignore[assignment,misc]

# Widget imports — also lazy
try:
    from kadima.ui.widgets.backend_selector import BackendSelector
    from kadima.ui.widgets.rtl_text_edit import RTLTextEdit
    from kadima.ui.widgets.entity_table import EntityTable
    from kadima.ui.widgets.audio_player import AudioPlayer

    _HAS_WIDGETS = True
except ImportError:
    _HAS_WIDGETS = False


# ---------------------------------------------------------------------------
# GenerativeWorker
# ---------------------------------------------------------------------------


class _WorkerSignals(QObject):
    """Signals emitted by GenerativeWorker.

    Must be a QObject subclass — QRunnable cannot carry signals directly.
    """

    started = pyqtSignal(str)           # tab_name
    finished = pyqtSignal(str, object)  # (tab_name, ProcessorResult)
    failed = pyqtSignal(str, str)       # (tab_name, error_msg)


class GenerativeWorker(QRunnable):
    """Runs a single generative module in QThreadPool.

    Args:
        tab_name: Identifier used in all emitted signals.
        module_cls: Engine class to instantiate (e.g. SentimentAnalyzer).
        module_config: Dict passed to module constructor.
        input_data: Input value forwarded to ``module.process()``.
        runtime_config: Dict forwarded as the second arg to ``module.process()``.
    """

    def __init__(
        self,
        tab_name: str,
        module_cls: Any,
        module_config: dict[str, Any],
        input_data: Any,
        runtime_config: dict[str, Any],
    ) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self.tab_name = tab_name
        self._module_cls = module_cls
        self._module_config = module_config
        self._input_data = input_data
        self._runtime_config = runtime_config
        self.signals = _WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        """Entry point — executed in a worker thread by QThreadPool."""
        self.signals.started.emit(self.tab_name)
        try:
            import inspect
            init_params = inspect.signature(self._module_cls.__init__).parameters
            if len(init_params) > 1:  # has params beyond 'self'
                module = self._module_cls(self._module_config)
            else:
                module = self._module_cls()
            result = module.process(self._input_data, self._runtime_config)
            self.signals.finished.emit(self.tab_name, result)
        except Exception as exc:
            logger.error(
                "GenerativeWorker[%s] error: %s\n%s",
                self.tab_name,
                exc,
                traceback.format_exc(),
            )
            self.signals.failed.emit(self.tab_name, str(exc))


# ---------------------------------------------------------------------------
# GenerativeView
# ---------------------------------------------------------------------------


class GenerativeView(QWidget):
    """Six-tab view for generative NLP modules (M13/M14/M15/M16/M17/M18).

    Signals:
        generative_finished_signal(str, object):
            Forwarded from any worker's finished signal.
            Arguments: (tab_name, ProcessorResult).
    """

    generative_finished_signal = pyqtSignal(str, object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("generative_view")
        self._pool = QThreadPool.globalInstance()
        self._tts_refreshing_voice_controls = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("Generative Modules")
        title.setObjectName("generative_title")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("generative_tabs")
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #3d3d5c; border-radius: 4px; }"
            "QTabBar::tab { background: #2d2d44; color: #a0a0c0; padding: 6px 14px; }"
            "QTabBar::tab:selected { background: #1e1e2e; color: #e0e0e0; }"
            "QTabBar::tab:hover { color: #c0c0e0; }"
        )
        root.addWidget(self._tabs)

        self._tabs.addTab(self._build_sentiment_tab(), "Sentiment")
        self._tabs.addTab(self._build_tts_tab(), "TTS")
        self._tabs.addTab(self._build_stt_tab(), "STT")
        self._tabs.addTab(self._build_translate_tab(), "Translate")
        self._tabs.addTab(self._build_diacritize_tab(), "Diacritize")
        self._tabs.addTab(self._build_ner_tab(), "NER")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_tab_container() -> tuple[QWidget, QVBoxLayout]:
        """Return (widget, layout) for a tab page."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        return w, lay

    @staticmethod
    def _make_button_row(
        run_label: str = "Run",
        clear_label: str = "Clear",
        copy_label: str | None = "Copy",
        export_label: str | None = None,
    ) -> tuple[QHBoxLayout, QPushButton, QPushButton, QPushButton | None, QPushButton | None]:
        """Build a standard button row and return (layout, run, clear, copy, export)."""
        row = QHBoxLayout()
        run_btn = QPushButton(run_label)
        run_btn.setFixedHeight(30)
        clear_btn = QPushButton(clear_label)
        clear_btn.setFixedHeight(30)
        row.addWidget(run_btn)
        row.addWidget(clear_btn)
        row.addStretch()

        copy_btn: QPushButton | None = None
        if copy_label:
            copy_btn = QPushButton(copy_label)
            copy_btn.setFixedHeight(30)
            row.addWidget(copy_btn)

        export_btn: QPushButton | None = None
        if export_label:
            export_btn = QPushButton(export_label)
            export_btn.setFixedHeight(30)
            row.addWidget(export_btn)

        return row, run_btn, clear_btn, copy_btn, export_btn

    @staticmethod
    def _make_status_label(initial: str = "Ready") -> QLabel:
        lbl = QLabel(initial)
        lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return lbl

    @staticmethod
    def _copy_text_to_clipboard(text: str) -> None:
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(text)

    # ------------------------------------------------------------------
    # Tab 0 — Sentiment
    # ------------------------------------------------------------------

    def _build_sentiment_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        self._sentiment_backend = BackendSelector(
            backends=["rules", "hebert"], default_backend="rules"
        )
        self._sentiment_backend.setObjectName("generative_sentiment_backend")
        lay.addWidget(self._sentiment_backend)

        self._sentiment_input = RTLTextEdit(placeholder="הכנס טקסט...")
        self._sentiment_input.setObjectName("generative_sentiment_input")
        self._sentiment_input.setMaximumHeight(120)
        lay.addWidget(self._sentiment_input)

        btn_row, run_btn, clear_btn, copy_btn, _ = self._make_button_row(
            run_label="Analyze Sentiment", copy_label=None
        )
        run_btn.setObjectName("generative_sentiment_run_btn")
        clear_btn.setObjectName("generative_sentiment_clear_btn")
        if _SentimentCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("SentimentAnalyzer not available (install [ml] extras)")
        lay.addLayout(btn_row)

        self._sentiment_result_lbl = QLabel("—")
        self._sentiment_result_lbl.setObjectName("generative_sentiment_result")
        self._sentiment_result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sentiment_result_lbl.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #a0a0c0; padding: 12px;"
        )
        lay.addWidget(self._sentiment_result_lbl)
        lay.addStretch()

        self._sentiment_status = self._make_status_label()
        self._sentiment_status.setObjectName("generative_sentiment_status")
        lay.addWidget(self._sentiment_status)

        # Connections
        run_btn.clicked.connect(self._on_sentiment_run)
        clear_btn.clicked.connect(self._on_sentiment_clear)

        return w

    def _on_sentiment_run(self) -> None:
        text = self._sentiment_input.toPlainText().strip()
        if not text or _SentimentCls is None:
            return
        backend = self._sentiment_backend.backend
        device = self._sentiment_backend.device
        worker = GenerativeWorker(
            tab_name="sentiment",
            module_cls=_SentimentCls,
            module_config={},
            input_data=text,
            runtime_config={"backend": backend, "device": device},
        )
        worker.signals.started.connect(
            lambda t: self._sentiment_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_sentiment_result)
        worker.signals.failed.connect(
            lambda t, e: self._sentiment_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_sentiment_result(self, tab_name: str, result: Any) -> None:
        self._sentiment_status.setText("Done")
        self.generative_finished_signal.emit(tab_name, result)
        try:
            label = getattr(result.data, "label", "unknown") if result.data else "unknown"
            score = getattr(result.data, "score", 0.0) if result.data else 0.0
            text = f"{label.capitalize()} ({score:.2f})"
            colour_map = {
                "positive": "#22c55e",
                "negative": "#ef4444",
                "neutral": "#a0a0c0",
            }
            colour = colour_map.get(label.lower(), "#a0a0c0")
            self._sentiment_result_lbl.setText(text)
            self._sentiment_result_lbl.setStyleSheet(
                f"font-size: 24px; font-weight: bold; color: {colour}; padding: 12px;"
            )
        except Exception as exc:
            logger.warning("sentiment result display error: %s", exc)
            self._sentiment_status.setText(f"Display error: {exc}")

    def _on_sentiment_clear(self) -> None:
        self._sentiment_input.clear()
        self._sentiment_result_lbl.setText("—")
        self._sentiment_result_lbl.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #a0a0c0; padding: 12px;"
        )
        self._sentiment_status.setText("Ready")

    # ------------------------------------------------------------------
    # Tab 1 — TTS
    # ------------------------------------------------------------------

    def _build_tts_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        tts_backends = ["auto", "f5tts", "lightblue", "phonikud", "mms"]
        self._tts_backend = BackendSelector(
            backends=tts_backends, default_backend="auto"
        )
        self._tts_backend.setObjectName("generative_tts_backend")
        lay.addWidget(self._tts_backend)
        self._tts_backend.changed.connect(lambda _backend, _device: self._on_tts_backend_changed())

        # Help text explaining backend differences
        help_text = QLabel(
            "🔊 Backends: "
            "<b>auto</b>=F5-TTS → LightBlue → Phonikud → MMS, "
            "<b>f5tts</b>=best quality + cloning (reference WAV or local preset voices), "
            "<b>lightblue</b>=fast CPU ONNX, "
            "<b>phonikud</b>=Hebrew Piper ONNX, "
            "<b>mms</b>=last-resort fallback"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #8888aa; font-size: 11px; padding: 4px 8px; "
                                "background: #1a1a2e; border-radius: 4px;")
        lay.addWidget(help_text)

        self._tts_language_hint = QLabel("Language: Hebrew only in the current prototype")
        self._tts_language_hint.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(self._tts_language_hint)

        # ML availability badges
        badges_row = QHBoxLayout()
        self._tts_f5tts_badge = QLabel("⬜ f5tts")
        self._tts_lightblue_badge = QLabel("⬜ lightblue")
        self._tts_phonikud_badge = QLabel("⬜ phonikud")
        self._tts_mms_badge = QLabel("⬜ mms")
        for badge in [
            self._tts_f5tts_badge,
            self._tts_lightblue_badge,
            self._tts_phonikud_badge,
            self._tts_mms_badge,
        ]:
            badge.setStyleSheet("color: #a0a0c0; font-size: 10px;")
            badges_row.addWidget(badge)
        badges_row.addStretch()
        lay.addLayout(badges_row)

        # Update badges based on available backends
        self._update_tts_ml_badges()

        # Input text with counters
        input_row = QHBoxLayout()
        self._tts_input = RTLTextEdit(placeholder="הכנס טקסט לסינתזה...")
        self._tts_input.setObjectName("generative_tts_input")
        self._tts_input.setMaximumHeight(120)
        input_row.addWidget(self._tts_input, stretch=1)

        # Char/word counters column
        counter_col = QVBoxLayout()
        self._tts_char_count = QLabel("0 chars")
        self._tts_char_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._tts_char_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._tts_char_count)

        self._tts_word_count = QLabel("0 words")
        self._tts_word_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._tts_word_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._tts_word_count)
        counter_col.addStretch()
        input_row.addLayout(counter_col)
        lay.addLayout(input_row)

        # Wire text change signal for counters
        self._tts_input.textChanged.connect(self._on_tts_input_changed)

        # Voice cloning controls
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Voice mode:")
        mode_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        mode_row.addWidget(mode_lbl)

        self._tts_voice_mode = QComboBox()
        self._tts_voice_mode.setObjectName("generative_tts_voice_mode")
        self._tts_voice_mode.currentIndexChanged.connect(self._on_tts_voice_mode_changed)
        mode_row.addWidget(self._tts_voice_mode, stretch=1)
        lay.addLayout(mode_row)

        vc_row = QHBoxLayout()
        self._tts_voice_clone_check = QLabel("Reference WAV:")
        self._tts_voice_clone_check.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        vc_row.addWidget(self._tts_voice_clone_check)

        self._tts_speaker_ref_input = QLineEdit()
        self._tts_speaker_ref_input.setObjectName("generative_tts_speaker_ref")
        self._tts_speaker_ref_input.setPlaceholderText("Path to speaker reference WAV (2-3 sec)...")
        self._tts_speaker_ref_input.setReadOnly(True)
        vc_row.addWidget(self._tts_speaker_ref_input, stretch=1)

        self._tts_speaker_browse_btn = QPushButton("Browse...")
        self._tts_speaker_browse_btn.setObjectName("generative_tts_speaker_browse_btn")
        self._tts_speaker_browse_btn.setFixedWidth(80)
        self._tts_speaker_browse_btn.clicked.connect(self._on_tts_speaker_browse)
        vc_row.addWidget(self._tts_speaker_browse_btn)
        lay.addLayout(vc_row)

        voice_row = QHBoxLayout()
        voice_lbl = QLabel("Voice:")
        voice_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        voice_row.addWidget(voice_lbl)
        self._tts_voice_input = QComboBox()
        self._tts_voice_input.setObjectName("generative_tts_voice")
        self._tts_voice_input.currentIndexChanged.connect(self._on_tts_voice_selection_changed)
        voice_row.addWidget(self._tts_voice_input, stretch=1)
        lay.addLayout(voice_row)

        self._tts_voice_hint = QLabel("")
        self._tts_voice_hint.setWordWrap(True)
        self._tts_voice_hint.setStyleSheet("color: #8888aa; font-size: 11px;")
        lay.addWidget(self._tts_voice_hint)

        btn_row, run_btn, clear_btn, _, export_btn = self._make_button_row(
            run_label="Synthesize", copy_label=None, export_label="Save WAV..."
        )
        run_btn.setObjectName("generative_tts_run_btn")
        clear_btn.setObjectName("generative_tts_clear_btn")
        if export_btn is not None:
            export_btn.setObjectName("generative_tts_export_btn")
            export_btn.setEnabled(False)
            self._tts_export_btn = export_btn
        if _TTSCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("TTSSynthesizer not available (install [gpu] extras)")
        lay.addLayout(btn_row)

        self._tts_progress = QProgressBar()
        self._tts_progress.setObjectName("generative_tts_progress")
        self._tts_progress.setRange(0, 0)
        self._tts_progress.setVisible(False)
        lay.addWidget(self._tts_progress)

        self._tts_audio_player = AudioPlayer()
        self._tts_audio_player.setObjectName("generative_tts_audio_player")
        lay.addWidget(self._tts_audio_player)
        lay.addStretch()

        self._tts_status = self._make_status_label()
        self._tts_status.setObjectName("generative_tts_status")
        lay.addWidget(self._tts_status)

        self._tts_last_audio_path: Path | None = None
        run_btn.clicked.connect(self._on_tts_run)
        clear_btn.clicked.connect(self._on_tts_clear)
        if export_btn is not None:
            export_btn.clicked.connect(self._on_tts_export)

        self._refresh_tts_voice_controls()

        return w

    def _on_tts_run(self) -> None:
        text = self._tts_input.toPlainText().strip()
        if not text or _TTSCls is None:
            return
        backend = self._tts_backend.backend
        device = self._tts_backend.device
        speaker_ref = self._tts_selected_speaker_ref()
        voice = self._tts_selected_voice()
        worker = GenerativeWorker(
            tab_name="tts",
            module_cls=_TTSCls,
            module_config={},
            input_data=text,
            runtime_config={
                "backend": backend,
                "device": device,
                "speaker_ref_path": speaker_ref,
                "voice": voice,
                "use_g2p": True,
            },
        )
        worker.signals.started.connect(
            lambda t: self._on_tts_started()
        )
        worker.signals.finished.connect(self._on_tts_result)
        worker.signals.failed.connect(
            lambda t, e: self._on_tts_failed(e)
        )
        self._pool.start(worker)

    def _on_tts_started(self) -> None:
        self._tts_progress.setVisible(True)
        self._tts_status.setText(
            "Synthesizing... F5-TTS may take 30-90 sec, CPU fallbacks are faster."
        )

    def _on_tts_result(self, tab_name: str, result: Any) -> None:
        self._tts_progress.setVisible(False)
        self.generative_finished_signal.emit(tab_name, result)
        try:
            audio_path = getattr(result.data, "audio_path", None) if result.data else None
            if audio_path:
                self._tts_last_audio_path = Path(audio_path)
                self._tts_audio_player.load(audio_path)
                if hasattr(self, "_tts_export_btn"):
                    self._tts_export_btn.setEnabled(True)
                backend = getattr(result.data, "backend", "unknown")
                duration = getattr(result.data, "duration_seconds", 0.0)
                sample_rate = getattr(result.data, "sample_rate", 0)
                note = str(getattr(result.data, "note", "") or "").strip()
                status_text = f"Done ({backend}) · {duration:.1f}s · {sample_rate} Hz"
                if note:
                    status_text = f"{status_text} · {note}"
                self._tts_status.setText(status_text)
            else:
                self._tts_last_audio_path = None
                if hasattr(self, "_tts_export_btn"):
                    self._tts_export_btn.setEnabled(False)
                self._tts_status.setText("Error: no audio_path in result")
        except Exception as exc:
            logger.warning("tts result display error: %s", exc)
            self._tts_status.setText(f"Display error: {exc}")

    def _on_tts_failed(self, error: str) -> None:
        self._tts_progress.setVisible(False)
        self._tts_last_audio_path = None
        if hasattr(self, "_tts_export_btn"):
            self._tts_export_btn.setEnabled(False)
        self._tts_status.setText(f"Error: {error}")

    def _on_tts_speaker_browse(self) -> None:
        """Open file dialog to select speaker reference WAV for voice cloning."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select speaker reference WAV",
            "",
            "Audio files (*.wav);;All files (*)",
        )
        if path:
            self._tts_speaker_ref_input.setText(path)

    def _on_tts_clear(self) -> None:
        self._tts_input.clear()
        self._tts_audio_player.clear()
        self._tts_speaker_ref_input.clear()
        self._tts_voice_mode.setCurrentIndex(0)
        self._tts_char_count.setText("0 chars")
        self._tts_word_count.setText("0 words")
        self._tts_progress.setVisible(False)
        self._tts_last_audio_path = None
        if hasattr(self, "_tts_export_btn"):
            self._tts_export_btn.setEnabled(False)
        self._tts_status.setText("Ready")
        self._refresh_tts_voice_controls()

    def _on_tts_input_changed(self) -> None:
        """Update char/word counters when TTS input text changes."""
        text = self._tts_input.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self._tts_char_count.setText(f"{char_count} chars")
        self._tts_word_count.setText(f"{word_count} words")

    def _on_tts_export(self) -> None:
        if self._tts_last_audio_path is None or not self._tts_last_audio_path.exists():
            self._tts_status.setText("No WAV to export")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save synthesized WAV",
            self._tts_last_audio_path.name,
            "Audio files (*.wav);;All files (*)",
        )
        if not path:
            return
        shutil.copyfile(self._tts_last_audio_path, path)
        self._tts_status.setText(f"Saved WAV to {path}")

    def _populate_tts_voice_modes(self, options: list[tuple[str, str]]) -> None:
        current = self._tts_voice_mode.currentData()
        self._tts_voice_mode.blockSignals(True)
        self._tts_voice_mode.clear()
        for value, label in options:
            self._tts_voice_mode.addItem(label, value)
        self._tts_voice_mode.blockSignals(False)
        if current is not None:
            for index in range(self._tts_voice_mode.count()):
                if self._tts_voice_mode.itemData(index) == current:
                    self._tts_voice_mode.setCurrentIndex(index)
                    break

    def _populate_tts_voice_choices(self, options: list[tuple[str, str]]) -> None:
        current = self._tts_voice_input.currentData()
        self._tts_voice_input.blockSignals(True)
        self._tts_voice_input.clear()
        for value, label in options:
            self._tts_voice_input.addItem(label, value)
        self._tts_voice_input.setEditable(False)
        self._tts_voice_input.blockSignals(False)
        if current is not None:
            for index in range(self._tts_voice_input.count()):
                if self._tts_voice_input.itemData(index) == current:
                    self._tts_voice_input.setCurrentIndex(index)
                    break

    def _f5_voice_presets(self) -> list[tuple[str, str]]:
        presets_dir = _get_f5tts_voice_presets_dir() if _get_f5tts_voice_presets_dir else None
        manifest_path = presets_dir / "manifest.csv" if presets_dir else None
        labels: dict[str, str] = {}
        if manifest_path and manifest_path.exists():
            try:
                with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                    for row in csv.DictReader(handle):
                        name = (row.get("preset_name") or "").strip()
                        if not name:
                            continue
                        speaker_id = (row.get("speaker_id") or "").strip()
                        duration = (row.get("duration_s") or "").strip()
                        gender = (row.get("gender") or "").strip().capitalize()
                        summary = f"{speaker_id} · {duration}s" if speaker_id and duration else name
                        if gender:
                            summary = f"{summary} · {gender}"
                        labels[name] = f"{name} ({summary})"
            except Exception as exc:
                logger.warning("Failed to read F5 preset manifest: %s", exc)

        presets = _list_f5tts_voice_presets() if _list_f5tts_voice_presets is not None else []
        return [(name, labels.get(name, name)) for name in presets]

    def _tts_selected_voice_mode(self) -> str:
        return str(self._tts_voice_mode.currentData() or _TTS_VOICE_MODE_DEFAULT)

    def _tts_selected_voice(self) -> str | None:
        if self._tts_selected_voice_mode() != _TTS_VOICE_MODE_PRESET:
            return None
        return str(self._tts_voice_input.currentData() or "").strip() or None

    def _tts_selected_speaker_ref(self) -> str | None:
        if self._tts_selected_voice_mode() != _TTS_VOICE_MODE_CLONE:
            return None
        return self._tts_speaker_ref_input.text().strip() or None

    def _refresh_tts_voice_controls(self) -> None:
        if self._tts_refreshing_voice_controls:
            return
        self._tts_refreshing_voice_controls = True
        try:
            self._refresh_tts_voice_controls_impl()
        finally:
            self._tts_refreshing_voice_controls = False

    def _refresh_tts_voice_controls_impl(self) -> None:
        backend = self._tts_backend.backend
        if backend in {"auto", "f5tts"}:
            preset_choices = self._f5_voice_presets()
            mode_options = [
                (_TTS_VOICE_MODE_DEFAULT, "Default voice (Recommended)"),
                (_TTS_VOICE_MODE_CLONE, "Clone from reference WAV"),
            ]
            if preset_choices:
                mode_options.insert(1, (_TTS_VOICE_MODE_PRESET, "Local preset voice"))
            self._populate_tts_voice_modes(mode_options)
            self._populate_tts_voice_choices(preset_choices)
            presets_dir = _get_f5tts_voice_presets_dir() if _get_f5tts_voice_presets_dir else None
            mode = self._tts_selected_voice_mode()
            has_presets = bool(preset_choices)
            self._tts_voice_input.setEnabled(mode == _TTS_VOICE_MODE_PRESET and has_presets)
            self._tts_speaker_ref_input.setEnabled(mode == _TTS_VOICE_MODE_CLONE)
            self._tts_speaker_browse_btn.setEnabled(mode == _TTS_VOICE_MODE_CLONE)
            if mode == _TTS_VOICE_MODE_DEFAULT:
                self._tts_voice_input.setCurrentIndex(-1)
                self._tts_voice_input.setToolTip("Bundled stable F5 default voice")
                self._tts_voice_hint.setText(
                    "F5-TTS will use the bundled stable reference voice. This is the safest option for full-text synthesis."
                )
            elif mode == _TTS_VOICE_MODE_PRESET and has_presets:
                if self._tts_voice_input.currentIndex() < 0 and self._tts_voice_input.count() > 0:
                    self._tts_voice_input.setCurrentIndex(0)
                self._tts_voice_input.setToolTip(f"Local F5 preset voices loaded from {presets_dir}")
                self._tts_voice_hint.setText(
                    "Select a local preset voice from the list. These Hebrew presets are experimental; if one fails, runtime falls back to the bundled default voice."
                )
            else:
                self._tts_voice_input.setCurrentIndex(-1)
                self._tts_voice_input.setToolTip("No local F5 presets found.")
                self._tts_voice_hint.setText(
                    "Choose a short clean WAV sample to clone a voice for F5-TTS."
                )
            return

        if backend == "lightblue":
            self._populate_tts_voice_modes([(_TTS_VOICE_MODE_PRESET, "Built-in voice")])
            self._populate_tts_voice_choices([
                ("Yonatan", "Yonatan (Built-in male voice)"),
                ("Noa", "Noa (Built-in female voice)"),
            ])
            if self._tts_voice_input.currentIndex() < 0 and self._tts_voice_input.count() > 0:
                self._tts_voice_input.setCurrentIndex(0)
            self._tts_voice_input.setEnabled(True)
            self._tts_speaker_ref_input.setEnabled(False)
            self._tts_speaker_browse_btn.setEnabled(False)
            self._tts_voice_input.setToolTip("LightBlue preset voices")
            self._tts_voice_hint.setText("LightBlue: choose one of the built-in voices, Yonatan or Noa.")
            return

        if backend == "phonikud":
            self._populate_tts_voice_modes([(_TTS_VOICE_MODE_PRESET, "Built-in voice")])
            self._populate_tts_voice_choices([("michael", "Michael (Packaged Hebrew voice)")])
            self._tts_voice_input.setCurrentIndex(0)
            self._tts_voice_input.setEnabled(True)
            self._tts_speaker_ref_input.setEnabled(False)
            self._tts_speaker_browse_btn.setEnabled(False)
            self._tts_voice_input.setToolTip("Phonikud voice selection")
            self._tts_voice_hint.setText("Phonikud: one packaged Hebrew voice is available.")
            return

        self._populate_tts_voice_modes([(_TTS_VOICE_MODE_DEFAULT, "Packaged voice")])
        self._populate_tts_voice_choices([])
        self._tts_voice_input.setEnabled(False)
        self._tts_speaker_ref_input.setEnabled(False)
        self._tts_speaker_browse_btn.setEnabled(False)
        self._tts_voice_input.setToolTip("MMS does not support voice selection")
        self._tts_voice_hint.setText("MMS: voice is fixed, nothing to choose here.")

    def _on_tts_backend_changed(self) -> None:
        if self._tts_refreshing_voice_controls:
            return
        self._refresh_tts_voice_controls()

    def _on_tts_voice_mode_changed(self, _index: int) -> None:
        if self._tts_refreshing_voice_controls:
            return
        self._refresh_tts_voice_controls()

    def _on_tts_voice_selection_changed(self, _index: int) -> None:
        if self._tts_refreshing_voice_controls:
            return
        if self._tts_backend.backend in {"auto", "f5tts"} and self._tts_selected_voice_mode() == _TTS_VOICE_MODE_PRESET:
            selected_label = self._tts_voice_input.currentText().strip()
            if selected_label:
                self._tts_status.setText(f"Selected F5 preset: {selected_label}")

    def _set_tts_badge(self, badge: QLabel, ok: bool, ready_text: str, missing_text: str) -> None:
        if ok:
            badge.setText(f"✅ {ready_text}")
            badge.setStyleSheet("color: #22c55e; font-size: 10px;")
        else:
            badge.setText(f"⬜ {missing_text}")
            badge.setStyleSheet("color: #a0a0c0; font-size: 10px;")

    def _update_tts_ml_badges(self) -> None:
        """Update ML availability badges for TTS tab."""
        try:
            from kadima.engine.tts_bootstrap import get_tts_bootstrap_statuses

            statuses = get_tts_bootstrap_statuses()
        except Exception:
            statuses = {}

        def _badge_text(name: str, fallback_missing: str) -> tuple[bool, str, str]:
            status = statuses.get(name)
            if status is None:
                return False, f"{name} ready", fallback_missing
            if status.ready:
                return True, f"{name} ready", fallback_missing
            if not status.package_ready:
                return False, f"{name} ready", f"{name} pkg missing"
            return False, f"{name} ready", f"{name} model missing"

        f5_ok, f5_ready, f5_missing = _badge_text("f5tts", "f5tts missing")
        lb_ok, lb_ready, lb_missing = _badge_text("lightblue", "lightblue missing")
        ph_ok, ph_ready, ph_missing = _badge_text("phonikud", "phonikud missing")
        mms_ok, mms_ready, mms_missing = _badge_text("mms", "mms fallback")

        self._set_tts_badge(self._tts_f5tts_badge, f5_ok, f5_ready, f5_missing)
        self._set_tts_badge(
            self._tts_lightblue_badge, lb_ok, lb_ready, lb_missing
        )
        self._set_tts_badge(
            self._tts_phonikud_badge, ph_ok, ph_ready, ph_missing
        )
        self._set_tts_badge(self._tts_mms_badge, mms_ok, mms_ready, mms_missing)

    # ------------------------------------------------------------------
    # Tab 2 — STT
    # ------------------------------------------------------------------

    def _build_stt_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        self._stt_backend = BackendSelector(
            backends=["whisper", "faster_whisper"], default_backend="whisper"
        )
        self._stt_backend.setObjectName("generative_stt_backend")
        lay.addWidget(self._stt_backend)

        file_row = QHBoxLayout()
        self._stt_file_input = QLineEdit()
        self._stt_file_input.setObjectName("generative_stt_file_input")
        self._stt_file_input.setPlaceholderText("Path to .wav or .mp3 file...")
        self._stt_file_input.setReadOnly(True)
        file_row.addWidget(self._stt_file_input, stretch=1)
        self._stt_browse_btn = QPushButton("Browse...")
        self._stt_browse_btn.setObjectName("generative_stt_browse_btn")
        self._stt_browse_btn.setFixedWidth(80)
        self._stt_browse_btn.clicked.connect(self._on_stt_browse)
        file_row.addWidget(self._stt_browse_btn)
        lay.addLayout(file_row)

        btn_row, run_btn, clear_btn, _, _ = self._make_button_row(
            run_label="Transcribe", copy_label=None
        )
        run_btn.setObjectName("generative_stt_run_btn")
        clear_btn.setObjectName("generative_stt_clear_btn")
        if _STTCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("STTTranscriber not available (install [gpu] extras)")
        lay.addLayout(btn_row)

        result_lbl = QLabel("Transcript:")
        result_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(result_lbl)

        self._stt_result = RTLTextEdit(placeholder="Transcript will appear here...")
        self._stt_result.setObjectName("generative_stt_result")
        lay.addWidget(self._stt_result)

        copy_btn = QPushButton("Copy Transcript")
        copy_btn.setObjectName("generative_stt_copy_btn")
        copy_btn.setFixedHeight(28)
        copy_btn.clicked.connect(
            lambda: self._copy_text_to_clipboard(self._stt_result.toPlainText())
        )
        lay.addWidget(copy_btn)

        self._stt_status = self._make_status_label()
        self._stt_status.setObjectName("generative_stt_status")
        lay.addWidget(self._stt_status)

        run_btn.clicked.connect(self._on_stt_run)
        clear_btn.clicked.connect(self._on_stt_clear)

        return w

    def _on_stt_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select audio file",
            "",
            "Audio files (*.wav *.mp3);;All files (*)",
        )
        if path:
            self._stt_file_input.setText(path)

    def _on_stt_run(self) -> None:
        path = self._stt_file_input.text().strip()
        if not path or _STTCls is None:
            return
        backend = self._stt_backend.backend
        device = self._stt_backend.device
        worker = GenerativeWorker(
            tab_name="stt",
            module_cls=_STTCls,
            module_config={},
            input_data=path,
            runtime_config={"backend": backend, "device": device},
        )
        worker.signals.started.connect(
            lambda t: self._stt_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_stt_result)
        worker.signals.failed.connect(
            lambda t, e: self._stt_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_stt_result(self, tab_name: str, result: Any) -> None:
        self._stt_status.setText("Done")
        self.generative_finished_signal.emit(tab_name, result)
        try:
            text = ""
            if result.data:
                text = str(getattr(result.data, "text", result.data))
            self._stt_result.setPlainText(text)
        except Exception as exc:
            logger.warning("stt result display error: %s", exc)
            self._stt_status.setText(f"Display error: {exc}")

    def _on_stt_clear(self) -> None:
        self._stt_file_input.clear()
        self._stt_result.clear()
        self._stt_status.setText("Ready")

    # ------------------------------------------------------------------
    # Tab 3 — Translate
    # ------------------------------------------------------------------

    def _build_translate_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        self._translate_backend = BackendSelector(
            backends=["mbart", "nllb", "opus", "dict"], default_backend="dict"
        )
        self._translate_backend.setObjectName("generative_translate_backend")
        lay.addWidget(self._translate_backend)

        # Help text explaining backends
        help_lbl = QLabel(
            "<b>mbart</b>: 50 languages, high quality (3GB VRAM) &middot; "
            "<b>nllb</b>: 200 languages, lighter (600MB VRAM) &middot; "
            "<b>opus</b>: HE↔EN only, fast &middot; "
            "<b>dict</b>: basic dictionary (always available, ~100 words)"
        )
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("color: #8888aa; font-size: 10px; padding: 2px 0;")
        help_lbl.setObjectName("generative_translate_help")
        lay.addWidget(help_lbl)

        # ML availability badges
        badge_row = QHBoxLayout()
        self._translate_mbart_badge = QLabel()
        self._translate_mbart_badge.setObjectName("generative_translate_mbart_badge")
        self._translate_mbart_badge.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        badge_row.addWidget(self._translate_mbart_badge)

        self._translate_nllb_badge = QLabel()
        self._translate_nllb_badge.setObjectName("generative_translate_nllb_badge")
        self._translate_nllb_badge.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        badge_row.addWidget(self._translate_nllb_badge)

        self._translate_opus_badge = QLabel()
        self._translate_opus_badge.setObjectName("generative_translate_opus_badge")
        self._translate_opus_badge.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        badge_row.addWidget(self._translate_opus_badge)
        badge_row.addStretch()
        lay.addLayout(badge_row)
        self._update_translate_ml_badges()

        direction_row = QHBoxLayout()
        dir_lbl = QLabel("Direction:")
        dir_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        direction_row.addWidget(dir_lbl)
        self._translate_direction = QComboBox()
        self._translate_direction.setObjectName("generative_translate_direction")
        self._translate_direction.addItems([
            "HE → EN", "HE → RU", "HE → AR", "HE → FR",
            "HE → DE", "HE → ES", "EN → HE",
        ])
        direction_row.addWidget(self._translate_direction)
        direction_row.addStretch()
        lay.addLayout(direction_row)

        # Input with character counter
        input_row = QHBoxLayout()
        input_row.setSpacing(4)
        self._translate_input = RTLTextEdit(placeholder="הכנס טקסט לתרגום...")
        self._translate_input.setObjectName("generative_translate_input")
        self._translate_input.setMaximumHeight(120)
        input_row.addWidget(self._translate_input, stretch=1)

        counter_col = QVBoxLayout()
        counter_col.setSpacing(2)
        self._translate_char_count = QLabel("0 chars")
        self._translate_char_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._translate_char_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._translate_char_count)

        self._translate_word_count = QLabel("0 words")
        self._translate_word_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._translate_word_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._translate_word_count)
        counter_col.addStretch()
        input_row.addLayout(counter_col)
        lay.addLayout(input_row)

        # Wire text change signal to update counters
        self._translate_input.textChanged.connect(self._on_translate_input_changed)

        btn_row, run_btn, clear_btn, copy_btn, _ = self._make_button_row(
            run_label="Translate", copy_label="Copy Result"
        )
        run_btn.setObjectName("generative_translate_run_btn")
        clear_btn.setObjectName("generative_translate_clear_btn")
        if _TranslatorCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("Translator not available (install [ml] extras)")
        lay.addLayout(btn_row)

        result_lbl = QLabel("Translation:")
        result_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(result_lbl)

        self._translate_result = RTLTextEdit(placeholder="Translation will appear here...")
        self._translate_result.setObjectName("generative_translate_result")
        self._translate_result.setReadOnly(True)
        lay.addWidget(self._translate_result)

        self._translate_status = self._make_status_label()
        self._translate_status.setObjectName("generative_translate_status")
        lay.addWidget(self._translate_status)

        run_btn.clicked.connect(self._on_translate_run)
        clear_btn.clicked.connect(self._on_translate_clear)
        if copy_btn is not None:
            copy_btn.clicked.connect(
                lambda: self._copy_text_to_clipboard(
                    self._translate_result.toPlainText()
                )
            )

        return w

    def _tgt_lang_from_direction(self) -> tuple[str, str]:
        mapping = {
            "HE → EN": ("he", "en"), "HE → RU": ("he", "ru"),
            "HE → AR": ("he", "ar"), "HE → FR": ("he", "fr"),
            "HE → DE": ("he", "de"), "HE → ES": ("he", "es"),
            "EN → HE": ("en", "he"),
        }
        return mapping.get(self._translate_direction.currentText(), ("he", "en"))

    def _on_translate_run(self) -> None:
        text = self._translate_input.toPlainText().strip()
        if not text or _TranslatorCls is None:
            return
        backend = self._translate_backend.backend
        device = self._translate_backend.device
        src_lang, tgt_lang = self._tgt_lang_from_direction()
        worker = GenerativeWorker(
            tab_name="translate",
            module_cls=_TranslatorCls,
            module_config={},
            input_data=text,
            runtime_config={
                "backend": backend, "device": device,
                "src_lang": src_lang, "tgt_lang": tgt_lang,
            },
        )
        worker.signals.started.connect(
            lambda t: self._translate_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_translate_result)
        worker.signals.failed.connect(
            lambda t, e: self._translate_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_translate_result(self, tab_name: str, result: Any) -> None:
        self._translate_status.setText("Done")
        self.generative_finished_signal.emit(tab_name, result)
        try:
            text = ""
            if result.data:
                # TranslationResult uses 'result' field
                text = str(getattr(result.data, "result", ""))
                # Update status with backend info
                backend = getattr(result.data, "backend", "unknown")
                self._translate_status.setText(
                    f"Done ({backend}) · {getattr(result.data, 'src_lang', '?')}→"
                    f"{getattr(result.data, 'tgt_lang', '?')} · "
                    f"{getattr(result.data, 'word_count', 0)} words"
                )
                # BUG FIX: was missing setPlainText() — result never appeared in UI
                self._translate_result.setPlainText(text)
            else:
                self._translate_result.setPlainText("No translation result.")
        except Exception as exc:
            logger.warning("translate result display error: %s", exc)
            self._translate_status.setText(f"Display error: {exc}")

    def _on_translate_clear(self) -> None:
        self._translate_input.clear()
        self._translate_result.clear()
        self._translate_char_count.setText("0 chars")
        self._translate_word_count.setText("0 words")
        self._translate_status.setText("Ready")

    def _on_translate_input_changed(self) -> None:
        """Update char/word counters when input text changes."""
        text = self._translate_input.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self._translate_char_count.setText(f"{char_count} chars")
        self._translate_word_count.setText(f"{word_count} words")

    def _update_translate_ml_badges(self) -> None:
        """Update ML availability badges for translate tab."""
        # Check if transformers + torch are available
        try:
            from kadima.engine.translator import _TRANSFORMERS_AVAILABLE, _TORCH_AVAILABLE
            ml_ok = _TRANSFORMERS_AVAILABLE and _TORCH_AVAILABLE
        except Exception:
            ml_ok = False

        # All ML backends share the same transformers dependency
        mbart_ok = ml_ok
        nllb_ok = ml_ok
        opus_ok = ml_ok

        # Style badges
        if mbart_ok:
            self._translate_mbart_badge.setText("✅ mbart ready (3GB)")
            self._translate_mbart_badge.setStyleSheet(
                "color: #22c55e; font-size: 10px; padding: 2px 6px;"
            )
        else:
            self._translate_mbart_badge.setText(
                "⬜ mbart (pip install transformers + download model)"
            )
            self._translate_mbart_badge.setStyleSheet(
                "color: #a0a0c0; font-size: 10px; padding: 2px 6px;"
            )

        if nllb_ok:
            self._translate_nllb_badge.setText("✅ nllb ready (600MB)")
            self._translate_nllb_badge.setStyleSheet(
                "color: #22c55e; font-size: 10px; padding: 2px 6px;"
            )
        else:
            self._translate_nllb_badge.setText(
                "⬜ nllb (pip install transformers + download model)"
            )
            self._translate_nllb_badge.setStyleSheet(
                "color: #a0a0c0; font-size: 10px; padding: 2px 6px;"
            )

        if opus_ok:
            self._translate_opus_badge.setText("✅ opus ready (HE↔EN)")
            self._translate_opus_badge.setStyleSheet(
                "color: #22c55e; font-size: 10px; padding: 2px 6px;"
            )
        else:
            self._translate_opus_badge.setText(
                "⬜ opus (pip install transformers + download model)"
            )
            self._translate_opus_badge.setStyleSheet(
                "color: #a0a0c0; font-size: 10px; padding: 2px 6px;"
            )

    # ------------------------------------------------------------------
    # Tab 4 — Diacritize
    # ------------------------------------------------------------------

    def _build_diacritize_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        self._diacritize_backend = BackendSelector(
            backends=["rules", "phonikud", "dicta"], default_backend="rules"
        )
        self._diacritize_backend.setObjectName("generative_diacritize_backend")
        lay.addWidget(self._diacritize_backend)

        # Help text explaining backends
        help_lbl = QLabel(
            "<b>phonikud</b>: fast ONNX model (<1GB) &middot; "
            "<b>dicta</b>: DictaBERT transformers (higher quality, slower) &middot; "
            "<b>rules</b>: dictionary lookup (always available)"
        )
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("color: #8888aa; font-size: 10px; padding: 2px 0;")
        help_lbl.setObjectName("generative_diacritize_help")
        lay.addWidget(help_lbl)

        # ML availability badges
        badge_row = QHBoxLayout()
        self._diacritize_phonikud_badge = QLabel()
        self._diacritize_phonikud_badge.setObjectName("generative_diacritize_phonikud_badge")
        self._diacritize_phonikud_badge.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        badge_row.addWidget(self._diacritize_phonikud_badge)

        self._diacritize_dicta_badge = QLabel()
        self._diacritize_dicta_badge.setObjectName("generative_diacritize_dicta_badge")
        self._diacritize_dicta_badge.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        badge_row.addWidget(self._diacritize_dicta_badge)
        badge_row.addStretch()
        lay.addLayout(badge_row)
        self._update_diacritize_ml_badges()

        # Input with character counter
        input_row = QHBoxLayout()
        input_row.setSpacing(4)
        self._diacritize_input = RTLTextEdit(placeholder="הכנס טקסט ללא ניקוד")
        self._diacritize_input.setObjectName("generative_diacritize_input")
        self._diacritize_input.setMaximumHeight(120)
        input_row.addWidget(self._diacritize_input, stretch=1)

        counter_col = QVBoxLayout()
        counter_col.setSpacing(2)
        self._diacritize_char_count = QLabel("0 chars")
        self._diacritize_char_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._diacritize_char_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._diacritize_char_count)

        self._diacritize_word_count = QLabel("0 words")
        self._diacritize_word_count.setStyleSheet("color: #a0a0c0; font-size: 10px;")
        self._diacritize_word_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        counter_col.addWidget(self._diacritize_word_count)
        counter_col.addStretch()
        input_row.addLayout(counter_col)
        lay.addLayout(input_row)

        # Wire text change signal to update counters
        self._diacritize_input.textChanged.connect(self._on_diacritize_input_changed)

        btn_row, run_btn, clear_btn, copy_btn, _ = self._make_button_row(
            run_label="Diacritize", copy_label="Copy Result"
        )
        run_btn.setObjectName("generative_diacritize_run_btn")
        clear_btn.setObjectName("generative_diacritize_clear_btn")
        if _DiacrCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("Diacritizer not available (install [ml] extras)")
        lay.addLayout(btn_row)

        result_lbl = QLabel("Diacritized text:")
        result_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(result_lbl)

        self._diacritize_result = RTLTextEdit(placeholder="Diacritized text will appear here...")
        self._diacritize_result.setObjectName("generative_diacritize_result")
        self._diacritize_result.setReadOnly(True)
        lay.addWidget(self._diacritize_result)

        self._diacritize_status = self._make_status_label()
        self._diacritize_status.setObjectName("generative_diacritize_status")
        lay.addWidget(self._diacritize_status)

        run_btn.clicked.connect(self._on_diacritize_run)
        clear_btn.clicked.connect(self._on_diacritize_clear)
        if copy_btn is not None:
            copy_btn.clicked.connect(
                lambda: self._copy_text_to_clipboard(
                    self._diacritize_result.toPlainText()
                )
            )

        return w

    def _on_diacritize_run(self) -> None:
        text = self._diacritize_input.toPlainText().strip()
        if not text or _DiacrCls is None:
            return
        backend = self._diacritize_backend.backend
        device = self._diacritize_backend.device
        worker = GenerativeWorker(
            tab_name="diacritize",
            module_cls=_DiacrCls,
            module_config={},
            input_data=text,
            runtime_config={"backend": backend, "device": device},
        )
        worker.signals.started.connect(
            lambda t: self._diacritize_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_diacritize_result)
        worker.signals.failed.connect(
            lambda t, e: self._diacritize_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_diacritize_result(self, tab_name: str, result: Any) -> None:
        self._diacritize_status.setText("Done")
        self.generative_finished_signal.emit(tab_name, result)
        try:
            text = ""
            if result.data:
                # DiacritizeResult uses 'result' field, not 'text'
                text = str(getattr(result.data, "result", ""))
            self._diacritize_result.setPlainText(text)
        except Exception as exc:
            logger.warning("diacritize result display error: %s", exc)
            self._diacritize_status.setText(f"Display error: {exc}")

    def _on_diacritize_clear(self) -> None:
        self._diacritize_input.clear()
        self._diacritize_result.clear()
        self._diacritize_status.setText("Ready")

    def _update_diacritize_ml_badges(self) -> None:
        """Update ML availability badges for diacritize tab."""
        # phonikud: check if _PhOnnx was imported successfully
        try:
            from kadima.engine.diacritizer import _PHONIKUD_AVAILABLE
            phonikud_ok = _PHONIKUD_AVAILABLE
        except Exception:
            phonikud_ok = False

        # dicta: check if transformers is available
        try:
            from kadima.engine.diacritizer import _TRANSFORMERS_AVAILABLE
            dicta_ok = _TRANSFORMERS_AVAILABLE
        except Exception:
            dicta_ok = False

        # Style badges
        if phonikud_ok:
            self._diacritize_phonikud_badge.setText("✅ phonikud ready")
            self._diacritize_phonikud_badge.setStyleSheet(
                "color: #22c55e; font-size: 10px; padding: 2px 6px;"
            )
        else:
            self._diacritize_phonikud_badge.setText("⬜ phonikud (pip install phonikud-onnx)")
            self._diacritize_phonikud_badge.setStyleSheet(
                "color: #a0a0c0; font-size: 10px; padding: 2px 6px;"
            )

        if dicta_ok:
            self._diacritize_dicta_badge.setText("✅ dicta ready")
            self._diacritize_dicta_badge.setStyleSheet(
                "color: #22c55e; font-size: 10px; padding: 2px 6px;"
            )
        else:
            self._diacritize_dicta_badge.setText("⬜ dicta (pip install transformers)")
            self._diacritize_dicta_badge.setStyleSheet(
                "color: #a0a0c0; font-size: 10px; padding: 2px 6px;"
            )

    def _on_diacritize_input_changed(self) -> None:
        """Update char/word counters when input text changes."""
        text = self._diacritize_input.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self._diacritize_char_count.setText(f"{char_count} chars")
        self._diacritize_word_count.setText(f"{word_count} words")

    # ------------------------------------------------------------------
    # Tab 5 — NER
    # ------------------------------------------------------------------

    def _build_ner_tab(self) -> QWidget:
        w, lay = self._make_tab_container()

        self._ner_backend = BackendSelector(
            backends=["rules", "heq_ner", "neodictabert"], default_backend="rules"
        )
        self._ner_backend.setObjectName("generative_ner_backend")
        lay.addWidget(self._ner_backend)

        self._ner_input = RTLTextEdit(placeholder="הכנס טקסט לזיהוי ישויות...")
        self._ner_input.setObjectName("generative_ner_input")
        self._ner_input.setMaximumHeight(100)
        lay.addWidget(self._ner_input)

        btn_row, run_btn, clear_btn, _, _ = self._make_button_row(
            run_label="Extract Entities", copy_label=None
        )
        run_btn.setObjectName("generative_ner_run_btn")
        clear_btn.setObjectName("generative_ner_clear_btn")
        if _NERCls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip("NERExtractor not available (install [ml] extras)")
        lay.addLayout(btn_row)

        result_lbl = QLabel("Entities:")
        result_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(result_lbl)

        self._ner_entity_table = EntityTable()
        self._ner_entity_table.setObjectName("generative_ner_entity_table")
        lay.addWidget(self._ner_entity_table)

        self._ner_status = self._make_status_label()
        self._ner_status.setObjectName("generative_ner_status")
        lay.addWidget(self._ner_status)

        run_btn.clicked.connect(self._on_ner_run)
        clear_btn.clicked.connect(self._on_ner_clear)

        return w

    def _on_ner_run(self) -> None:
        text = self._ner_input.toPlainText().strip()
        if not text or _NERCls is None:
            return
        backend = self._ner_backend.backend
        device = self._ner_backend.device
        worker = GenerativeWorker(
            tab_name="ner",
            module_cls=_NERCls,
            module_config={},
            input_data=text,
            runtime_config={"backend": backend, "device": device},
        )
        worker.signals.started.connect(
            lambda t: self._ner_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_ner_result)
        worker.signals.failed.connect(
            lambda t, e: self._ner_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_ner_result(self, tab_name: str, result: Any) -> None:
        self._ner_status.setText("Done")
        self.generative_finished_signal.emit(tab_name, result)
        try:
            entities: list[Any] = []
            if result.data:
                entities = list(
                    getattr(result.data, "entities", result.data)
                )
            self._ner_entity_table.load(entities)
        except Exception as exc:
            logger.warning("ner result display error: %s", exc)
            self._ner_status.setText(f"Display error: {exc}")

    def _on_ner_clear(self) -> None:
        self._ner_input.clear()
        self._ner_entity_table.clear()
        self._ner_status.setText("Ready")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """No-op refresh hook (called by MainWindow on view switch)."""
        logger.debug("GenerativeView.refresh() called")
