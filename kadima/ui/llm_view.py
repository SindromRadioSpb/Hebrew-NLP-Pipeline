# kadima/ui/llm_view.py
"""LLMView — LLM chat view with presets panel (T5 Step 14).

Layout:
  QVBoxLayout
  ├── Status bar: server URL + Check button + connection indicator
  └── QSplitter (horizontal)
      ├── Left: Presets panel (mode selector + context inputs + Run btn)
      └── Right: ChatWidget (conversation history + input)

Threading: _LLMWorker(QRunnable) via QThreadPool.globalInstance().
LLM imports are lazy and wrapped in try/except ImportError.
"""
from __future__ import annotations

import logging
import traceback
from typing import Any

try:
    from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot
    from PyQt6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSizePolicy,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM client / service lazy imports
# ---------------------------------------------------------------------------

try:
    from kadima.llm.client import LlamaCppClient as _ClientCls
    from kadima.llm.service import LLMService as _ServiceCls

    _HAS_LLM = True
except ImportError:
    _ClientCls = None  # type: ignore[assignment,misc]
    _ServiceCls = None  # type: ignore[assignment,misc]
    _HAS_LLM = False

try:
    from kadima.ui.widgets.chat_widget import ChatWidget
    from kadima.ui.widgets.rtl_text_edit import RTLTextEdit

    _HAS_WIDGETS = True
except ImportError:
    _HAS_WIDGETS = False

# Preset mode definitions: (label, hint for context field, hint for domain/extra field)
_MODES = [
    ("Chat",             "Type your message in the chat below",     ""),
    ("Define Term",      "Term (e.g. סגסוגת)",                      "Domain (e.g. הנדסת חומרים)"),
    ("Explain Grammar",  "Sentence to explain",                      ""),
    ("Gen Exercises",    "Grammar pattern (e.g. פעל בינוני)",        "Level: בסיסי / בינוני / מתקדם"),
    ("Answer Question",  "Question (e.g. מה ההבדל בין קל לפיעל?)",  "Domain (e.g. עברית)"),
]


# ---------------------------------------------------------------------------
# _LLMWorker
# ---------------------------------------------------------------------------


class _LLMSignals(QObject):
    """Signals for _LLMWorker."""

    finished = pyqtSignal(str)   # response text
    failed = pyqtSignal(str)     # error message


class _LLMWorker(QRunnable):
    """Runs an LLMService call in QThreadPool.

    Args:
        service: LLMService instance to call.
        mode: Preset mode name (must match _MODES labels).
        context: Primary input text.
        extra: Secondary input (domain, level, etc.).
        history: Full conversation history for Chat mode.
    """

    def __init__(
        self,
        service: Any,
        mode: str,
        context: str,
        extra: str,
        history: list[dict[str, str]],
    ) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._service = service
        self._mode = mode
        self._context = context
        self._extra = extra
        self._history = history
        self.signals = _LLMSignals()

    @pyqtSlot()
    def run(self) -> None:
        """Execute the LLM call in the worker thread."""
        try:
            result = self._dispatch()
            self.signals.finished.emit(result)
        except Exception as exc:
            logger.error(
                "_LLMWorker[%s] error: %s\n%s", self._mode, exc, traceback.format_exc()
            )
            self.signals.failed.emit(str(exc))

    def _dispatch(self) -> str:
        """Route to the correct LLMService method based on mode."""
        mode = self._mode
        if mode == "Define Term":
            return self._service.define_term(
                self._context, domain=self._extra or "הנדסת חומרים"
            )
        if mode == "Explain Grammar":
            return self._service.explain_grammar(self._context)
        if mode == "Gen Exercises":
            return self._service.generate_exercises(
                self._context, level=self._extra or "בינוני"
            )
        if mode == "Answer Question":
            return self._service.answer_question(
                self._context, domain=self._extra or "עברית"
            )
        # Chat mode — use client.chat() with full history
        client = self._service.client
        messages = list(self._history)
        return client.chat(messages, max_tokens=512)


