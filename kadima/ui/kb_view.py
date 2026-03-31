# kadima/ui/kb_view.py
"""Knowledge Base view — T3 Step 6.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.5

Zones:
  Left panel:
    - Search bar (QLineEdit) + type QComboBox (surface/canonical/definition/embedding)
    - Search button
    - Results table (surface, pos, definition truncated, source_corpus_id)

  Right panel (splitter):
    - Term detail: Surface/Canonical/Lemma/POS/Features labels
    - Definition QTextEdit (editable, RTL)
    - Save Definition + Generate Definition buttons
    - Related terms table (from kb_relations)
    - Cluster button

Embedding search requires NeoDictaBERT — graceful fallback to text search.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QPushButton,
        QSplitter,
        QTableView,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_KADIMA_HOME = __import__("os").environ.get(
    "KADIMA_HOME", __import__("os.path", fromlist=["expanduser"]).expanduser("~/.kadima")
)
_DB_PATH = __import__("os.path", fromlist=["join"]).join(_KADIMA_HOME, "kadima.db")

_SEARCH_TYPES = ["surface", "canonical", "definition", "embedding"]
_RESULT_COLS = ["Surface", "POS", "Definition", "Corpus"]


class KBResultModel(QAbstractTableModel):
    """Model for KBTerm search results."""

    COLUMNS = _RESULT_COLS

    def __init__(self, terms: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._terms: List[Any] = terms or []

    def load(self, terms: List[Any]) -> None:
        self.beginResetModel()
        self._terms = terms or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._terms)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        t = self._terms[index.row()]
        col = index.column()
        get = (lambda k: t.get(k) if isinstance(t, dict) else getattr(t, k, None))
        if col == 0:
            return str(get("surface") or "")
        if col == 1:
            return str(get("pos") or "")
        if col == 2:
            defn = get("definition") or ""
            return str(defn)[:80] + ("…" if len(str(defn)) > 80 else "")
        if col == 3:
            return str(get("source_corpus_id") or "")
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def term_at(self, row: int) -> Any:
        if 0 <= row < len(self._terms):
            return self._terms[row]
        return None


class KBView(QWidget):
    """Knowledge Base view — text/embedding/similar search + definition editor.

    Signals:
        term_selected(object): A KBTerm was selected in the results table.
    """

    term_selected = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("kb_view")
        self._current_term: Any = None

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("kb_splitter")
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([500, 400])
        splitter.setHandleWidth(2)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)

    # ── Build helpers ─────────────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("kb_left_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 6, 10)
        layout.setSpacing(8)

        hdr = QLabel("📚  Knowledge Base")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(hdr)

        # Search bar
        search_row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("kb_search_edit")
        self._search_edit.setPlaceholderText("חפש מונח…")
        self._search_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._search_edit.setStyleSheet(
            "QLineEdit { background: #2d2d44; border: 1px solid #3d3d5c; border-radius: 4px;"
            "  padding: 5px 8px; color: #e0e0e0; }"
            "QLineEdit:focus { border-color: #7c3aed; }"
        )
        self._search_edit.returnPressed.connect(self._do_search)
        search_row.addWidget(self._search_edit, stretch=1)

        self._search_type = QComboBox()
        self._search_type.setObjectName("kb_search_type_combo")
        self._search_type.addItems(_SEARCH_TYPES)
        search_row.addWidget(self._search_type)

        self._search_btn = QPushButton("🔍")
        self._search_btn.setObjectName("kb_search_btn")
        self._search_btn.setStyleSheet(
            "QPushButton { background: #7c3aed; border: none; border-radius: 4px;"
            "  padding: 6px 12px; color: #fff; font-weight: bold; }"
            "QPushButton:hover { background: #6d28d9; }"
        )
        self._search_btn.clicked.connect(self._do_search)
        search_row.addWidget(self._search_btn)
        layout.addLayout(search_row)

        # Results count label
        self._result_count = QLabel("Search for terms in the Knowledge Base")
        self._result_count.setObjectName("kb_result_count")
        self._result_count.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._result_count)

        # Results table
        self._result_model = KBResultModel()
        self._result_view = QTableView()
        self._result_view.setObjectName("kb_results_table")
        self._result_view.setModel(self._result_model)
        self._result_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._result_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._result_view.setAlternatingRowColors(True)
        self._result_view.verticalHeader().hide()
        self._result_view.setShowGrid(False)
        hh = self._result_view.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._result_view.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0; border: none; padding: 4px 8px; font-size: 11px; }"
        )
        self._result_view.selectionModel().currentRowChanged.connect(self._on_term_selected)
        layout.addWidget(self._result_view, stretch=1)

        return panel

    def _build_right(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("kb_right_panel")
        panel.setStyleSheet("QWidget#kb_right_panel { background: #16162a; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 10, 10, 10)
        layout.setSpacing(8)

        # Term header labels
        self._term_surface_lbl = QLabel("—")
        self._term_surface_lbl.setObjectName("kb_term_surface")
        self._term_surface_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #e0e0e0; direction: rtl;"
        )
        self._term_surface_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self._term_surface_lbl)

        self._term_meta_lbl = QLabel("—")
        self._term_meta_lbl.setObjectName("kb_term_meta")
        self._term_meta_lbl.setStyleSheet("color: #a0a0c0; font-size: 12px;")
        self._term_meta_lbl.setWordWrap(True)
        layout.addWidget(self._term_meta_lbl)

        # Definition group
        defn_group = QGroupBox("Definition")
        defn_group.setObjectName("kb_defn_group")
        defn_group.setStyleSheet(
            "QGroupBox { color: #a0a0c0; font-size: 11px; font-weight: 600;"
            "  border: 1px solid #3d3d5c; border-radius: 6px; margin-top: 8px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        defn_layout = QVBoxLayout(defn_group)

        self._defn_edit = QTextEdit()
        self._defn_edit.setObjectName("kb_defn_edit")
        self._defn_edit.setPlaceholderText("…הגדרה")
        self._defn_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._defn_edit.setMaximumHeight(120)
        self._defn_edit.setStyleSheet(
            "QTextEdit { background: #1e1e2e; border: 1px solid #3d3d5c;"
            "  border-radius: 4px; color: #e0e0e0; padding: 6px; }"
        )
        defn_layout.addWidget(self._defn_edit)

        btn_row = QHBoxLayout()
        self._save_defn_btn = QPushButton("💾  Save")
        self._save_defn_btn.setObjectName("kb_save_defn_btn")
        self._save_defn_btn.setEnabled(False)
        self._save_defn_btn.clicked.connect(self._save_definition)
        btn_row.addWidget(self._save_defn_btn)

        self._gen_defn_btn = QPushButton("🤖  Generate")
        self._gen_defn_btn.setObjectName("kb_gen_defn_btn")
        self._gen_defn_btn.setEnabled(False)
        self._gen_defn_btn.clicked.connect(self._generate_definition)
        btn_row.addWidget(self._gen_defn_btn)
        btn_row.addStretch()
        defn_layout.addLayout(btn_row)
        layout.addWidget(defn_group)

        # Related terms
        related_group = QGroupBox("Related Terms")
        related_group.setObjectName("kb_related_group")
        related_group.setStyleSheet(
            "QGroupBox { color: #a0a0c0; font-size: 11px; font-weight: 600;"
            "  border: 1px solid #3d3d5c; border-radius: 6px; margin-top: 8px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        related_layout = QVBoxLayout(related_group)

        self._related_table = QTableView()
        self._related_table.setObjectName("kb_related_table")
        self._related_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._related_table.setMaximumHeight(120)
        self._related_table.verticalHeader().hide()
        self._related_table.setShowGrid(False)
        self._related_table.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0; border: none; padding: 3px 6px; }"
        )
        related_layout.addWidget(self._related_table)

        cluster_row = QHBoxLayout()
        self._cluster_btn = QPushButton("📊  Cluster")
        self._cluster_btn.setObjectName("kb_cluster_btn")
        self._cluster_btn.setEnabled(False)
        self._cluster_btn.clicked.connect(self._run_clustering)
        cluster_row.addWidget(self._cluster_btn)
        cluster_row.addStretch()
        related_layout.addLayout(cluster_row)
        layout.addWidget(related_group)

        layout.addStretch()
        return panel

    # ── Search logic ──────────────────────────────────────────────────────────

    def _do_search(self) -> None:
        query = self._search_edit.text().strip()
        if not query:
            return
        search_type = self._search_type.currentText()
        terms: List[Any] = []
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                if search_type in ("surface", "canonical", "definition"):
                    col = search_type
                    rows = conn.execute(
                        f"SELECT * FROM kb_terms WHERE {col} LIKE ? LIMIT 50",
                        (f"%{query}%",),
                    ).fetchall()
                    terms = [dict(r) for r in rows]
                else:
                    # embedding search — fall back to surface if no torch
                    try:
                        import numpy as np
                        import torch
                        from kadima.kb.search import KBSearch
                        from kadima.kb.repository import KBRepository

                        repo = KBRepository(conn)
                        search = KBSearch(repo)
                        # Encode query via KadimaTransformer
                        from kadima.nlp.components.transformer_component import KadimaTransformer

                        kt = KadimaTransformer.from_config({"model_name": "dicta-il/dictabert"})
                        doc = kt.nlp.make_doc(query)
                        kt(doc)
                        vec = doc.tensor.mean(axis=0) if doc.tensor is not None else None
                        if vec is not None:
                            results = search.search_by_embedding(vec, top_k=20)
                            terms = [r[0] for r in results]
                        else:
                            raise ValueError("No tensor")
                    except Exception as emb_exc:
                        logger.debug("Embedding search unavailable: %s — falling back", emb_exc)
                        rows = conn.execute(
                            "SELECT * FROM kb_terms WHERE surface LIKE ? LIMIT 50",
                            (f"%{query}%",),
                        ).fetchall()
                        terms = [dict(r) for r in rows]
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("KB search error: %s", exc)
            self._result_count.setText(f"Error: {exc}")
            return

        self._result_model.load(terms)
        n = len(terms)
        self._result_count.setText(
            f"{n} term{'s' if n != 1 else ''} found"
            if n else "No terms found."
        )

    # ── Selection & edit ──────────────────────────────────────────────────────

    def _on_term_selected(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if not current.isValid():
            self._clear_detail()
            return
        term = self._result_model.term_at(current.row())
        if term is None:
            return
        self._current_term = term
        self._show_term_detail(term)
        self.term_selected.emit(term)

    def _show_term_detail(self, term: Any) -> None:
        get = (lambda k: term.get(k) if isinstance(term, dict) else getattr(term, k, None))
        surface = get("surface") or "—"
        canonical = get("canonical") or ""
        lemma = get("lemma") or ""
        pos = get("pos") or ""
        features = get("features") or {}
        definition = get("definition") or ""

        self._term_surface_lbl.setText(surface)
        meta_parts = []
        if canonical and canonical != surface:
            meta_parts.append(f"Canonical: {canonical}")
        if lemma:
            meta_parts.append(f"Lemma: {lemma}")
        if pos:
            meta_parts.append(f"POS: {pos}")
        if features:
            meta_parts.append(f"Features: {features}")
        self._term_meta_lbl.setText("  ·  ".join(meta_parts) or "—")
        self._defn_edit.setPlainText(str(definition))

        self._save_defn_btn.setEnabled(True)
        self._gen_defn_btn.setEnabled(True)
        self._cluster_btn.setEnabled(True)
        self._load_related(term)

    def _clear_detail(self) -> None:
        self._current_term = None
        self._term_surface_lbl.setText("—")
        self._term_meta_lbl.setText("—")
        self._defn_edit.clear()
        self._save_defn_btn.setEnabled(False)
        self._gen_defn_btn.setEnabled(False)
        self._cluster_btn.setEnabled(False)

    def _load_related(self, term: Any) -> None:
        get = (lambda k: term.get(k) if isinstance(term, dict) else getattr(term, k, None))
        term_id = get("id")
        if term_id is None:
            return
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                rows = conn.execute(
                    "SELECT r.relation_type, t2.surface AS related_surface"
                    " FROM kb_relations r"
                    " JOIN kb_terms t2 ON t2.id = r.target_id"
                    " WHERE r.source_id = ? LIMIT 20",
                    (term_id,),
                ).fetchall()
            finally:
                conn.close()
            # Simple display via QTableView — create a small inline model
            related = [{"Type": r["relation_type"], "Related": r["related_surface"]} for r in rows]
            self._related_table.setModel(_DictListModel(related, ["Type", "Related"]))
            self._related_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )
        except Exception as exc:
            logger.debug("Could not load related terms: %s", exc)

    def _save_definition(self) -> None:
        if self._current_term is None:
            return
        get = (lambda k: self._current_term.get(k) if isinstance(self._current_term, dict)
               else getattr(self._current_term, k, None))
        term_id = get("id")
        if term_id is None:
            return
        definition = self._defn_edit.toPlainText().strip()
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                conn.execute(
                    "UPDATE kb_terms SET definition=? WHERE id=?", (definition, term_id)
                )
                conn.commit()
            finally:
                conn.close()
            logger.info("Saved definition for term %d", term_id)
        except Exception as exc:
            logger.error("Could not save definition: %s", exc)

    def _generate_definition(self) -> None:
        """Trigger LLM definition generation (stub — requires llm/service.py)."""
        logger.info("Generate definition requested (LLM not connected in Step 6)")

    def _run_clustering(self) -> None:
        """Trigger term clustering (requires TermClusterer)."""
        logger.info("Cluster requested (TermClusterer integration pending)")

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Re-run last search if any."""
        if self._search_edit.text().strip():
            self._do_search()

    def search(self, query: str, search_type: str = "surface") -> None:
        """Programmatically trigger a search.

        Args:
            query: Search query string.
            search_type: One of surface / canonical / definition / embedding.
        """
        self._search_edit.setText(query)
        idx = _SEARCH_TYPES.index(search_type) if search_type in _SEARCH_TYPES else 0
        self._search_type.setCurrentIndex(idx)
        self._do_search()


# ── Inline dict-list model ────────────────────────────────────────────────────


class _DictListModel(QAbstractTableModel):
    """Minimal model for a list of uniform dicts (for related terms)."""

    def __init__(self, rows: List[dict], columns: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows = rows
        self._columns = columns

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return str(self._rows[index.row()].get(self._columns[index.column()], ""))

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._columns[section]
        return None
