# kadima/ui/nlp_tools_view.py
"""NLP Tools view — placeholder (implemented in Step 13, T5).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.9
Tabs: Grammar (Dicta-LM) · Keyphrase (YAKE) · Summarize (mT5/LLM)
Modules: M23, M24, M25
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


class NLPToolsView(QWidget):
    """NLP Tools view — Grammar / Keyphrase / Summarize tabs.

    Stub placeholder. Full implementation: T5 Step 13.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("nlp_tools_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "🔧  NLP Tools  [T5]\n\n"
            "Grammar Checker · Keyphrase Extractor · Summarizer\n"
            "M23 / M24 / M25 via engine modules\n\n"
            "Coming in T5 Step 13"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)