# ---------------------------------------------------------------------------
# LLMView
# ---------------------------------------------------------------------------


class LLMView(QWidget):
    """LLM Chat view — free chat + preset quick-actions via Dicta-LM.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("llm_view")
        self._pool = QThreadPool.globalInstance()
        self._service: Any = None
        self._build_ui()
        self._init_service()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("LLM Chat")
        title.setObjectName("llm_title")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        root.addWidget(title)

        root.addLayout(self._build_status_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("llm_splitter")
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle { background: #3d3d5c; }")
        splitter.addWidget(self._build_presets_panel())
        splitter.addWidget(self._build_chat_panel())
        splitter.setSizes([320, 600])
        root.addWidget(splitter, stretch=1)

    def _build_status_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        url_lbl = QLabel("Server:")
        url_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        row.addWidget(url_lbl)

        self._url_input = QLineEdit("http://localhost:8081")
        self._url_input.setObjectName("llm_url_input")
        self._url_input.setMaximumWidth(220)
        self._url_input.setStyleSheet(
            "QLineEdit { background: #1a1a2e; border: 1px solid #3d3d5c;"
            " border-radius: 4px; color: #e0e0e0; padding: 2px 6px; }"
        )
        row.addWidget(self._url_input)

        check_btn = QPushButton("Check")
        check_btn.setObjectName("llm_check_btn")
        check_btn.setFixedWidth(60)
        check_btn.setFixedHeight(26)
        check_btn.clicked.connect(self._on_check_server)
        row.addWidget(check_btn)

        self._server_status = QLabel("○  Offline")
        self._server_status.setObjectName("llm_server_status")
        self._server_status.setStyleSheet("color: #ef4444; font-size: 11px;")
        row.addWidget(self._server_status)
        row.addStretch()
        return row

    def _build_presets_panel(self) -> QWidget:
        w = QWidget()
        w.setObjectName("llm_presets_panel")
        w.setMaximumWidth(340)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(8)

        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        lay.addWidget(mode_lbl)

        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("llm_mode_combo")
        for label, _, _ in _MODES:
            self._mode_combo.addItem(label)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        lay.addWidget(self._mode_combo)

        self._context_hint = QLabel(_MODES[0][1])
        self._context_hint.setStyleSheet("color: #808090; font-size: 10px;")
        self._context_hint.setWordWrap(True)
        lay.addWidget(self._context_hint)

        self._context_input = RTLTextEdit(placeholder="הכנס טקסט...")
        self._context_input.setObjectName("llm_context_input")
        self._context_input.setMaximumHeight(100)
        lay.addWidget(self._context_input)

        self._extra_hint = QLabel("")
        self._extra_hint.setStyleSheet("color: #808090; font-size: 10px;")
        self._extra_hint.setWordWrap(True)
        lay.addWidget(self._extra_hint)

        self._extra_input = QLineEdit()
        self._extra_input.setObjectName("llm_extra_input")
        self._extra_input.setStyleSheet(
            "QLineEdit { background: #1a1a2e; border: 1px solid #3d3d5c;"
            " border-radius: 4px; color: #e0e0e0; padding: 4px; }"
        )
        lay.addWidget(self._extra_input)

        self._run_btn = QPushButton("Run Preset")
        self._run_btn.setObjectName("llm_run_btn")
        self._run_btn.setFixedHeight(32)
        self._run_btn.clicked.connect(self._on_preset_run)
        if not _HAS_LLM:
            self._run_btn.setEnabled(False)
            self._run_btn.setToolTip("LLM service not available (install [ml] extras)")
        lay.addWidget(self._run_btn)

        self._preset_status = QLabel("Ready")
        self._preset_status.setObjectName("llm_preset_status")
        self._preset_status.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        self._preset_status.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        lay.addWidget(self._preset_status)
        lay.addStretch()

        self._on_mode_changed(0)
        return w

    def _build_chat_panel(self) -> QWidget:
        w = QWidget()
        w.setObjectName("llm_chat_panel")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 0, 0, 0)
        lay.setSpacing(4)

        self._chat = ChatWidget()
        self._chat.setObjectName("llm_chat_widget")
        self._chat.message_sent.connect(self._on_chat_message)
        lay.addWidget(self._chat, stretch=1)
        return w

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_service(self) -> None:
        if not _HAS_LLM:
            return
        url = self._url_input.text().strip()
        try:
            client = _ClientCls(server_url=url)
            self._service = _ServiceCls(client=client)
        except Exception as exc:
            logger.warning("LLM service init failed: %s", exc)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_check_server(self) -> None:
        url = self._url_input.text().strip()
        if not _HAS_LLM or not url:
            return
        self._init_service()
        try:
            loaded = self._service.client.is_loaded() if self._service else False
        except Exception:
            loaded = False
        if loaded:
            self._server_status.setText("●  Connected")
            self._server_status.setStyleSheet("color: #22c55e; font-size: 11px;")
        else:
            self._server_status.setText("○  Offline")
            self._server_status.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _on_mode_changed(self, index: int) -> None:
        _, ctx_hint, extra_hint = _MODES[index]
        self._context_hint.setText(ctx_hint)
        self._extra_hint.setText(extra_hint)
        is_chat = _MODES[index][0] == "Chat"
        self._context_input.setVisible(not is_chat)
        self._context_hint.setVisible(not is_chat)
        self._extra_input.setVisible(bool(extra_hint))
        self._extra_hint.setVisible(bool(extra_hint))
        run_label = "Send to Chat" if is_chat else "Run Preset"
        self._run_btn.setText(run_label)

    def _on_preset_run(self) -> None:
        mode = self._mode_combo.currentText()
        if mode == "Chat":
            # For Chat mode, trigger the ChatWidget's send button instead
            return
        context = self._context_input.toPlainText().strip()
        if not context or self._service is None:
            return
        self._run_btn.setEnabled(False)
        self._preset_status.setText("Running...")
        worker = _LLMWorker(
            service=self._service,
            mode=mode,
            context=context,
            extra=self._extra_input.text().strip(),
            history=[],
        )
        worker.signals.finished.connect(self._on_preset_result)
        worker.signals.failed.connect(self._on_preset_failed)
        self._pool.start(worker)

    def _on_preset_result(self, response: str) -> None:
        self._run_btn.setEnabled(True)
        self._preset_status.setText("Done")
        mode = self._mode_combo.currentText()
        ctx = self._context_input.toPlainText().strip()
        self._chat.append_message("user", f"[{mode}] {ctx}")
        self._chat.append_message("assistant", response or "(empty response)")

    def _on_preset_failed(self, error: str) -> None:
        self._run_btn.setEnabled(True)
        self._preset_status.setText(f"Error: {error}")

    def _on_chat_message(self, text: str) -> None:
        if self._service is None:
            self._chat.append_message("system", "LLM server not connected. Click Check.")
            return
        self._chat.set_input_enabled(False)
        history = self._chat.messages()
        worker = _LLMWorker(
            service=self._service,
            mode="Chat",
            context=text,
            extra="",
            history=history,
        )
        worker.signals.finished.connect(self._on_chat_response)
        worker.signals.failed.connect(self._on_chat_failed)
        self._pool.start(worker)

    def _on_chat_response(self, response: str) -> None:
        self._chat.set_input_enabled(True)
        self._chat.append_message("assistant", response or "(empty response)")

    def _on_chat_failed(self, error: str) -> None:
        self._chat.set_input_enabled(True)
        self._chat.append_message("system", f"Error: {error}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh connection status on view switch."""
        self._on_check_server()
