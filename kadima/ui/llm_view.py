# kadima/ui/llm_view.py
"""LLM Chat view — placeholder (implemented in Step 14, T5).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.10
Data sources: llm/service.py (define_term, explain_grammar, chat),
              llm/client.py (is_loaded, health_check)
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)


class LLMView(QWidget):
    """LLM Chat view — Dicta-LM chat + quick actions (define/explain/exercise).

    Stub placeholder. Full implementation: T5 Step 14.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("llm_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "🤖  LLM Chat  [T5]\n\n"
            "Dicta-LM chat · Define term · Explain grammar\n"
            "Generate exercises · Conversation history\n\n"
            "Coming in T5 Step 14"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)
