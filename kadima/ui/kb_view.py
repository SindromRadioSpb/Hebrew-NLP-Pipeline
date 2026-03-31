# kadima/ui/kb_view.py
"""KB view — placeholder (implemented in Step 6).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.5
Data sources: kb/repository.py, kb/search.py (text/embedding/similar),
              kb/generator.py (LLM definition generation)
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


class KBView(QWidget):
    """Knowledge Base view — text/embedding/similar search + definition editor.

    Stub placeholder. Full implementation: Step 6.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("kb_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "📚  Knowledge Base\n\n"
            "Text / Embedding / Similar search\n"
            "Term detail · Definition editor · Cluster view\n\n"
            "Coming in Step 6"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)

    def refresh(self) -> None:
        """Reload KB data (no-op until Step 6)."""
