# Every time I worked on it
# 4-17-26 1:45 AM
# 4-17-26 11:23 PM
import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap, QFont, QCloseEvent, QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QPushButton,
    QCheckBox,
    QSlider,
    QListWidget,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QLineEdit,
    QTabWidget,
    QListWidgetItem,
    QColorDialog,
    QGridLayout,
    QInputDialog,
)
import json
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import Picture
import base64
import requests
import vlc
import time
import random

APPDATA_ROOT = os.getenv("APPDATA") or str(Path.home())
APPDATA_DIR = os.path.join(APPDATA_ROOT, "errorC003C004", "Music Player")
SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.json")
BLANK_PATH = os.path.join(APPDATA_DIR, "blank.png")
cover_path = BLANK_PATH
os.makedirs(APPDATA_DIR, exist_ok=True)


if not os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump({"Current Preset": "Default"}, f, indent=2)

    PROFILE_NAME = "Default"
else:

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    PROFILE_NAME = data.get("Current Preset", "Default")

if not os.path.exists(BLANK_PATH):
    try: 
        get = requests.get("https://github.com/errorC003C004/Yet-Another-Music-Player/blob/main/no_image.png?raw=true", stream=True).raw
        with open(BLANK_PATH, "wb") as f:
            f.write(get.read())
    except Exception as e:
        print("Cant Download Blank Image: ", e)

PROFILE_DIR = os.path.join(APPDATA_DIR, PROFILE_NAME)
TEMP_DIR = os.path.join(PROFILE_DIR, "Temp")
MEDIA_DIR = os.path.join(PROFILE_DIR, "Media")
PRESET_PATH = os.path.join(PROFILE_DIR, "preset.json")

os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

def create_auto_preset():
    os.makedirs(PROFILE_DIR, exist_ok=True)

    if not os.path.exists(PRESET_PATH):
        with open(PRESET_PATH, "w", encoding="utf-8") as f:
            json.dump({"preset": {}, "songs": [], "theme": {}}, f, indent=2)

def _load_auto_preset(w) -> None:
    if not os.path.exists(PRESET_PATH):
        create_auto_preset()
        return
    try:
        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        w._apply_preset_to_ui(data)
    except Exception as e:
        print("Auto-load failed:", e)



@dataclass
class Preset:
    muted: bool = False
    shuffle: bool = True
    repeat: bool = False
    current_song: int = 0
    volume: float = 100 


