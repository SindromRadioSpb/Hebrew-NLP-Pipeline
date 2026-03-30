# kadima/app.py
"""PyQt application bootstrap для KADIMA Desktop UI."""

import sys
import logging

logger = logging.getLogger(__name__)


def main():
    """Запуск KADIMA GUI."""
    try:
        from PyQt6.QtWidgets import QApplication
        from kadima.ui.main_window import MainWindow
    except ImportError:
        logger.error("PyQt6 not installed. Install with: pip install pyqt6")
        print("Error: PyQt6 not installed. Run: pip install pyqt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("KADIMA")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
