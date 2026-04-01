# kadima/ui/pipeline_view.py
"""Pipeline Configuration & Run view — T3 Step 3.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.2

Layout (horizontal split):
  Left panel  — Configuration (profile, module toggles, thresholds)
  Right panel — Input (text / corpus) + Run/Stop + Progress + Log

Threading: PipelineWorker(QRunnable) runs in QThreadPool.
           All UI updates arrive via Qt signals cross-thread.
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtCore import (
        QObject,
        QRunnable,
        Qt,
        QThreadPool,
        pyqtSignal,
        pyqtSlot,
    )
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_KADIMA_HOME = __import__("os").environ.get(
    "KADIMA_HOME", __import__("os.path", fromlist=["expanduser"]).expanduser("~/.kadima")
)
_DB_PATH = __import__("os.path", fromlist=["join"]).join(_KADIMA_HOME, "kadima.db")

# NLP module order as it flows in the pipeline
_NLP_MODULES_ORDERED = [
    ("sent_split", "Sentence Split (M1)"),
    ("tokenizer", "Tokenizer (M2)"),
    ("morph_analyzer", "Morph Analyzer (M3)"),
    ("ngram", "N-gram Extractor (M4)"),
    ("np_chunk", "NP Chunker (M5)"),
    ("canonicalize", "Canonicalizer (M6)"),
    ("am", "Association Measures (M7)"),
    ("term_extract", "Term Extractor (M8)"),
    ("noise", "Noise Classifier (M12)"),
]

_GEN_MODULES_ORDERED = [
    ("diacritizer", "Diacritizer (M13)"),
    ("translator", "Translator (M14)"),
    ("tts", "TTS Synthesizer (M15)"),
    ("stt", "STT Transcriber (M16)"),
    ("ner", "NER Extractor (M17)"),
    ("sentiment", "Sentiment (M18)"),
    ("summarizer", "Summarizer (M19)"),
    ("qa", "QA Extractor (M20)"),
    ("morph_gen", "Morph Generator (M21)"),
    ("transliterator", "Transliterator (M22)"),
    ("grammar", "Grammar Corrector (M23)"),
    ("keyphrase", "Keyphrase (M24)"),
    ("paraphrase", "Paraphraser (M25)"),
]

_PROFILES = ["balanced", "precise", "recall"]


# ── Worker signals ────────────────────────────────────────────────────────────


class _WorkerSignals(QObject):
    """Signals emitted by PipelineWorker (must be QObject subclass)."""

    started = pyqtSignal()
    progress = pyqtSignal(int, str)   # percent, module_name
    finished = pyqtSignal(object)     # PipelineResult
    failed = pyqtSignal(str)          # error message
    log = pyqtSignal(str)             # single log line


# ── Pipeline worker ───────────────────────────────────────────────────────────


class PipelineWorker(QRunnable):
    """Runs the NLP pipeline in a QThreadPool worker thread.

    Args:
        text: Input text for run_on_text mode.
        corpus_id: If set, run run(corpus_id) instead of run_on_text.
        config_dict: Pipeline config overrides (profile, modules, thresholds).
    """

    def __init__(
        self,
        text: str = "",
        corpus_id: Optional[int] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._text = text
        self._corpus_id = corpus_id
        self._config_dict = config_dict or {}
        self.signals = _WorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation (checked at safe points)."""
        self._cancelled = True

    @pyqtSlot()
    def run(self) -> None:
        """Entry point — called by QThreadPool in a worker thread."""
        self.signals.started.emit()
        self.signals.log.emit("Pipeline started…")
        try:
            from kadima.pipeline.config import PipelineConfig
            from kadima.pipeline.orchestrator import PipelineService

            cfg_kwargs: Dict[str, Any] = {}
            if "profile" in self._config_dict:
                cfg_kwargs["profile"] = self._config_dict["profile"]
            if "modules" in self._config_dict:
                cfg_kwargs["modules"] = self._config_dict["modules"]
            if "thresholds" in self._config_dict:
                from kadima.pipeline.config import ThresholdsConfig

                cfg_kwargs["thresholds"] = ThresholdsConfig(
                    **self._config_dict["thresholds"]
                )
            config = PipelineConfig(**cfg_kwargs)

            service = PipelineService(config=config, db_path=_DB_PATH)

            if self._cancelled:
                self.signals.log.emit("Cancelled before start.")
                return

            if self._corpus_id is not None:
                self.signals.progress.emit(10, "loading corpus")
                self.signals.log.emit(f"Loading corpus {self._corpus_id}…")
                result = service.run(self._corpus_id)
            else:
                self.signals.progress.emit(10, "processing text")
                self.signals.log.emit(f"Processing {len(self._text)} chars…")
                result = service.run_on_text(self._text)

            if self._cancelled:
                self.signals.log.emit("Cancelled.")
                return

            self.signals.progress.emit(100, "done")
            self.signals.log.emit("Pipeline finished successfully.")
            self.signals.finished.emit(result)

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("PipelineWorker error: %s\n%s", exc, tb)
            self.signals.log.emit(f"ERROR: {exc}")
            self.signals.failed.emit(str(exc))