class Audio:
    def __init__(self, player) -> None:
        super().__init__()
        self.instance = vlc.Instance(
            "--file-caching=300",
            "--network-caching=300"
        )
        self.audio_player = self.instance.media_player_new()
        self.history = deque(maxlen=50)
        self.recent_shuffle = deque(maxlen=10)

        self.player = player
        self.preset = Preset()

        self._event_manager = self.audio_player.event_manager()
        self._event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_song_end
        )

    def get_current_song(self):
        songs = self.player.get_song_list()
        index = getattr(self.player, "current_song", 0)

        if not songs:
            return None

        if index < 0 or index >= len(songs):
            index = 0
            self.player.current_song = 0
            self.preset.current_song = 0

        return songs[index]

    def get_data(self):
        current_song = self.get_current_song()
        if not current_song:
            return "Unknown Artist", "Unknown Title", BLANK_PATH

        try:
            audio = OggVorbis(current_song)
            artist = audio.get("artist", ["Unknown Artist"])[0]
            title = audio.get("title", ["Unknown Title"])[0]
            pics = audio.get("metadata_block_picture")

            if pics:
                os.makedirs(TEMP_DIR, exist_ok=True)
                raw_block = base64.b64decode(pics[0])
                pic = Picture(raw_block)

                ext = "jpg" if pic.mime in ("image/jpeg", "image/jpg") else "png"
                cover_path = os.path.join(TEMP_DIR, f"cover.{ext}")
                with open(cover_path, "wb") as f:
                    f.write(pic.data)
            else:
                cover_path = BLANK_PATH
                print("No embedded cover art found")

            return artist, title, cover_path

        except Exception as e:
            print("Failed to read metadata:", e)
            return "Unknown Artist", os.path.basename(current_song), BLANK_PATH

    def play(self):
        song = self.get_current_song()
        if not song:
            QMessageBox.warning(self.player, "No songs", "No songs are loaded.")
            return

        artist, title, cover_path = self.get_data()

        if not hasattr(self, "_current_media_path") or self._current_media_path != song:
            self._current_media = self.instance.media_new(song)
            self._current_media_path = song
            self.audio_player.set_media(self._current_media)

        self.audio_player.play()

        self.player._set_now_playing_info(artist, title)
        self.player.setWindowTitle(
            f"Yet Another Music Player - {self.player._get_current_preset_name()} - {artist} - {title}"
        )

        print(f"Current song: {os.path.basename(song)}")

        pixmap = QPixmap(cover_path)
        self.player.label.setPixmap(pixmap)
        self.player.cover_path = cover_path

        row = self.player.current_song
        if 0 <= row < self.player.song_list.count():
            self.player.song_list.setCurrentRow(row)

    def stop(self):
        self.audio_player.stop()
        self.player.position_slider.setRange(0, 0)
        self.player.position_slider.setValue(0)
        self.player.time_label.setText("0:00 / 0:00")

    def pause(self):
        if self.audio_player.is_playing():
            self.player.pause_btn.setText("Resume")
            self.audio_player.pause()
        else:
            self.player.pause_btn.setText("Pause")
            self.audio_player.pause()

    def shuffle(self):
        self.preset.shuffle = not self.preset.shuffle

    def repeat(self):
        self.preset.repeat = not self.preset.repeat

    def mute(self):
        self.preset.muted = not self.preset.muted
        self.audio_player.audio_set_volume(0 if self.preset.muted else int(self.preset.volume))

    def volume(self, volume: float):
        if self.preset.muted:
            self.audio_player.audio_set_volume(0)
            return
        self.preset.volume = volume
        self.audio_player.audio_set_volume(int(volume))

    def next(self):
        songs = self.player.get_song_list()
        if not songs:
            return

        old_index = self.player.current_song

        if self.preset.shuffle:
            if len(songs) == 1:
                new_index = 0
            else:
                blocked = set(self.recent_shuffle)
                blocked.add(old_index)

                choices = [i for i in range(len(songs)) if i not in blocked]

                if not choices:
                    choices = [i for i in range(len(songs)) if i != old_index]

                if not choices:
                    choices = [old_index]

                new_index = random.choice(choices)
        else:
            new_index = (old_index + 1) % len(songs)

        self.history.append(old_index)
        self.player.current_song = new_index
        self.preset.current_song = new_index

        if self.preset.shuffle:
            self.recent_shuffle.append(new_index)

        self.play()

    def back(self):
        songs = self.player.get_song_list()
        if not songs:
            return

        if self.history:
            self.player.current_song = self.history.pop()
        else:
            self.player.current_song = (self.player.current_song - 1) % len(songs)

        self.preset.current_song = self.player.current_song
        self.play()

    def _on_song_end(self):
        songs = self.player.get_song_list()
        if not songs:
            return

        def advance():
            if self.preset.repeat:
                self.play()
            else:
                self.next()

        QTimer.singleShot(0, advance)

    def get_time(self):
        length_ms = self.audio_player.get_length()
        time_ms = self.audio_player.get_time()

        if length_ms <= 0:
            return 0, 0

        if time_ms < 0:
            time_ms = 0

        full_time = length_ms // 1000
        current_time = time_ms // 1000
        return full_time, current_time

    def set_time(self, seconds: int):
        if seconds < 0:
            seconds = 0
        self.audio_player.set_time(seconds * 1000)



