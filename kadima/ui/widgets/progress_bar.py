# kadima/ui/widgets/progress_bar.py
"""PyQt widget: Pipeline progress indicator."""

try:
    from PyQt6.QtWidgets import QProgressBar, QLabel, QVBoxLayout, QWidget
    HAS_QT = True
except ImportError:
    HAS_QT = False


class PipelineProgressBar:
    """Progress bar with module status labels for pipeline execution.

    Usage:
        bar = PipelineProgressBar()
        bar.set_progress("M4", 4, 9)  # module name, current step, total
    """

    MODULE_NAMES = {
        "M1": "Sentence Split",
        "M2": "Tokenizer",
        "M3": "Morph Analyzer",
        "M4": "N-gram Extractor",
        "M5": "NP Chunker",
        "M6": "Canonicalizer",
        "M7": "Association Measures",
        "M8": "Term Extractor",
        "M12": "Noise Classifier",
    }

    def __init__(self, parent=None):
        if not HAS_QT:
            raise ImportError("PyQt6 required for UI components")
        self._widget = QWidget(parent)
        self._layout = QVBoxLayout(self._widget)
        self._label = QLabel("Ready", self._widget)
        self._bar = QProgressBar(self._widget)
        self._bar.setMaximum(9)
        self._layout.addWidget(self._label)
        self._layout.addWidget(self._bar)

    def set_progress(self, module_id: str, step: int, total: int = 9):
        name = self.MODULE_NAMES.get(module_id, module_id)
        self._label.setText(f"Running: {name} ({step}/{total})")
        self._bar.setValue(step)

    def set_done(self):
        self._label.setText("Pipeline complete ✓")
        self._bar.setValue(9)

    def set_error(self, module_id: str, error: str):
        name = self.MODULE_NAMES.get(module_id, module_id)
        self._label.setText(f"Error in {name}: {error}")

    def widget(self):
        return self._widget
