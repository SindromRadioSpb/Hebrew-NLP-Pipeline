# kadima/ui/nlp_tools_view.py
"""NLPToolsView — 3-tab view for Tier 3 NLP modules (T5 Step 13).

Tabs: Grammar (M23) · Keyphrase (M24) · Summarize (M19)

Threading: GenerativeWorker(QRunnable) via QThreadPool.globalInstance().
All engine imports are lazy and wrapped in try/except ImportError.
"""
from __future__ import annotations

import logging
from typing import Any

try:
    from PyQt6.QtCore import Qt, QThreadPool
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
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

# ---------------------------------------------------------------------------
# Engine module lazy imports
# ---------------------------------------------------------------------------

try:
    from kadima.engine.grammar_corrector import GrammarCorrector as _GrammarCls
except ImportError:
    _GrammarCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.keyphrase_extractor import KeyphraseExtractor as _KeyphraseCls
except ImportError:
    _KeyphraseCls = None  # type: ignore[assignment,misc]

try:
    from kadima.engine.summarizer import Summarizer as _SummarizerCls
except ImportError:
    _SummarizerCls = None  # type: ignore[assignment,misc]

try:
    from kadima.ui.generative_view import GenerativeWorker
    from kadima.ui.widgets.backend_selector import BackendSelector
    from kadima.ui.widgets.rtl_text_edit import RTLTextEdit

    _HAS_WIDGETS = True
except ImportError:
    _HAS_WIDGETS = False


# ---------------------------------------------------------------------------
# NLPToolsView
# ---------------------------------------------------------------------------


