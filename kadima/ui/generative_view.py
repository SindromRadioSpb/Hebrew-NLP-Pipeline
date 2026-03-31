# kadima/ui/generative_view.py
"""Generative view — placeholder (implemented in Step 10, T4).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.7
Tabs: Sentiment · TTS · STT · Translate · Diacritize · NER
Threading: GenerativeWorker(QRunnable) via QThreadPool
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


class GenerativeView(QWidget):
    """Generative tools view — 6 tabs for ML generative modules.

    Stub placeholder. Full implementation: T4 Step 10.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("generative_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "🧪  Generative  [T4]\n\n"
            "Sentiment · TTS · STT · Translate · Diacritize · NER\n"
            "GenerativeWorker(QRunnable) · Model lazy loading\n\n"
            "Coming in T4 Step 10"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)