# ── Pipeline View ─────────────────────────────────────────────────────────────


class PipelineView(QWidget):
    """Pipeline configuration & run view.

    Signals:
        run_started_signal: Pipeline run was started.
        run_progress_signal(int, str): Progress update (percent, module_name).
        run_finished_signal(object): PipelineResult on completion.
        run_failed_signal(str): Error message on failure.
    """

    run_started_signal = pyqtSignal()
    run_progress_signal = pyqtSignal(int, str)
    run_finished_signal = pyqtSignal(object)
    run_failed_signal = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("pipeline_view")

        self._worker: Optional[PipelineWorker] = None
        self._pool = QThreadPool.globalInstance()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("pipeline_splitter")

        # Left: configuration panel
        left = self._build_config_panel()
        splitter.addWidget(left)

        # Right: input + run + progress + log
        right = self._build_run_panel()
        splitter.addWidget(right)

        splitter.setSizes([340, 700])
        splitter.setHandleWidth(2)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)

    # ── Config panel (left) ───────────────────────────────────────────────────

    def _build_config_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("pipeline_config_panel")
        panel.setFrameShape(QFrame.Shape.NoFrame)
        panel.setStyleSheet("QFrame#pipeline_config_panel { background: #16162a; }")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Profile
        profile_group = QGroupBox("Profile")
        profile_group.setObjectName("pipeline_profile_group")
        pg_layout = QVBoxLayout(profile_group)
        self._profile_combo = QComboBox()
        self._profile_combo.setObjectName("pipeline_profile_combo")
        self._profile_combo.addItems([p.upper() for p in _PROFILES])
        self._profile_combo.setCurrentIndex(0)
        pg_layout.addWidget(self._profile_combo)
        layout.addWidget(profile_group)

        # NLP modules
        nlp_group = QGroupBox("NLP Modules")
        nlp_group.setObjectName("pipeline_nlp_group")
        nlp_layout = QVBoxLayout(nlp_group)
        self._nlp_checks: Dict[str, QCheckBox] = {}
        for key, label in _NLP_MODULES_ORDERED:
            cb = QCheckBox(label)
            cb.setObjectName(f"pipeline_nlp_{key}")
            cb.setChecked(True)
            nlp_layout.addWidget(cb)
            self._nlp_checks[key] = cb
        layout.addWidget(nlp_group)

        # Generative modules
        gen_group = QGroupBox("Generative Modules")
        gen_group.setObjectName("pipeline_gen_group")
        gen_layout = QVBoxLayout(gen_group)
        self._gen_checks: Dict[str, QCheckBox] = {}
        for key, label in _GEN_MODULES_ORDERED:
            cb = QCheckBox(label)
            cb.setObjectName(f"pipeline_gen_{key}")
            cb.setChecked(False)
            gen_layout.addWidget(cb)
            self._gen_checks[key] = cb
        layout.addWidget(gen_group)

        # Thresholds
        thresh_group = QGroupBox("Thresholds")
        thresh_group.setObjectName("pipeline_thresh_group")
        tg_layout = QVBoxLayout(thresh_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Min freq:"))
        self._min_freq = QSpinBox()
        self._min_freq.setObjectName("pipeline_min_freq")
        self._min_freq.setRange(1, 1000)
        self._min_freq.setValue(2)
        row1.addWidget(self._min_freq)
        tg_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("PMI threshold:"))
        self._pmi_threshold = QDoubleSpinBox()
        self._pmi_threshold.setObjectName("pipeline_pmi_threshold")
        self._pmi_threshold.setRange(0.0, 20.0)
        self._pmi_threshold.setSingleStep(0.5)
        self._pmi_threshold.setValue(3.0)
        row2.addWidget(self._pmi_threshold)
        tg_layout.addLayout(row2)

        self._hapax_filter = QCheckBox("Hapax filter")
        self._hapax_filter.setObjectName("pipeline_hapax_filter")
        self._hapax_filter.setChecked(True)
        tg_layout.addWidget(self._hapax_filter)

        layout.addWidget(thresh_group)
        layout.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return panel

    # ── Run panel (right) ─────────────────────────────────────────────────────

    def _build_run_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("pipeline_run_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Input mode:")
        mode_lbl.setStyleSheet("color: #a0a0c0;")
        mode_row.addWidget(mode_lbl)
        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("pipeline_mode_combo")
        self._mode_combo.addItems(["Text", "Corpus"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Text input (RTL)
        from kadima.ui.widgets.rtl_text_edit import RTLTextEdit

        self._text_input = RTLTextEdit(
            placeholder="הקלד טקסט עברי לעיבוד…",
            parent=panel,
        )
        self._text_input.setObjectName("pipeline_text_input")
        self._text_input.setMinimumHeight(140)
        layout.addWidget(self._text_input)

        # Corpus selector (hidden in text mode)
        self._corpus_combo = QComboBox()
        self._corpus_combo.setObjectName("pipeline_corpus_combo")
        self._corpus_combo.hide()
        layout.addWidget(self._corpus_combo)

        # Run / Stop buttons
        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run (F5)")
        self._run_btn.setObjectName("pipeline_run_button")
        self._run_btn.setStyleSheet(
            "QPushButton { background: #7c3aed; border: none; border-radius: 6px;"
            "  padding: 8px 20px; color: #fff; font-weight: bold; }"
            "QPushButton:hover { background: #6d28d9; }"
            "QPushButton:disabled { background: #3d3d5c; color: #666; }"
        )
        self._run_btn.clicked.connect(self.trigger_run)
        btn_row.addWidget(self._run_btn)

        self._stop_btn = QPushButton("⏹  Stop (Esc)")
        self._stop_btn.setObjectName("pipeline_stop_button")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 6px;"
            "  padding: 8px 20px; color: #e0e0e0; }"
            "QPushButton:hover { background: #ef4444; color: #fff; }"
            "QPushButton:disabled { color: #555; }"
        )
        self._stop_btn.clicked.connect(self.trigger_stop)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Progress bar
        from kadima.ui.widgets.progress_bar import PipelineProgressBar

        self._progress_bar = PipelineProgressBar(panel)
        progress_widget = self._progress_bar.widget()
        progress_widget.setObjectName("pipeline_progress_bar")
        layout.addWidget(progress_widget)

        # Log output
        log_lbl = QLabel("Log")
        log_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(log_lbl)

        self._log_output = QTextEdit()
        self._log_output.setObjectName("pipeline_log_output")
        self._log_output.setReadOnly(True)
        self._log_output.setMaximumHeight(160)
        self._log_output.setStyleSheet(
            "QTextEdit { background: #0d0d1a; border: 1px solid #2d2d44;"
            "  border-radius: 4px; color: #a0a0c0; font-family: 'Consolas', monospace;"
            "  font-size: 11px; padding: 4px; }"
        )
        layout.addWidget(self._log_output)

        return panel

    # ── Slots & handlers ──────────────────────────────────────────────────────

    def _on_mode_changed(self, index: int) -> None:
        text_mode = index == 0
        self._text_input.setVisible(text_mode)
        self._corpus_combo.setVisible(not text_mode)

    def _get_selected_modules(self) -> List[str]:
        mods: List[str] = []
        for key, cb in self._nlp_checks.items():
            if cb.isChecked():
                mods.append(key)
        for key, cb in self._gen_checks.items():
            if cb.isChecked():
                mods.append(key)
        return mods

    def _get_config_dict(self) -> Dict[str, Any]:
        profile = self._profile_combo.currentText().lower()
        modules = self._get_selected_modules()
        thresholds = {
            "min_freq": self._min_freq.value(),
            "pmi_threshold": self._pmi_threshold.value(),
            "hapax_filter": self._hapax_filter.isChecked(),
        }
        return {"profile": profile, "modules": modules, "thresholds": thresholds}

    def trigger_run(self) -> None:
        """Start the pipeline (called by MainWindow F5 or Run button)."""
        text = self._text_input.toPlainText().strip()
        mode = self._mode_combo.currentIndex()

        corpus_id: Optional[int] = None
        if mode == 1:
            data = self._corpus_combo.currentData()
            if data:
                corpus_id = int(data)
            if corpus_id is None:
                self._append_log("No corpus selected.")
                return
            text = ""

        if mode == 0 and not text:
            self._append_log("No text entered.")
            return

        config_dict = self._get_config_dict()
        if not config_dict.get("modules"):
            # Fall back to all NLP modules if user unchecked everything
            config_dict["modules"] = list(self._nlp_checks.keys())
            self._append_log("No modules selected — using all NLP modules.")
        self._worker = PipelineWorker(text=text, corpus_id=corpus_id, config_dict=config_dict)
        self._worker.signals.started.connect(self._on_started)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.failed.connect(self._on_failed)
        self._worker.signals.log.connect(self._append_log)

        self._pool.start(self._worker)

    def trigger_run_for_corpus(self, corpus_id: int) -> None:
        """Switch to Corpus mode, select corpus_id, and start the pipeline."""
        self.refresh()  # ensure corpus list is current
        self._mode_combo.setCurrentIndex(1)  # Corpus mode
        for i in range(self._corpus_combo.count()):
            if self._corpus_combo.itemData(i) == corpus_id:
                self._corpus_combo.setCurrentIndex(i)
                break
        self.trigger_run()

    def trigger_stop(self) -> None:
        """Request pipeline cancellation."""
        if self._worker:
            self._worker.cancel()
            self._append_log("Stop requested…")

    def refresh(self) -> None:
        """Reload corpus list from DB."""
        self._corpus_combo.clear()
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                rows = conn.execute(
                    "SELECT id, name FROM corpora WHERE status='active' ORDER BY name"
                ).fetchall()
            finally:
                conn.close()
            for row in rows:
                self._corpus_combo.addItem(row["name"], userData=row["id"])
        except Exception as exc:
            logger.debug("Could not load corpora: %s", exc)

    # ── Worker signal handlers (main thread) ──────────────────────────────────

    def _on_started(self) -> None:
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._log_output.clear()
        self._append_log("Pipeline started…")
        self.run_started_signal.emit()

    def _on_progress(self, percent: int, module: str) -> None:
        # PipelineProgressBar.set_progress(module_id, step, total)
        # We convert percent 0-100 → step 0-9
        try:
            step = max(0, min(9, round(percent * 9 / 100)))
            self._progress_bar.set_progress(module, step)
        except Exception:
            pass
        self.run_progress_signal.emit(percent, module)

    def _on_finished(self, result: Any) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        try:
            self._progress_bar.set_done()
        except Exception:
            pass
        self.run_finished_signal.emit(result)

    def _on_failed(self, error: str) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._append_log(f"FAILED: {error}")
        self.run_failed_signal.emit(error)

    def _append_log(self, line: str) -> None:
        self._log_output.append(line)
        self._log_output.ensureCursorVisible()