class NLPToolsView(QWidget):
    """Three-tab view for Tier 3 NLP modules (M23 Grammar / M24 Keyphrase / M19 Summarize).

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("nlp_tools_view")
        self._pool = QThreadPool.globalInstance()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("NLP Tools")
        title.setObjectName("nlp_tools_title")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("nlp_tools_tabs")
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #3d3d5c; border-radius: 4px; }"
            "QTabBar::tab { background: #2d2d44; color: #a0a0c0; padding: 6px 14px; }"
            "QTabBar::tab:selected { background: #1e1e2e; color: #e0e0e0; }"
            "QTabBar::tab:hover { color: #c0c0e0; }"
        )
        root.addWidget(self._tabs)

        self._tabs.addTab(self._build_grammar_tab(), "Grammar")
        self._tabs.addTab(self._build_keyphrase_tab(), "Keyphrase")
        self._tabs.addTab(self._build_summarize_tab(), "Summarize")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tab_container() -> tuple[QWidget, QVBoxLayout]:
        """Return (widget, layout) for a new tab page."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        return w, lay

    @staticmethod
    def _status_label(name: str) -> QLabel:
        """Return a styled status label with the given objectName."""
        lbl = QLabel("Ready")
        lbl.setObjectName(name)
        lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return lbl

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(text)

    def _btn_row(
        self, tab: str, run_label: str, module_cls: Any
    ) -> tuple[QHBoxLayout, QPushButton, QPushButton]:
        """Build a standard Run/Clear button row.

        Args:
            tab: Tab identifier for objectName prefix.
            run_label: Text for the Run button.
            module_cls: Engine class — if None, Run is disabled.

        Returns:
            (layout, run_button, clear_button)
        """
        row = QHBoxLayout()
        run_btn = QPushButton(run_label)
        run_btn.setObjectName(f"nlp_tools_{tab}_run_btn")
        run_btn.setFixedHeight(30)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName(f"nlp_tools_{tab}_clear_btn")
        clear_btn.setFixedHeight(30)
        row.addWidget(run_btn)
        row.addWidget(clear_btn)
        row.addStretch()
        if module_cls is None:
            run_btn.setEnabled(False)
            run_btn.setToolTip(
                f"{tab.capitalize()} module not available (install [ml] extras)"
            )
        return row, run_btn, clear_btn

    # ------------------------------------------------------------------
    # Tab 0 — Grammar (M23)
    # ------------------------------------------------------------------

    def _build_grammar_tab(self) -> QWidget:
        w, lay = self._tab_container()

        self._grammar_backend = BackendSelector(
            backends=["rules", "llm"], default_backend="rules"
        )
        self._grammar_backend.setObjectName("nlp_tools_grammar_backend")
        lay.addWidget(self._grammar_backend)

        self._grammar_input = RTLTextEdit(placeholder="הכנס טקסט לתיקון דקדוקי...")
        self._grammar_input.setObjectName("nlp_tools_grammar_input")
        self._grammar_input.setMaximumHeight(120)
        lay.addWidget(self._grammar_input)

        btn_row, run_btn, clear_btn = self._btn_row("grammar", "Check Grammar", _GrammarCls)
        lay.addLayout(btn_row)

        hdr = QLabel("Corrected text:")
        hdr.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(hdr)

        self._grammar_result = RTLTextEdit(placeholder="Corrected text will appear here...")
        self._grammar_result.setObjectName("nlp_tools_grammar_result")
        self._grammar_result.setReadOnly(True)
        lay.addWidget(self._grammar_result)

        lay.addLayout(self._grammar_meta_row())

        self._grammar_status = self._status_label("nlp_tools_grammar_status")
        lay.addWidget(self._grammar_status)

        run_btn.clicked.connect(self._on_grammar_run)
        clear_btn.clicked.connect(self._on_grammar_clear)
        return w

    def _grammar_meta_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._grammar_corrections_lbl = QLabel("Corrections: —")
        self._grammar_corrections_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        row.addWidget(self._grammar_corrections_lbl)
        row.addStretch()
        copy_btn = QPushButton("Copy Result")
        copy_btn.setFixedHeight(26)
        copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self._grammar_result.toPlainText())
        )
        row.addWidget(copy_btn)
        return row

    def _on_grammar_run(self) -> None:
        text = self._grammar_input.toPlainText().strip()
        if not text or _GrammarCls is None:
            return
        worker = GenerativeWorker(
            tab_name="grammar",
            module_cls=_GrammarCls,
            module_config={},
            input_data=text,
            runtime_config={"backend": self._grammar_backend.backend},
        )
        worker.signals.started.connect(lambda t: self._grammar_status.setText("Running..."))
        worker.signals.finished.connect(self._on_grammar_result)
        worker.signals.failed.connect(
            lambda t, e: self._grammar_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_grammar_result(self, tab_name: str, result: Any) -> None:
        self._grammar_status.setText("Done")
        try:
            corrected = getattr(result.data, "corrected", "") if result.data else ""
            count = getattr(result.data, "correction_count", 0) if result.data else 0
            self._grammar_result.setPlainText(corrected)
            self._grammar_corrections_lbl.setText(f"Corrections: {count}")
        except Exception as exc:
            logger.warning("grammar result display error: %s", exc)
            self._grammar_status.setText(f"Display error: {exc}")

    def _on_grammar_clear(self) -> None:
        self._grammar_input.clear()
        self._grammar_result.clear()
        self._grammar_corrections_lbl.setText("Corrections: —")
        self._grammar_status.setText("Ready")

    # ------------------------------------------------------------------
    # Tab 1 — Keyphrase (M24)
    # ------------------------------------------------------------------

    def _build_keyphrase_tab(self) -> QWidget:
        w, lay = self._tab_container()

        self._keyphrase_backend = BackendSelector(
            backends=["tfidf", "yake"], default_backend="tfidf"
        )
        self._keyphrase_backend.setObjectName("nlp_tools_keyphrase_backend")
        lay.addWidget(self._keyphrase_backend)

        self._keyphrase_input = RTLTextEdit(
            placeholder="הכנס טקסט לחילוץ מונחי מפתח..."
        )
        self._keyphrase_input.setObjectName("nlp_tools_keyphrase_input")
        self._keyphrase_input.setMaximumHeight(120)
        lay.addWidget(self._keyphrase_input)

        btn_row, run_btn, clear_btn = self._btn_row(
            "keyphrase", "Extract Keyphrases", _KeyphraseCls
        )
        lay.addLayout(btn_row)

        hdr = QLabel("Keyphrases (phrase — score):")
        hdr.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(hdr)

        self._keyphrase_list = QListWidget()
        self._keyphrase_list.setObjectName("nlp_tools_keyphrase_result")
        self._keyphrase_list.setStyleSheet(
            "QListWidget { background: #1a1a2e; border: 1px solid #3d3d5c;"
            " border-radius: 4px; color: #e0e0e0; }"
            "QListWidget::item:selected { background: #3d3d5c; }"
        )
        self._keyphrase_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay.addWidget(self._keyphrase_list)

        copy_btn = QPushButton("Copy All")
        copy_btn.setFixedHeight(26)
        copy_btn.clicked.connect(self._on_keyphrase_copy)
        lay.addWidget(copy_btn)

        self._keyphrase_status = self._status_label("nlp_tools_keyphrase_status")
        lay.addWidget(self._keyphrase_status)

        run_btn.clicked.connect(self._on_keyphrase_run)
        clear_btn.clicked.connect(self._on_keyphrase_clear)
        return w

    def _on_keyphrase_run(self) -> None:
        text = self._keyphrase_input.toPlainText().strip()
        if not text or _KeyphraseCls is None:
            return
        worker = GenerativeWorker(
            tab_name="keyphrase",
            module_cls=_KeyphraseCls,
            module_config={},
            input_data=text,
            runtime_config={"backend": self._keyphrase_backend.backend, "top_n": 10},
        )
        worker.signals.started.connect(
            lambda t: self._keyphrase_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_keyphrase_result)
        worker.signals.failed.connect(
            lambda t, e: self._keyphrase_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_keyphrase_result(self, tab_name: str, result: Any) -> None:
        self._keyphrase_status.setText("Done")
        self._keyphrase_list.clear()
        try:
            keyphrases = getattr(result.data, "keyphrases", []) if result.data else []
            scores = getattr(result.data, "scores", []) if result.data else []
            for phrase, score in zip(keyphrases, scores, strict=False):
                self._keyphrase_list.addItem(QListWidgetItem(f"{phrase}  —  {score:.3f}"))
            if not keyphrases:
                self._keyphrase_list.addItem(QListWidgetItem("(no keyphrases found)"))
        except Exception as exc:
            logger.warning("keyphrase result display error: %s", exc)
            self._keyphrase_status.setText(f"Display error: {exc}")

    def _on_keyphrase_copy(self) -> None:
        lines = [
            self._keyphrase_list.item(i).text()
            for i in range(self._keyphrase_list.count())
        ]
        self._copy_to_clipboard("\n".join(lines))

    def _on_keyphrase_clear(self) -> None:
        self._keyphrase_input.clear()
        self._keyphrase_list.clear()
        self._keyphrase_status.setText("Ready")

    # ------------------------------------------------------------------
    # Tab 2 — Summarize (M19)
    # ------------------------------------------------------------------

    def _build_summarize_tab(self) -> QWidget:
        w, lay = self._tab_container()

        self._summarize_backend = BackendSelector(
            backends=["extractive", "mt5", "llm"], default_backend="extractive"
        )
        self._summarize_backend.setObjectName("nlp_tools_summarize_backend")
        lay.addWidget(self._summarize_backend)

        self._summarize_input = RTLTextEdit(placeholder="הכנס טקסט לסיכום...")
        self._summarize_input.setObjectName("nlp_tools_summarize_input")
        self._summarize_input.setMaximumHeight(140)
        lay.addWidget(self._summarize_input)

        btn_row, run_btn, clear_btn = self._btn_row(
            "summarize", "Summarize", _SummarizerCls
        )
        lay.addLayout(btn_row)

        hdr = QLabel("Summary:")
        hdr.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(hdr)

        self._summarize_result = RTLTextEdit(placeholder="Summary will appear here...")
        self._summarize_result.setObjectName("nlp_tools_summarize_result")
        self._summarize_result.setReadOnly(True)
        lay.addWidget(self._summarize_result)

        lay.addLayout(self._summarize_meta_row())

        self._summarize_status = self._status_label("nlp_tools_summarize_status")
        lay.addWidget(self._summarize_status)

        run_btn.clicked.connect(self._on_summarize_run)
        clear_btn.clicked.connect(self._on_summarize_clear)
        return w

    def _summarize_meta_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._summarize_ratio_lbl = QLabel("Compression ratio: —")
        self._summarize_ratio_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        row.addWidget(self._summarize_ratio_lbl)
        row.addStretch()
        copy_btn = QPushButton("Copy Summary")
        copy_btn.setFixedHeight(26)
        copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self._summarize_result.toPlainText())
        )
        row.addWidget(copy_btn)
        return row

    def _on_summarize_run(self) -> None:
        text = self._summarize_input.toPlainText().strip()
        if not text or _SummarizerCls is None:
            return
        worker = GenerativeWorker(
            tab_name="summarize",
            module_cls=_SummarizerCls,
            module_config={},
            input_data=text,
            runtime_config={
                "backend": self._summarize_backend.backend,
                "max_sentences": 3,
            },
        )
        worker.signals.started.connect(
            lambda t: self._summarize_status.setText("Running...")
        )
        worker.signals.finished.connect(self._on_summarize_result)
        worker.signals.failed.connect(
            lambda t, e: self._summarize_status.setText(f"Error: {e}")
        )
        self._pool.start(worker)

    def _on_summarize_result(self, tab_name: str, result: Any) -> None:
        self._summarize_status.setText("Done")
        try:
            summary = getattr(result.data, "summary", "") if result.data else ""
            ratio = getattr(result.data, "compression_ratio", 0.0) if result.data else 0.0
            self._summarize_result.setPlainText(summary)
            self._summarize_ratio_lbl.setText(f"Compression ratio: {ratio:.2f}")
        except Exception as exc:
            logger.warning("summarize result display error: %s", exc)
            self._summarize_status.setText(f"Display error: {exc}")

    def _on_summarize_clear(self) -> None:
        self._summarize_input.clear()
        self._summarize_result.clear()
        self._summarize_ratio_lbl.setText("Compression ratio: —")
        self._summarize_status.setText("Ready")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """No-op refresh hook (called by MainWindow on view switch)."""
        logger.debug("NLPToolsView.refresh() called")