class Player(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.engine = Audio(self)
        self.songs: Dict[str, Dict] = {}
        self._loading_ui = False
        self.cover_path = BLANK_PATH
        self.current_song = self.engine.preset.current_song

        self.setWindowTitle(f"Yet Another Music Player - {PROFILE_NAME}")
        self.setMinimumSize(1120, 720)
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        properties_tab = QWidget()
        properties_layout = QVBoxLayout(properties_tab)
        properties_layout.setContentsMargins(16, 16, 16, 16)
        properties_layout.setSpacing(14)

        songs_tab = QWidget()
        songs_layout = QVBoxLayout(songs_tab)
        songs_layout.setContentsMargins(16, 16, 16, 16)
        songs_layout.setSpacing(14)

        preset_tab = QWidget()
        preset_layout = QVBoxLayout(preset_tab)
        preset_layout.setContentsMargins(16, 16, 16, 16)
        preset_layout.setSpacing(14)

        self.tabs.addTab(properties_tab, "Player")
        self.tabs.addTab(songs_tab, "Library")
        self.tabs.addTab(preset_tab, "Preset")

        # =====================================================
        #                    SHARED WIDGETS
        # =====================================================
        self.mute_cb = QCheckBox("Mute")
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.back_btn = QPushButton("Previous")
        self.pause_btn = QPushButton("Pause")
        self.next_btn = QPushButton("Next")
        self.shuffle_cb = QCheckBox("Shuffle")
        self.repeat_cb = QCheckBox("Repeat")

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(int(self.engine.preset.volume))

        self.volume_value_label = QLabel(f"{int(self.engine.preset.volume)}%")
        self.volume_value_label.setObjectName("ValuePill")
        self.volume_value_label.setMinimumWidth(52)
        self.volume_value_label.setAlignment(Qt.AlignCenter)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("MutedLabel")

        self._dragging_position = False
        self.position_timer = QTimer(self)
        self.position_timer.setInterval(500)
        self.position_timer.timeout.connect(self._update_position_slider)
        self.position_timer.start()

        # =====================================================
        #                    COVER / NOW PLAYING
        # =====================================================
        self.label = QLabel()
        self.label.setObjectName("CoverArt")
        self.label.setFixedSize(260, 260)
        self.label.setScaledContents(True)
        self.pixmap = QPixmap(self.cover_path)
        self.label.setPixmap(self.pixmap)

        self.now_playing_title = QLabel("Nothing playing")
        self.now_playing_title.setObjectName("SongTitle")

        self.now_playing_artist = QLabel("Drag .ogg files into the window")
        self.now_playing_artist.setObjectName("MutedLabel")

        self.song_list = QListWidget()
        self.song_list.setObjectName("SongList")
        self.song_list.setMinimumHeight(260)

        # =====================================================
        #                    PLAYER TAB
        # =====================================================
        now_playing_group = QGroupBox("Now Playing")
        now_playing_layout = QHBoxLayout(now_playing_group)
        now_playing_layout.setSpacing(18)

        cover_col = QVBoxLayout()
        cover_col.addWidget(self.label, alignment=Qt.AlignTop)

        info_col = QVBoxLayout()
        info_col.setSpacing(10)
        info_col.addStretch(1)
        info_col.addWidget(self.now_playing_title)
        info_col.addWidget(self.now_playing_artist)

        progress_wrap = QVBoxLayout()
        progress_wrap.setSpacing(6)
        progress_wrap.addWidget(self.position_slider)

        progress_row = QHBoxLayout()
        progress_row.addWidget(self.time_label)
        progress_row.addStretch()
        progress_wrap.addLayout(progress_row)

        info_col.addLayout(progress_wrap)

        volume_group = QGroupBox("Volume")
        volume_layout = QHBoxLayout(volume_group)
        volume_layout.addWidget(self.volume_slider, 1)
        volume_layout.addWidget(self.volume_value_label)

        controls_group = QGroupBox("Playback")

        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(10)

        controls_layout_1 = QHBoxLayout()
        controls_layout_1.addWidget(self.play_btn)
        controls_layout_1.addWidget(self.stop_btn)

        controls_layout_2 = QHBoxLayout()
        controls_layout_2.addWidget(self.back_btn)
        controls_layout_2.addWidget(self.pause_btn)
        controls_layout_2.addWidget(self.next_btn)

        controls_layout.addLayout(controls_layout_1)
        controls_layout.addLayout(controls_layout_2)

        
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout(options_group)
        options_layout.addWidget(self.shuffle_cb)
        options_layout.addWidget(self.repeat_cb)
        options_layout.addWidget(self.mute_cb)
        options_layout.addStretch()

        info_col.addWidget(volume_group)
        info_col.addWidget(controls_group)
        info_col.addWidget(options_group)
        info_col.addStretch(2)

        now_playing_layout.addLayout(cover_col, 0)
        now_playing_layout.addLayout(info_col, 1)

        properties_layout.addWidget(now_playing_group)
        properties_layout.addStretch(1)

        # =====================================================
        #                    LIBRARY TAB
        # =====================================================
        library_group = QGroupBox("Songs")
        library_layout = QVBoxLayout(library_group)

        library_hint = QLabel("Drop .ogg files anywhere into the window")
        library_hint.setObjectName("Mut edLabel")

        library_layout.addWidget(library_hint)
        library_layout.addWidget(self.song_list, 1)

        songs_layout.addWidget(library_group, 1)

        # =====================================================
        #                    PRESET TAB
        # =====================================================
        preset_group = QGroupBox("Presets")
        group_layout = QVBoxLayout(preset_group)
        preset_layout.addWidget(preset_group)

        top = QHBoxLayout()
        self.preset_name = QLineEdit()
        self.preset_name.setText(PROFILE_NAME)
        self.preset_name.setPlaceholderText("Preset name")
        self.save_preset_btn = QPushButton("Save")

        top.addWidget(self.preset_name, 1)
        top.addWidget(self.save_preset_btn)

        bottom = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.load_preset_btn = QPushButton("Load")
        self.export_preset_btn = QPushButton("Set Default")

        bottom.addWidget(self.preset_combo, 1)
        bottom.addWidget(self.load_preset_btn)
        bottom.addWidget(self.export_preset_btn)

        group_layout.addLayout(top)
        group_layout.addLayout(bottom)
        preset_layout.addStretch(1)

        # =====================================================
        #                    CONNECTIONS
        # =====================================================
        self.play_btn.clicked.connect(self.engine.play)
        self.stop_btn.clicked.connect(self.engine.stop)
        self.back_btn.clicked.connect(self.engine.back)
        self.pause_btn.clicked.connect(self.engine.pause)
        self.next_btn.clicked.connect(self.engine.next)

        self.mute_cb.stateChanged.connect(self.mute_handler)
        self.mute_cb.setChecked(self.engine.preset.muted)
        self.shuffle_cb.setChecked(self.engine.preset.shuffle)
        self.repeat_cb.setChecked(self.engine.preset.repeat)
        self.shuffle_cb.stateChanged.connect(lambda _: self.engine.shuffle())
        self.repeat_cb.stateChanged.connect(lambda _: self.engine.repeat())

        self.volume_slider.valueChanged.connect(self.engine.volume)
        self.volume_slider.valueChanged.connect(self._update_volume_label)

        self._refresh_preset_dropdown()

        self.mute_cb.stateChanged.connect(self._apply_ui_to_engine)
        self.shuffle_cb.stateChanged.connect(self._apply_ui_to_engine)
        self.repeat_cb.stateChanged.connect(self._apply_ui_to_engine)
        self.volume_slider.valueChanged.connect(self._apply_ui_to_engine)
        self.position_slider.sliderPressed.connect(self._position_slider_pressed)
        self.position_slider.sliderMoved.connect(self._position_slider_moved)
        self.position_slider.sliderReleased.connect(self._position_slider_released)

        self.save_preset_btn.clicked.connect(self._save_preset_file)
        self.load_preset_btn.clicked.connect(self._load_preset_file)
        self.export_preset_btn.clicked.connect(self._export_current_preset)

        self.current_theme = DEFAULT_THEME.copy()
        apply_theme(QApplication.instance(), {"theme": self.current_theme})

    def _update_volume_label(self, value):
        self.volume_value_label.setText(f"{value}%")

    def _set_now_playing_info(self, artist: str, title: str):
        self.now_playing_title.setText(title or "Unknown Title")
        self.now_playing_artist.setText(artist or "Unknown Artist")

    def _position_slider_moved(self, value):
        full_time = self.position_slider.maximum()
        self.time_label.setText(
            f"{self._format_time(value)} / {self._format_time(full_time)}"
        )

    def _format_time(self, seconds: int) -> str:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    def _update_position_slider(self):
        if self._dragging_position:
            return

        full_time, current_time = self.engine.get_time()

        self.position_slider.blockSignals(True)
        self.position_slider.setRange(0, max(full_time, 0))
        self.position_slider.setValue(min(current_time, max(full_time, 0)))
        self.position_slider.blockSignals(False)

        self.time_label.setText(
            f"{self._format_time(current_time)} / {self._format_time(full_time)}"
        )

    def _position_slider_pressed(self):
        self._dragging_position = True

    def _position_slider_released(self):
        self._dragging_position = False
        self.engine.set_time(self.position_slider.value())
        self._update_position_slider()

    def mute_handler(self):
        self.engine.mute()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            if any(url.toLocalFile().lower().endswith(".ogg") for url in event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        added = False
        last_index = None

        for url in event.mimeData().urls():
            path = url.toLocalFile()

            if not path.lower().endswith(".ogg"):
                continue

            if not os.path.isfile(path):
                continue

            if any(d.get("path") == path for d in self.songs.values()):
                continue

            index = str(len(self.songs))
            self.songs[index] = {"path": path}
            self.song_list.addItem(os.path.basename(path))

            last_index = int(index)
            added = True
            print(f"Added: {path}")

        if last_index is not None:
            self.current_song = last_index
            self.engine.preset.current_song = last_index

            song_name = self._get_current_song_name()

            if os.path.exists(self.cover_path):
                pixmap = QPixmap(self.cover_path)
                self.label.setPixmap(pixmap)

            self.setWindowTitle(
                f"Yet Another Music Player - {self._get_current_preset_name()} - {song_name}"
            )

        if added:
            try:
                os.makedirs(os.path.dirname(PRESET_PATH), exist_ok=True)

                data = {}
                if os.path.exists(PRESET_PATH):
                    with open(PRESET_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)

                data["songs"] = [d["path"] for d in self.songs.values() if "path" in d]
                data.setdefault("preset", {})["current_song"] = self.current_song
                data.setdefault("theme", self.current_theme.copy())

                with open(PRESET_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

            except Exception as e:
                print("Failed to update preset songs:", e)

        if added:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _preset_folder(self, name: str) -> str:
        return os.path.join(APPDATA_DIR, name)

    def _preset_path(self, name: str) -> str:
        return os.path.join(self._preset_folder(name), "preset.json")

    def _settings_path(self) -> str:
        return os.path.join(APPDATA_DIR, "settings.json")

    def _set_current_preset_name(self, name: str) -> None:
        global PROFILE_NAME, PROFILE_DIR, TEMP_DIR, MEDIA_DIR, PRESET_PATH
        PROFILE_NAME = name
        PROFILE_DIR = os.path.join(APPDATA_DIR, PROFILE_NAME)
        TEMP_DIR = os.path.join(PROFILE_DIR, "Temp")
        MEDIA_DIR = os.path.join(PROFILE_DIR, "Media")
        PRESET_PATH = os.path.join(PROFILE_DIR, "preset.json")

        os.makedirs(PROFILE_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(MEDIA_DIR, exist_ok=True)

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data["Current Preset"] = name
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if hasattr(self, "preset_name"):
            self.preset_name.setText(name)

    def _get_current_preset_name(self) -> str:
        try:
            if not os.path.isfile(self._settings_path()):
                return "Default"
            with open(self._settings_path(), "r", encoding="utf-8") as f:
                return json.load(f).get("Current Preset", "Default")
        except Exception:
            return "Default"

    def _refresh_preset_dropdown(self) -> None:
        if not hasattr(self, "preset_combo"):
            return

        current = self.preset_combo.currentText()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        if os.path.exists(APPDATA_DIR):
            for entry in sorted(os.listdir(APPDATA_DIR)):
                preset_path = os.path.join(APPDATA_DIR, entry, "preset.json")
                if os.path.isfile(preset_path):
                    self.preset_combo.addItem(entry)

        if self.preset_combo.count() == 0:
            self.preset_combo.addItem("Default")

        target = current or PROFILE_NAME
        index = self.preset_combo.findText(target)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

        self.preset_combo.blockSignals(False)

    def _save_preset_file(self) -> None:
        name = self.preset_name.text().strip() or "Default"

        try:
            folder = self._preset_folder(name)
            os.makedirs(folder, exist_ok=True)

            path = self._preset_path(name)

            p = self._current_preset()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(p, f, indent=2)

            self._set_current_preset_name(name)
            self._refresh_preset_dropdown()
            self.preset_combo.setCurrentText(name)

            QMessageBox.information(self, "Preset saved", "Preset saved successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Preset save failed", str(e))

    def _load_preset_file(self) -> None:
        name = self.preset_combo.currentText().strip()
        if not name:
            return

        path = self._preset_path(name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._apply_preset_to_ui(data)
            self._set_current_preset_name(name)

        except Exception as e:
            QMessageBox.critical(self, "Preset load failed", str(e))
        self.setWindowTitle(f"Yet Another Music Player - {self._get_current_preset_name()} - {self._get_current_song_name()}")

    def _export_current_preset(self) -> None:
        try:
            preset_name = self._get_current_preset_name()
            path = self._preset_path(preset_name)

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._current_preset(), f, indent=2)

            QMessageBox.information(
                self,
                f"Default Preset: {preset_name}",
                "Preset saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Preset export failed", str(e))

    def _current_preset(self) -> Dict:
        songs = [data["path"] for data in self.songs.values() if "path" in data]
        return {
            "preset": asdict(self.engine.preset),
            "songs": songs,
            "theme": self.current_theme.copy(),
        }

    def get_song_list(self) -> List[str]:
        songs = []

        for data in self.songs.values():
            path = data.get("path")
            if path and os.path.isfile(path):
                songs.append(path)

        return songs

    def _get_current_song_name(self):
        artist, title, cover_path = self.engine.get_data()
        self.cover_path = cover_path
        pixmap = QPixmap(self.cover_path)
        self.label.setPixmap(pixmap)
        self._set_now_playing_info(artist, title)
        return f"{artist} - {title}"

    def _apply_preset_to_ui(self, data: Dict) -> None:
        self._loading_ui = True

        theme = data.get("theme", {})
        self.current_theme = DEFAULT_THEME.copy()
        self.current_theme.update(theme)
        apply_theme(QApplication.instance(), {"theme": self.current_theme})

        preset_dict = dict(data.get("preset", {}))
        p = Preset(**preset_dict)
        self.engine.preset = p

        loaded_songs = data.get("songs", [])

        self.songs = {}
        self.song_list.clear()

        for i, path in enumerate(loaded_songs):
            if not path or not os.path.isfile(path):
                continue

            self.songs[str(i)] = {"path": path}
            self.song_list.addItem(os.path.basename(path))

        if self.songs:
            self.current_song = max(0, min(p.current_song, len(self.songs) - 1))
        else:
            self.current_song = 0

        self.engine.preset.current_song = self.current_song

        self.mute_cb.setChecked(p.muted)
        self.shuffle_cb.setChecked(p.shuffle)
        self.repeat_cb.setChecked(p.repeat)
        self.volume_slider.setValue(int(p.volume))
        self._update_volume_label(int(p.volume))
        self._apply_ui_to_engine()

        if self.song_list.count() > 0:
            self.song_list.setCurrentRow(self.current_song)
            self.setWindowTitle(
                f"Yet Another Music Player - {self._get_current_preset_name()} - {self._get_current_song_name()}"
            )
        else:
            self._set_now_playing_info("Unknown Artist", "Nothing playing")
            self.label.setPixmap(QPixmap(BLANK_PATH))
            self.setWindowTitle(
                f"Yet Another Music Player - {self._get_current_preset_name()}"
            )

        self._loading_ui = False

    def _apply_ui_to_engine(self) -> None:
        if getattr(self, "_loading_ui", False):
            return
        p = self.engine.preset
        p.muted = self.mute_cb.isChecked()
        p.shuffle = self.shuffle_cb.isChecked()
        p.repeat = self.repeat_cb.isChecked()
        p.current_song = self.current_song
        p.volume = self.volume_slider.value()

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            os.makedirs(os.path.dirname(PRESET_PATH), exist_ok=True)
            with open(PRESET_PATH, "w", encoding="utf-8") as f:
                json.dump(self._current_preset(), f, indent=2)
        except Exception as e:
            print("Failed to save preset on exit:", e)
        #os.system("powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Why did you close me?')\"")
        super().closeEvent(event)



QSS_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "Inter","Segoe UI",system-ui;
    font-size: 13px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 0;
    background: transparent;
}}
QTabBar::tab {{
    background: {panel};
    color: {muted_text};
    border: 1px solid {border};
    border-bottom: 0;
    padding: 10px 14px;
    margin-right: 6px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}}
QTabBar::tab:hover {{
    color: {text};
}}
QTabBar::tab:selected {{
    background: {panel_active};
    color: {text};
    border-color: {border_selected};
}}

/* Grouping */
QGroupBox {{
    background-color: {panel};
    border: 1px solid {border};
    border-radius: 12px;
    margin-top: 18px;
    padding: 12px;
    padding-top: 18px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 0px;
    padding: 0 8px;
    color: {muted_text};
    font-weight: 600;
    background-color: {panel};
}}

/* Inputs */
QLineEdit, QComboBox, QListWidget {{
    background-color: {panel};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: {selection};
}}
QLineEdit:focus, QComboBox:focus, QListWidget:focus {{
    border: 1px solid {accent};
    outline: 0;
}}
QComboBox::drop-down {{
    border: 0;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {panel};
    border: 1px solid {border};
    outline: 0;
    selection-background-color: {selection};
    padding: 6px;
}}

QListWidget::item {{
    padding: 8px 10px;
    border-radius: 8px;
}}
QListWidget::item:hover {{
    background: {panel_active};
}}
QListWidget::item:selected {{
    background: {selection};
}}

/* Buttons */
QPushButton {{
    background-color: {panel_active};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 8px 12px;
}}
QPushButton:hover {{
    background-color: {button_hover};
    border-color: {border_hover};
}}
QPushButton:pressed {{
    background-color: {button_pressed};
}}
QPushButton:disabled {{
    color: {disabled_text};
    background-color: {panel};
    border-color: {border_disabled};
}}

/* Checkbox */
QCheckBox {{
    spacing: 10px;
    background-color: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid {border};
    background: {panel};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent};
}}
QCheckBox::indicator:checked:hover {{
    background: {accent_hover};
    border-color: {accent_hover};
}}

/* Slider */
QSlider::groove:horizontal {{
    height: 6px;
    background: {slider_bg};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 18px;
    margin: -7px 0;
    border-radius: 9px;
    background: {accent};
    border: 1px solid {accent};
}}
QSlider::handle:horizontal:hover {{
    background: {accent_hover};
    border-color: {accent_hover};
}}

/* Progress */
QProgressBar {{
    height: 10px;
    background: {slider_bg};
    border: 1px solid {border};
    border-radius: 6px;
}}
QProgressBar::chunk {{
    background: {accent};
    border-radius: 6px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {border_hover};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QLabel {{
    color: {text};
    background-color: transparent;
}}
"""

DEFAULT_THEME = {
    "bg": "#0f1115",
    "text": "#e6e9ef",
    "muted_text": "#9aa4b2",

    "panel": "#151823",
    "panel_active": "#1f2430",

    "border": "#2a2f3a",
    "border_hover": "#3a4152",
    "border_selected": "#3a4152",
    "border_disabled": "#1b1f27",

    "button_hover": "#242a37",
    "button_pressed": "#1a1f29",

    "accent": "#7c5cff",
    "accent_hover": "#8b73ff",

    "selection": "#2b3350",

    "slider_bg": "#1b2030",

    "disabled_text": "#677284",
}

def apply_theme(app: QApplication, settings: dict):
    app.setStyle("Fusion")
    app.setFont(QFont("Inter", 10))

    theme = DEFAULT_THEME.copy()
    if settings and "theme" in settings:
        theme.update(settings["theme"])

    qss = QSS_TEMPLATE.format(**theme)
    app.setStyleSheet(qss)
    for w in app.allWidgets():
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()

def set_theme_value(self, key: str, value: str):
    self.current_theme[key] = value
    apply_theme(QApplication.instance(), {"theme": self.current_theme})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Player()
    _load_auto_preset(w)
    w.show()
    sys.exit(app.exec())
