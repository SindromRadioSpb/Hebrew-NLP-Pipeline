# kadima/ui/annotation_view.py
"""Annotation view — placeholder (implemented in Step 11, T4).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.8
Data sources: annotation/project_manager.py, annotation/sync.py,
              annotation/ner_training.py (retrain), annotation/ls_client.py
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


class AnnotationView(QWidget):
    """Annotation view — Label Studio projects + pre-annotate + Active Learning queue.

    Stub placeholder. Full implementation: T4 Step 11.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("annotation_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "🏷  Annotation  [T4]\n\n"
            "Label Studio projects · Pre-annotate\n"
            "Active Learning queue · Export to NER training\n\n"
            "Coming in T4 Step 11"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)
