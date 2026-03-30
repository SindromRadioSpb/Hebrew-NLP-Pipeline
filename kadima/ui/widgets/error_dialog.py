# kadima/ui/widgets/error_dialog.py
"""PyQt widget: Error display dialog."""

try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
    HAS_QT = True
except ImportError:
    HAS_QT = False


class ErrorDialog:
    """Modal error dialog with details expansion.

    Usage:
        dlg = ErrorDialog("Pipeline failed", details="M4 returned empty results")
        dlg.show()
    """

    def __init__(self, title: str, message: str = "", details: str = "", parent=None):
        if not HAS_QT:
            raise ImportError("PyQt6 required for UI components")
        self._dialog = QDialog(parent)
        self._dialog.setWindowTitle(title)
        self._dialog.setMinimumWidth(400)

        layout = QVBoxLayout(self._dialog)

        label = QLabel(message or title)
        layout.addWidget(label)

        if details:
            details_box = QTextEdit()
            details_box.setPlainText(details)
            details_box.setReadOnly(True)
            details_box.setMaximumHeight(200)
            layout.addWidget(details_box)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._dialog.close)
        layout.addWidget(close_btn)

    def show(self):
        self._dialog.exec()
