# kadima/ui/widgets/backend_selector.py
"""BackendSelector — QWidget for choosing ML backend + device.

Used by GenerativeView tabs to select backend (e.g. xtts/whisper/hebert)
and compute device (cuda/cpu).
"""
from __future__ import annotations

import logging
from typing import List, Optional

try:
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_DEVICES = ["cuda", "cpu"]


class BackendSelector(QWidget):
    """Compact backend + device selector.

    Signals:
        changed(str, str): Emitted when backend or device changes.
            Arguments: (backend, device).
    """

    changed = pyqtSignal(str, str)

    def __init__(
        self,
        backends: List[str],
        default_backend: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("backend_selector")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        backend_lbl = QLabel("Backend:")
        backend_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        layout.addWidget(backend_lbl)

        self._backend_combo = QComboBox()
        self._backend_combo.setObjectName("backend_selector_backend_combo")
        self._backend_combo.addItems(backends)
        if default_backend and default_backend in backends:
            self._backend_combo.setCurrentText(default_backend)
        self._backend_combo.currentTextChanged.connect(self._on_changed)
        layout.addWidget(self._backend_combo)

        device_lbl = QLabel("Device:")
        device_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        layout.addWidget(device_lbl)

        self._device_combo = QComboBox()
        self._device_combo.setObjectName("backend_selector_device_combo")
        self._device_combo.addItems(_DEVICES)
        self._device_combo.currentTextChanged.connect(self._on_changed)
        layout.addWidget(self._device_combo)

        layout.addStretch()

    def _on_changed(self, _: str) -> None:
        self.changed.emit(self.backend, self.device)

    @property
    def backend(self) -> str:
        """Currently selected backend string."""
        return self._backend_combo.currentText()

    @property
    def device(self) -> str:
        """Currently selected device string."""
        return self._device_combo.currentText()

    def set_backend(self, backend: str) -> None:
        """Programmatically select a backend."""
        if self._backend_combo.findText(backend) >= 0:
            self._backend_combo.setCurrentText(backend)

    def set_device(self, device: str) -> None:
        """Programmatically select a device."""
        if self._device_combo.findText(device) >= 0:
            self._device_combo.setCurrentText(device)
