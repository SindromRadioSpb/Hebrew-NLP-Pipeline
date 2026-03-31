# kadima/ui/validation_view.py
"""Validation view — T3 Step 5.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.4

Zones:
  - Summary cards ×3 (PASS / WARN / FAIL counts, colour-coded)
  - Overall status label (large, colour)
  - Upload Gold Corpus + Run Validation buttons
  - CheckTable with ResultColorDelegate + result filter QComboBox
  - Right panel: review editor + notes + Export Report button
"""
from __future__ import annotations

import csv
import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_RESULT_COLOURS = {
    "PASS": ("#22c55e", "#1a3d2b"),
    "WARN": ("#eab308", "#3d3010"),
    "FAIL": ("#ef4444", "#3d1a1a"),
}


class ValidationView(QWidget):
    """Validation report view — PASS/WARN/FAIL checks table + review editor.

    Signals:
        run_validation_requested: User clicked "Run Validation".
        upload_corpus_requested: User clicked "Upload Gold Corpus".
    """

    run_validation_requested = pyqtSignal()
    upload_corpus_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("validation_view")

        self._checks: List[Any] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Header row ───────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()
        hdr = QLabel("✅  Validation")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        hdr_row.addWidget(hdr)

        self._overall_label = QLabel("—")
        self._overall_label.setObjectName("validation_overall_label")
        self._overall_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #666;")
        self._overall_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hdr_row.addWidget(self._overall_label, stretch=1)
        root.addLayout(hdr_row)

        # ── Summary cards ────────────────────────────────────────────────────
        self._build_summary_cards(root)

        # ── Action buttons ───────────────────────────────────────────────────
        action_row = QHBoxLayout()
        self._upload_btn = QPushButton("📂  Upload Gold Corpus")
        self._upload_btn.setObjectName("validation_upload_btn")
        self._upload_btn.clicked.connect(self.upload_corpus_requested)
        action_row.addWidget(self._upload_btn)

        self._run_btn = QPushButton("▶  Run Validation")
        self._run_btn.setObjectName("validation_run_btn")
        self._run_btn.setStyleSheet(
            "QPushButton { background: #7c3aed; border: none; border-radius: 6px;"
            "  padding: 7px 18px; color: #fff; font-weight: bold; }"
            "QPushButton:hover { background: #6d28d9; }"
        )
        self._run_btn.clicked.connect(self.run_validation_requested)
        action_row.addWidget(self._run_btn)
        action_row.addStretch()

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color: #a0a0c0;")
        action_row.addWidget(filter_lbl)

        self._filter_combo = QComboBox()
        self._filter_combo.setObjectName("validation_filter_combo")
        self._filter_combo.addItems(["All", "PASS", "WARN", "FAIL"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        action_row.addWidget(self._filter_combo)
        root.addLayout(action_row)

        # ── Content splitter ─────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("validation_splitter")

        left = self._build_checks_panel()
        splitter.addWidget(left)

        right = self._build_review_panel()
        splitter.addWidget(right)
        splitter.setSizes([800, 300])
        splitter.setHandleWidth(2)

        root.addWidget(splitter, stretch=1)

    # ── Build helpers ─────────────────────────────────────────────────────────

    def _build_summary_cards(self, parent: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(10)
        self._summary_cards: dict[str, tuple[QFrame, QLabel]] = {}
        for result in ("PASS", "WARN", "FAIL"):
            card = QFrame()
            card.setObjectName(f"validation_card_{result.lower()}")
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setFixedHeight(70)
            text_col, bg_col = _RESULT_COLOURS[result]
            card.setStyleSheet(
                f"QFrame#{card.objectName()} {{"
                f"  background: {bg_col};"
                f"  border: 1px solid {text_col}40;"
                f"  border-radius: 8px;"
                "}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            title = QLabel(result)
            title.setStyleSheet(f"color: {text_col}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
            val = QLabel("0")
            val.setObjectName(f"validation_card_{result.lower()}_count")
            val.setStyleSheet(f"color: {text_col}; font-size: 22px; font-weight: bold;")
            card_layout.addWidget(title)
            card_layout.addWidget(val)
            row.addWidget(card)
            self._summary_cards[result] = (card, val)
        parent.addLayout(row)

    def _build_checks_panel(self) -> QWidget:
        from kadima.ui.widgets.check_table import CheckTable

        panel = QWidget()
        panel.setObjectName("validation_checks_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self._check_table = CheckTable()
        self._check_table.selectionModel().currentRowChanged.connect(self._on_check_selected)
        layout.addWidget(self._check_table)

        self._empty_label = QLabel("Upload gold corpus and run validation")
        self._empty_label.setObjectName("validation_empty_label")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #555; font-size: 14px; padding: 40px;")
        layout.addWidget(self._empty_label)

        return panel

    def _build_review_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("validation_review_panel")
        panel.setStyleSheet("QWidget#validation_review_panel { background: #16162a; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        hdr = QLabel("Review")
        hdr.setStyleSheet("color: #a0a0c0; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(hdr)

        self._review_detail = QTextEdit()
        self._review_detail.setObjectName("validation_review_detail")
        self._review_detail.setReadOnly(True)
        self._review_detail.setMaximumHeight(140)
        self._review_detail.setStyleSheet(
            "QTextEdit { background: #1e1e2e; border: 1px solid #3d3d5c;"
            "  border-radius: 4px; color: #e0e0e0; padding: 6px; }"
        )
        layout.addWidget(self._review_detail)

        notes_lbl = QLabel("Notes")
        notes_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px; font-weight: 600;")
        layout.addWidget(notes_lbl)

        self._notes_edit = QTextEdit()
        self._notes_edit.setObjectName("validation_notes_edit")
        self._notes_edit.setPlaceholderText("Add review notes…")
        self._notes_edit.setStyleSheet(
            "QTextEdit { background: #1e1e2e; border: 1px solid #3d3d5c;"
            "  border-radius: 4px; color: #e0e0e0; padding: 6px; }"
        )
        layout.addWidget(self._notes_edit, stretch=1)

        self._export_btn = QPushButton("📥  Export Report")
        self._export_btn.setObjectName("validation_export_btn")
        self._export_btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px;"
            "  padding: 6px 12px; color: #e0e0e0; }"
            "QPushButton:hover { background: #7c3aed; }"
        )
        self._export_btn.clicked.connect(self._export_report)
        layout.addWidget(self._export_btn)

        return panel

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_filter_changed(self, text: str) -> None:
        self._check_table.set_result_filter("" if text == "All" else text)

    def _on_check_selected(self) -> None:
        sel = self._check_table.selectionModel().currentIndex()
        if not sel.isValid():
            self._review_detail.clear()
            return
        check = self._check_table.check_at_proxy_row(sel.row())
        if check is None:
            return
        if isinstance(check, dict):
            lines = [f"<b>{k}:</b> {v}" for k, v in check.items()]
        else:
            lines = [
                f"<b>Type:</b> {getattr(check, 'check_type', '—')}",
                f"<b>File:</b> {getattr(check, 'file_id', '—')}",
                f"<b>Item:</b> {getattr(check, 'item', '—')}",
                f"<b>Expected:</b> {getattr(check, 'expected', '—')}",
                f"<b>Actual:</b> {getattr(check, 'actual', '—')}",
                f"<b>Result:</b> {getattr(check, 'result', '—')}",
            ]
        self._review_detail.setHtml("<br>".join(lines))

    def _export_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Validation Report", "validation_report.csv", "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Type", "File", "Item", "Expected", "Actual", "Result"])
                for ch in self._checks:
                    if isinstance(ch, dict):
                        writer.writerow([
                            ch.get("check_type", ""), ch.get("file_id", ""),
                            ch.get("item", ""), ch.get("expected", ""),
                            ch.get("actual", ""), ch.get("result", ""),
                        ])
                    else:
                        writer.writerow([
                            getattr(ch, "check_type", ""), getattr(ch, "file_id", ""),
                            getattr(ch, "item", ""), getattr(ch, "expected", ""),
                            getattr(ch, "actual", ""), getattr(ch, "result", ""),
                        ])
            logger.info("Validation report exported to %s", path)
        except Exception as exc:
            logger.error("Export failed: %s", exc)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_results(self, checks: List[Any]) -> None:
        """Populate the view from a list of CheckResult objects or dicts.

        Args:
            checks: List of CheckResult dataclasses or dicts.
        """
        self._checks = checks or []
        self._check_table.load(self._checks)

        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for ch in self._checks:
            result = ch.get("result") if isinstance(ch, dict) else getattr(ch, "result", "")
            if result in counts:
                counts[result] += 1

        for result, (_card, val_lbl) in self._summary_cards.items():
            val_lbl.setText(str(counts[result]))

        # Overall status
        if counts["FAIL"] > 0:
            self._overall_label.setText("FAIL ✗")
            self._overall_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ef4444;")
        elif counts["WARN"] > 0:
            self._overall_label.setText("WARN ⚠")
            self._overall_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #eab308;")
        elif counts["PASS"] > 0:
            self._overall_label.setText("PASS ✓")
            self._overall_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #22c55e;")
        else:
            self._overall_label.setText("—")
            self._overall_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #666;")

        has_data = bool(self._checks)
        self._check_table.setVisible(has_data)
        self._empty_label.setVisible(not has_data)

    def refresh(self) -> None:
        """Reload last set of checks (no-op if none loaded)."""
        if self._checks:
            self.load_results(self._checks)
