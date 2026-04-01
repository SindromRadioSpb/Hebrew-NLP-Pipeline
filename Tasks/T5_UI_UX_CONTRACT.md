# T5 UI UX Contract — nlp_tools_view + llm_view

> Applies to: Step 13 (`nlp_tools_view.py`), Step 14 (`llm_view.py`), Step 15 (tests).
> Status: **Policy defined** (not yet Operational).

---

## Screen Template

All T5 views follow the same structural pattern as `generative_view.py`:

```
QVBoxLayout (root, margins=12)
├── Title QLabel  (font-size 16px bold, color #e0e0e0)
│   objectName: <view>_title
└── QTabWidget
    objectName: <view>_tabs
    └── per tab: QWidget  (margins=8, spacing=6)
        ├── BackendSelector or mode selector
        ├── RTLTextEdit input  (objectName: <view>_<tab>_input)
        ├── QHBoxLayout buttons
        │   ├── Run QPushButton   (objectName: <view>_<tab>_run_btn)
        │   ├── Clear QPushButton (objectName: <view>_<tab>_clear_btn)
        │   └── Copy QPushButton  (optional)
        ├── Result area (RTLTextEdit or QListWidget)
        │   objectName: <view>_<tab>_result
        └── Status QLabel        (objectName: <view>_<tab>_status)
```

**LLMView exception:** uses `QSplitter` (left=presets, right=ChatWidget) instead of QTabWidget.

---

## Background Worker Pattern

Re-use `GenerativeWorker` from `kadima.ui.generative_view` for engine-module tasks.
Use `_LLMWorker` (defined locally in `llm_view.py`) for LLM service calls.

```python
worker = GenerativeWorker(
    tab_name="<tab>",
    module_cls=_SomeCls,
    module_config={},
    input_data=text,
    runtime_config={"backend": backend},
)
worker.signals.started.connect(lambda t: status.setText("Running..."))
worker.signals.finished.connect(self._on_<tab>_result)
worker.signals.failed.connect(lambda t, e: status.setText(f"Error: {e}"))
QThreadPool.globalInstance().start(worker)
```

**Rule:** Never call engine modules or LLMService from the main thread.

---

## Error Pattern

```python
def _on_<tab>_result(self, tab_name: str, result: Any) -> None:
    status.setText("Done")
    try:
        # access result.data fields
        ...
    except Exception as exc:
        logger.warning("<tab> result display error: %s", exc)
        status.setText(f"Display error: {exc}")
```

Module unavailable → disable Run button at build time:
```python
if _SomeCls is None:
    run_btn.setEnabled(False)
    run_btn.setToolTip("<Module> not available (install [ml] extras)")
```

---

## Export / Copy Pattern

Each tab with text output has a **Copy Result** button:
```python
copy_btn.clicked.connect(
    lambda: QApplication.clipboard().setText(result_edit.toPlainText())
)
```

---

## Smoke Test Checklist (per view)

| # | Check | How |
|---|-------|-----|
| 1 | View instantiates without crash | `view = SomeView()` |
| 2 | objectName set | `view.objectName() == "some_view"` |
| 3 | Tab widget found by name | `findChild(QTabWidget, "some_tabs")` |
| 4 | Correct tab count | `tab.count() == N` |
| 5 | Key widgets exist by objectName | `findChild(QWidget, "some_tab_run_btn")` |
| 6 | Run buttons disabled when module unavailable | `btn.isEnabled() == False` (if no ML) |
| 7 | Signals declared | `hasattr(view, "some_signal")` |
| 8 | `show()` / `hide()` does not crash | call both |
| 9 | `refresh()` does not crash | `view.refresh()` |

All tests: `pytest.importorskip("PyQt6")` guard + `qapp` fixture.

---

## objectName Conventions

| Widget | Pattern | Example |
|--------|---------|---------|
| View root | `<view>_view` | `nlp_tools_view` |
| Tab widget | `<view>_tabs` | `nlp_tools_tabs` |
| Tab input | `<view>_<tab>_input` | `nlp_tools_grammar_input` |
| Tab result | `<view>_<tab>_result` | `nlp_tools_grammar_result` |
| Run button | `<view>_<tab>_run_btn` | `nlp_tools_keyphrase_run_btn` |
| Clear button | `<view>_<tab>_clear_btn` | `nlp_tools_summarize_clear_btn` |
| Status label | `<view>_<tab>_status` | `nlp_tools_grammar_status` |
| ChatWidget | `chat_widget` | — |
| Chat input | `chat_input` | — |
| Chat send btn | `chat_send_btn` | — |
| LLM mode combo | `llm_mode_combo` | — |
| LLM context input | `llm_context_input` | — |
| LLM run button | `llm_run_btn` | — |
| LLM status label | `llm_server_status` | — |
