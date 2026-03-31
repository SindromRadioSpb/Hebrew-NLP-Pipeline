# kadima/ui/widgets/audio_player.py
"""AudioPlayer — compact widget for WAV/MP3 playback.

Used by GenerativeView (TTS tab) to play back synthesized audio.
Falls back gracefully if Qt multimedia is not available.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

try:
    from PyQt6.QtCore import pyqtSignal, QUrl
    from PyQt6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QWidget,
    )
    from PyQt6.QtCore import Qt
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

_HAS_MULTIMEDIA = False
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    _HAS_MULTIMEDIA = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class AudioPlayer(QWidget):
    """Compact audio player widget.

    Provides Play/Stop buttons, a position slider, and a duration label.
    Requires PyQt6-Qt6-Multimedia. If unavailable, shows a "No multimedia"
    placeholder that still emits signals so callers can open externally.

    Signals:
        play_requested(str): Emitted when Play is clicked. Argument: file path.
        stop_requested: Emitted when Stop is clicked.
    """

    play_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("audio_player")

        self._path: Optional[Path] = None
        self._player: Optional[object] = None
        self._audio_output: Optional[object] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("audio_player_play_btn")
        self._play_btn.setFixedWidth(36)
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._on_play)
        layout.addWidget(self._play_btn)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setObjectName("audio_player_stop_btn")
        self._stop_btn.setFixedWidth(36)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        layout.addWidget(self._stop_btn)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setObjectName("audio_player_slider")
        self._slider.setEnabled(False)
        layout.addWidget(self._slider, stretch=1)

        self._duration_lbl = QLabel("0:00")
        self._duration_lbl.setObjectName("audio_player_duration")
        self._duration_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        layout.addWidget(self._duration_lbl)

        if not _HAS_MULTIMEDIA:
            self._duration_lbl.setText("(no multimedia)")
        else:
            self._init_player()

    def _init_player(self) -> None:
        """Initialise QMediaPlayer if multimedia is available."""
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._slider.sliderMoved.connect(self._player.setPosition)

    def load(self, path: Union[str, Path]) -> None:
        """Load an audio file into the player.

        Args:
            path: Path to WAV or MP3 file.
        """
        self._path = Path(path)
        self._play_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        if _HAS_MULTIMEDIA and self._player is not None:
            self._player.setSource(QUrl.fromLocalFile(str(self._path)))
        logger.debug("AudioPlayer loaded: %s", self._path)

    def _on_play(self) -> None:
        if self._path:
            self.play_requested.emit(str(self._path))
        if _HAS_MULTIMEDIA and self._player is not None:
            self._player.play()

    def _on_stop(self) -> None:
        self.stop_requested.emit()
        if _HAS_MULTIMEDIA and self._player is not None:
            self._player.stop()

    def _on_duration_changed(self, duration_ms: int) -> None:
        self._slider.setMaximum(duration_ms)
        total_sec = duration_ms // 1000
        self._duration_lbl.setText(f"{total_sec // 60}:{total_sec % 60:02d}")

    def _on_position_changed(self, position_ms: int) -> None:
        self._slider.setValue(position_ms)

    def clear(self) -> None:
        """Unload current audio and reset controls."""
        self._path = None
        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._slider.setValue(0)
        self._duration_lbl.setText("0:00")
        if _HAS_MULTIMEDIA and self._player is not None:
            self._player.stop()
