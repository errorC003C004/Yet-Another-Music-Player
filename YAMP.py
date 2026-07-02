#region Changelog
''' Every time I worked on it
    4-17-26 01:45 AM === Made Changelog, unknown
    4-19-26 04:26 PM === unknown
    4-17-26 11:23 PM === unknown
    4-20-26 08:22 PM === unknown
    4-21-26 09:33 PM === unknown
    4-22-26 10:47 PM === unknown
    4-23-26 07:53 PM === unknown
    4-26-26 07:44 PM === unknown
    5-03-26 08:31 PM === unknown
    5-05-26 06:10 PM === unknown
    5-06-26 06:19 PM === unknown
    5-09-26 12:42 PM === unknown
    5-10-26 09:30 PM === Added Translation Support
    5-11-26 09:18 PM === Added Console Support for EXE, miscellaneous fixes
    5-13-26 09:11 PM === Fixed Translation with EXE, Added Audio Normalization, small bug fixes
                        + Sliders and Translation Bug Fixes
    5-17-26 12:11 AM === small bug fixes,
                        + Added Queue button (auto queing coming soon), also made the loudness thingy no longer logger.info (its logger.debug)
    5-19-26 07:03 PM === Added Clickable Queue Buttons, simplified imports/startup ram usage
                        + Queue Saving, Windows Remember Position, settings tab
                        + Removed Preset Tab and added to settings
                        + Fixed Slider Backgrounds
    5-20-26 05:09 PM === Added Theme in Settings, Maybe fixed crashes
    5-21-26 08:53 PM === Crash Fix, Made Normalize Audio a Toggle
    
    1.1.1
    
    5-24-26 10:09 PM === bug fixes, started working on youtube imbedded support and it wont be added anytime soon
    5-25-26 03:33 PM === Added Musixmatch, LRCLIB, Lyrics.ohv, and Vocaloid Wiki Lyrics Support
    5-26-26 06:16 PM === bug fixes, Added Draggable Tabs, Emoji Logs fixed
                        + Queue Slots Draggable, Smooth Scrolling
    5-27-26 01:47 PM === Queue Slots had .ogg and werent the same name as library, lyrics show current song then load lyrics
    5-28-26 01:21 AM === VocaDB support
    5-31-26 09:34 PM === Spotify Font Added
    6-01-26 06:15 PM === All Font Sizes Can be Changed, Lyrics Fallback shown in Text
                        + This Section is Now Not Red in VsCode
    6-03-26 05:18 PM === Fixed Loading.. at Startup
    6-05-26 11:06 PM === Made Queue/Libary Show Artist Under The Title
                        + Optimized Slots
    6-08-26 10:17 PM === Organized Code, Made Online Lyrics in Thread, auto font download
    6-11-26 12:12 AM === Some Fixes with Slots, Added .mp3, .flac, .ogg, .oga, .opus, .wav, .m4a, .mp4, .aac, .wma, .aiff, .aif, .m3u, .m3u8
                        + Made everything in try except, Made Em dashes (—) in the title bar
    6-12-26 10:55 PM === Changed Logging (allows print()), organized a bit more
    6-13-26 08:42 PM === Made logging into a folder, auto scroll turns off on scroll (2.5 secs until on), Comment Cleanup
    7-01-26 10:37 PM === Put setup stuff in try except, Fixed Images for Queue/Library being shifted down
'''
 
''' Known Issues:
    * Translation Not Working on EXE
    * Images for Queue/Library are shifted down
    * Show Images Button Does Nothing
'''
 
''' Fixed Issues:
    * Images for Queue/Library are shifted down
''' 
 
''' Added Features:
    * Write Fetched Lyrics to file (or cache)
'''
 
''' Future Features:
    * If lyrics window is draggable, user can scroll with scroll wheel to skip lines or scroll down (only scroll if plain, if timed, skip to next line)
    * Option to also save song current position/time
    * Youtube Imbedded Support
    * Search Bar in Library
'''
#endregion

#region Imports
TRANSLATE_AVAILABLE = None
translate_import_error = None
from deep_translator import GoogleTranslator
import sys
import ctypes
from ctypes import wintypes
import os
from winrt.windows.foundation import Uri
from winrt.windows.media import MediaPlaybackType, MediaPlaybackStatus, SystemMediaTransportControlsButton
from winrt.windows.media.core import MediaSource
from winrt.windows.media.playback import MediaPlayer, MediaPlaybackState
from winrt.windows.storage import StorageFile
from winrt.windows.storage.streams import RandomAccessStreamReference
from mutagen import File as MutagenFile
from mutagen.flac import Picture
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QStyle, QColorDialog, QFrame, QSizePolicy, QInputDialog, QStyledItemDelegate, QTabWidget, QWidget, QPushButton, QScrollArea, QLabel, QListWidget, QListWidgetItem, QCheckBox, QSlider, QComboBox, QGroupBox, QMenu, QAbstractItemView, QApplication, QLineEdit, QMessageBox
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QRect, QThread, QSize, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QPixmap, QFont, QCloseEvent, QIcon, QFontDatabase
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
from typing import Dict, List
from shiboken6 import isValid
import json
import base64
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import random
from datetime import datetime, timedelta
import re
import hashlib
import logging
import threading
LIB_AND_PYLN_IMPORTED = False
#endregion

player_ver = "1.2"

#region Audio Stuff
audio_ext = {
    ".mp3",
    ".flac",
    ".ogg",
    ".oga",
    ".opus",
    ".wav",
    ".m4a",
    ".mp4",
    ".aac",
    ".wma",
    ".aiff",
    ".aif",
}

playlist_ext = {
    ".m3u",
    ".m3u8",
}

lib_ext = audio_ext | playlist_ext


def is_supported_audio_file(path: str) -> bool:
    try:
        return os.path.splitext(path)[1].lower() in audio_ext
    except Exception as e:
        logger.warning("is_supported_audio_file caused an unexpected bug: %s", e)
def is_supported_playlist_file(path: str) -> bool:
    try:
        return os.path.splitext(path)[1].lower() in playlist_ext
    except Exception as e:
        logger.warning("is_supported_playlist_file caused an unexpected bug: %s", e)
def is_supported_library_file(path: str) -> bool:
    try:
        ext = os.path.splitext(path)[1].lower()
        return ext in lib_ext
    except Exception as e:
        logger.warning("is_supported_library_file caused an unexpected bug: %s", e)
def read_m3u_playlist(path: str) -> list[str]:
    try:
        songs = []

        try:
            base_dir = os.path.dirname(path)

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if line.lower().startswith(("http://", "https://")):
                        continue

                    if not os.path.isabs(line):
                        line = os.path.abspath(os.path.join(base_dir, line))

                    if os.path.isfile(line) and is_supported_audio_file(line):
                        songs.append(line)

        except Exception as e:
            logger.warning("🟡 Failed to read playlist %s: %s", path, e)

        return songs
    except Exception as e:
        logger.warning("read_m3u_playlist caused an unexpected bug: %s", e)
def collect_supported_audio_paths(path: str) -> list[str]:
    try:
        found = []

        if not path:
            return found

        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for name in files:
                    child = os.path.join(root, name)

                    if is_supported_audio_file(child):
                        found.append(child)
                    elif is_supported_playlist_file(child):
                        found.extend(read_m3u_playlist(child))

            return found

        if not os.path.isfile(path):
            return found

        if is_supported_audio_file(path):
            found.append(path)
        elif is_supported_playlist_file(path):
            found.extend(read_m3u_playlist(path))

        return found
    except Exception as e:
        logger.warning("collect_supported_audio_paths caused an unexpected bug: %s", e)
#endregion

runningpy = not getattr(sys, "frozen", False)

#region Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
logger.handlers.clear()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
APPDATA_ROOT = os.getenv("APPDATA") or str(Path.home())
APPDATA_DIR = os.path.join(APPDATA_ROOT, "errorC003C004", "Music Player")
current_date = datetime.now().strftime("%Y-%m-%d")
LOG_DIR = os.path.join(APPDATA_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, f"YAMPv{player_ver}-{current_date}.log")
file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
class StreamToLogger:
    def __init__(self, original_stream, logger_func):
        self.original_stream = original_stream
        self.logger_func = logger_func
        self._buffer = ""

    def write(self, text):
        if not text:
            return

        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()

        self._buffer += text

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip()

            if line:
                self.logger_func(line)

    def flush(self):
        if self._buffer.strip():
            self.logger_func(self._buffer.strip())
            self._buffer = ""

        if self.original_stream:
            self.original_stream.flush()

    def isatty(self):
        return bool(getattr(self.original_stream, "isatty", lambda: False)())

    @property
    def encoding(self):
        return getattr(self.original_stream, "encoding", "utf-8")

kernel32 = ctypes.windll.kernel32
CTRL_CLOSE_EVENT = 2
_console_owner = None
ConsoleCtrlHandlerType = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    ctypes.c_uint
)
@ConsoleCtrlHandlerType
def _console_ctrl_handler(ctrl_type):
    try:
        global _console_owner

        if ctrl_type == CTRL_CLOSE_EVENT:
            if _console_owner is not None:
                console_close_bridge.closed.emit()
            return True

        return False
    except Exception as e:
        logger.warning("_console_ctrl_handler caused an unexpected bug: %s", e)
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
handle = kernel32.GetStdHandle(-11)
mode = ctypes.c_uint()
if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
    kernel32.SetConsoleMode(
        handle,
        mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    )
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
class ConsoleCloseBridge(QObject):
    closed = Signal()
console_close_bridge = ConsoleCloseBridge()
class COORD(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_short),
        ("Y", ctypes.c_short),
    ]

class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("nFont", ctypes.c_ulong),
        ("dwFontSize", COORD),
        ("FontFamily", ctypes.c_uint),
        ("FontWeight", ctypes.c_uint),
        ("FaceName", wintypes.WCHAR * 32),
    ]

#endregion

#region Paths Setup
FONT_DIR = Path(APPDATA_DIR) / "fonts"
SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.json")
BLANK_PATH = os.path.join(APPDATA_DIR, "blank.png")
ICON_PATH = os.path.join(APPDATA_DIR, "icon.png")
if not os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump({"Current Preset": "Default"}, f, indent=2)

    PROFILE_NAME = "Default"
else:

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    PROFILE_NAME = data.get("Current Preset", "Default")
PROFILE_DIR = os.path.join(APPDATA_DIR, PROFILE_NAME)
TEMP_DIR = os.path.join(PROFILE_DIR, "Temp")
PRESET_PATH = os.path.join(PROFILE_DIR, "preset.json")
cover_path = BLANK_PATH
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(APPDATA_DIR, exist_ok=True)

#fonts
try:
    FONT_NAMES = [
        "SpotifyMixUI-Bold.ttf",
        "SpotifyMixUI-Regular.ttf",
        "SpotifyMixUITitle-Bold.ttf",
        "SpotifyMixUITitle-Extrabold.ttf",
        "SpotifyMixUITitleVariable.ttf",
    ]

    def _download_missing_assets() -> None:
        ''' Downloads the blank/icon images and fonts if they're missing.
            This does blocking network calls (up to several seconds each), so it must
            NEVER be run at import time or on the UI thread — it's kicked off on a
            background thread after the window is already shown (see __main__). '''
        try:
            if not os.path.exists(BLANK_PATH):
                try:
                    with urlopen("https://github.com/errorC003C004/Yet-Another-Music-Player/blob/main/files_to_build/no_image.png?raw=true", timeout=10) as r:
                        with open(BLANK_PATH, "wb") as f:
                            f.write(r.read())
                except Exception as e:
                    logger.warning("🟡 Cant Download Blank Image: %s", e)
            if not os.path.exists(ICON_PATH):
                try:
                    with urlopen("https://github.com/errorC003C004/Yet-Another-Music-Player/blob/main/files_to_build/icon.png?raw=true", timeout=10) as r:
                        with open(ICON_PATH, "wb") as f:
                            f.write(r.read())
                except Exception as e:
                    logger.warning("🟡 Cant Download Icon Image: %s", e)
            #fonts
            try:
                os.makedirs(FONT_DIR, exist_ok=True)
                missing_fonts = [
                    name for name in FONT_NAMES
                    if not os.path.exists(os.path.join(FONT_DIR, name))
                ]

                if missing_fonts:
                    logger.warning("🟡 Missing fonts: %s", missing_fonts)
                    for name in os.listdir(FONT_DIR):
                        path = os.path.join(FONT_DIR, name)

                        try:
                            if os.path.isfile(path):
                                os.remove(path)
                        except Exception as e:
                            logger.warning("🟡 Cant Remove Font File: %s", e)
                    for name in FONT_NAMES:
                        url = (
                            "https://github.com/errorC003C004/Yet-Another-Music-Player"
                            f"/blob/main/files_to_build/fonts/{quote(name)}?raw=true"
                        )

                        path = os.path.join(FONT_DIR, name)

                        try:
                            logger.debug("Downloading font: %s", name)

                            with urlopen(url, timeout=10) as r:
                                with open(path, "wb") as out:
                                    out.write(r.read())

                        except Exception as e:
                            logger.warning("🟡 Cant Download Font %s: %s", name, e)
            except Exception as e:
                logger.warning("🟡 Cant Download Fonts: %s", e)
        except Exception as e:
            logger.warning("_download_missing_assets caused an unexpected bug: %s", e)

    class _AssetsReadyBridge(QObject):
        ''' Lets the background asset-download thread notify the UI thread when it's
            done, so Qt signal/slot handles the cross-thread marshaling safely. '''
        ready = Signal()

    assets_ready_bridge = _AssetsReadyBridge()

    def _download_missing_assets_then_notify() -> None:
        try:
            _download_missing_assets()
        finally:
            assets_ready_bridge.ready.emit()
except Exception as e:
    logger.warning("🟡 Cant Download Fonts: %s", e)
#endregion

#region Preset
def create_auto_preset():
    try:
        os.makedirs(PROFILE_DIR, exist_ok=True)

        if not os.path.exists(PRESET_PATH):
            with open(PRESET_PATH, "w", encoding="utf-8") as f:
                json.dump({"preset": {}, "songs": [], "theme": {}}, f, indent=2)
    except Exception as e:
        logger.warning("create_auto_preset caused an unexpected bug: %s", e)

def _load_auto_preset(w) -> None:
    try:
        w._loading_preset = True
        try:
            if not os.path.exists(PRESET_PATH):
                create_auto_preset()
                return

            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            w._apply_preset_to_ui(data)
        except Exception as e:
            logger.warning("🟡 Auto-load failed: %s", e)
        finally:
            w._loading_preset = False
    except Exception as e:
        logger.warning("_load_auto_preset caused an unexpected bug: %s", e)
#endregion


#region Helpers/Smthn
def smooth_wheel_scroll(widget, event, duration=180):
    try:
        sb = widget.verticalScrollBar()

        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()

        if pixel_delta:
            amount = pixel_delta
        elif angle_delta:
            steps = angle_delta / 120
            amount = steps * QApplication.wheelScrollLines() * sb.singleStep()
        else:
            return

        target = sb.value() - int(amount)
        target = max(sb.minimum(), min(sb.maximum(), target))

        anim = QPropertyAnimation(sb, b"value", widget)
        anim.setDuration(duration)
        anim.setStartValue(sb.value())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        widget._smooth_scroll_anim = anim
        anim.start()

        event.accept()
    except Exception as e:
        logger.warning("smooth_wheel_scroll caused an unexpected bug: %s", e)
#endregion

#region Widgets
class LyricsPopupWindow(QWidget):
    geometryChanged = Signal()
    closedByUser = Signal()

    def __init__(self, title="Lyrics", minimum_size=(420, 120), show_all=False):
        try:
            super().__init__()

            self.show_all = show_all

            self.setWindowTitle(title)
            self.setMinimumSize(*minimum_size)
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setMouseTracking(True)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

            self._drag_ready = False
            self._dragging = False
            self._drag_offset = QPoint()
            self._last_lyrics_count = -1

            self._hover_timer = QTimer(self)
            self._hover_timer.setSingleShot(True)
            self._hover_timer.setInterval(1000)
            self._hover_timer.timeout.connect(self._enable_drag_ready)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 14, 14, 14)

            self.box = QWidget()
            self.box.setObjectName("FloatingLyricsBox")
            self.box.setMouseTracking(True)
            self.box.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

            box_layout = QVBoxLayout(self.box)
            box_layout.setContentsMargins(16, 12, 16, 12)

            if self.show_all:
                self.lyrics_list = QListWidget()
                self.lyrics_list.setFrameShape(QFrame.Shape.NoFrame)
                self.lyrics_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
                self.lyrics_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.lyrics_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.lyrics_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
                self.lyrics_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                self.lyrics_list.setMouseTracking(True)
                self.lyrics_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self.lyrics_list.setStyleSheet("""
                    QListWidget {
                        background: transparent;
                        border: none;
                        outline: none;
                    }
                    QListWidget::item {
                        background: transparent;
                        border: none;
                        padding: 5px;
                    }
                """)
                box_layout.addWidget(self.lyrics_list)
                self.label = None
            else:
                self.label = QLabel("")
                self.label.setObjectName("FloatingLyricsText")
                self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.label.setWordWrap(True)
                self.label.setMouseTracking(True)
                self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

                box_layout.addWidget(self.label)
                self.lyrics_list = None

            layout.addWidget(self.box)

            self._set_idle_style()
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def set_text(self, text: str):
        try:
            if self.label is None:
                return

            self.label.setTextFormat(Qt.TextFormat.PlainText)

            if self.contains_japanese(text):
                self.label.setStyleSheet("""
                    font-family: 'Spotify Mix UI', 'Noto Sans JP';
                    color: white;
                    font-size: 22px;
                    font-weight: 700;
                """)
            else:
                self.label.setStyleSheet("""
                    font-family: 'Spotify Mix UI', 'Segoe UI Variable';
                    color: white;
                    font-size: 22px;
                    font-weight: 700;
                """)

            self.label.setText(text or "")
        except Exception as e:
            logger.warning("set_text caused an unexpected bug: %s", e)

    def set_lyrics(self, lyrics_data: list, current_index: int = -1, highlight: bool = True):
        try:
            if not self.show_all:
                if lyrics_data and current_index < 0:
                    current_index = 0

                if 0 <= current_index < len(lyrics_data):
                    text = lyrics_data[current_index].get("text", "")
                    self.set_text(str(text))
                else:
                    self.set_text("")
                return

            if self.lyrics_list is None:
                return

            total = len(lyrics_data)

            if total == 0:
                self.lyrics_list.clear()
                self._last_lyrics_count = 0
                return

            current_index = max(0, min(total - 1, current_index))

            if self.lyrics_list.count() != total:
                self.lyrics_list.clear()

                for line in lyrics_data:
                    text = str(line.get("text", ""))
                    if not text.strip():
                        text = "♫"

                    item = QListWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.lyrics_list.addItem(item)

                self._last_lyrics_count = total

            for i in range(self.lyrics_list.count()):
                item = self.lyrics_list.item(i)
                if item is None:
                    continue

                active = highlight and i == current_index

                text = item.text()
                font = item.font()
                font.setFamily(
                    self.theme_font_raw("lyrics_jp_font", "Noto Sans JP")
                    if self.contains_japanese(text)
                    else self.theme_font_raw("lyrics_en_font", "Segoe UI Variable")
                )
                font.setBold(active)
                font.setPointSize(18 if active else 13)
                item.setFont(font)

                item.setForeground(Qt.GlobalColor.white if active else Qt.GlobalColor.gray)
                item.setBackground(Qt.GlobalColor.transparent)

            item = self.lyrics_list.item(current_index)
            if item is not None:
                self.smooth_scroll_to_item(item)
        except Exception as e:
            logger.warning("set_lyrics caused an unexpected bug: %s", e)

    def smooth_scroll_to_item(self, item, duration=260):
        try:
            if not self.show_all or self.lyrics_list is None or item is None:
                return

            sb = self.lyrics_list.verticalScrollBar()
            rect = self.lyrics_list.visualItemRect(item)

            target = sb.value() + rect.top()
            target -= self.lyrics_list.viewport().height() // 2
            target += rect.height() // 2

            target = max(sb.minimum(), min(sb.maximum(), target))

            if target == sb.value():
                return

            anim = QPropertyAnimation(sb, b"value", self.lyrics_list)
            anim.setDuration(duration)
            anim.setStartValue(sb.value())
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            self.lyrics_list._smooth_scroll_anim = anim
            anim.start()
        except Exception as e:
            logger.warning("smooth_scroll_to_item caused an unexpected bug: %s", e)

    def theme_font(self, name: str, default: str) -> str:
        try:
            return f"'{self.theme_font_raw(name, default)}'"
        except Exception as e:
            logger.warning("theme_font caused an unexpected bug: %s", e)

    def theme_font_raw(self, name: str, default: str) -> str:
        try:
            try:
                with open(PRESET_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)

                theme = data.get("theme", {})
                return theme.get(name, default)
            except Exception:
                return default
        except Exception as e:
            logger.warning("theme_font_raw caused an unexpected bug: %s", e)

    def _apply_style(self, alpha):
        try:
            self.box.setStyleSheet(f"""
                QWidget#FloatingLyricsBox {{
                    background-color: rgba(31, 36, 48, {alpha});
                    border-radius: 12px;
                }}
                QLabel#FloatingLyricsText {{
                    background-color: transparent;
                    color: white;
                    font-size: 22px;
                    font-weight: 700;
                }}
            """)
        except Exception as e:
            logger.warning("_apply_style caused an unexpected bug: %s", e)

    def _set_idle_style(self):
        try:
            self._drag_ready = False
            self._apply_style(0)
        except Exception as e:
            logger.warning("_set_idle_style caused an unexpected bug: %s", e)

    def _set_hover_style(self):
        try:
            self._apply_style(120)
        except Exception as e:
            logger.warning("_set_hover_style caused an unexpected bug: %s", e)

    def _enable_drag_ready(self):
        try:
            self._drag_ready = True
            self._apply_style(210)
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        except Exception as e:
            logger.warning("_enable_drag_ready caused an unexpected bug: %s", e)

    def _mouse_over_label(self, global_pos) -> bool:
        try:
            if self.label is not None:
                label_pos = self.label.mapFromGlobal(global_pos)
                return self.label.rect().contains(label_pos)

            if self.lyrics_list is not None:
                list_pos = self.lyrics_list.mapFromGlobal(global_pos)
                return self.lyrics_list.rect().contains(list_pos)

            return False
        except Exception as e:
            logger.warning("_mouse_over_label caused an unexpected bug: %s", e)

    def enterEvent(self, event):
        try:
            global_pos = self.cursor().pos()

            if not self._mouse_over_label(global_pos):
                super().enterEvent(event)
                return

            self._set_hover_style()
            self._hover_timer.start()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            super().enterEvent(event)
        except Exception as e:
            logger.warning("enterEvent caused an unexpected bug: %s", e)

    def leaveEvent(self, event):
        try:
            if self._dragging:
                super().leaveEvent(event)
                return

            self._hover_timer.stop()
            self.unsetCursor()
            self._set_idle_style()
            super().leaveEvent(event)
        except Exception as e:
            logger.warning("leaveEvent caused an unexpected bug: %s", e)

    def mousePressEvent(self, event):
        try:
            if self._drag_ready and event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return

            super().mousePressEvent(event)
        except Exception as e:
            logger.warning("mousePressEvent caused an unexpected bug: %s", e)

    def mouseMoveEvent(self, event):
        try:
            if self._dragging:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                event.accept()
                return

            if self._mouse_over_label(event.globalPosition().toPoint()):
                if not self._hover_timer.isActive() and not self._drag_ready:
                    self._set_hover_style()
                    self._hover_timer.start()
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                if not self._dragging:
                    self._hover_timer.stop()
                    self.unsetCursor()
                    self._set_idle_style()

            super().mouseMoveEvent(event)
        except Exception as e:
            logger.warning("mouseMoveEvent caused an unexpected bug: %s", e)

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self._dragging = False

            super().mouseReleaseEvent(event)
        except Exception as e:
            logger.warning("mouseReleaseEvent caused an unexpected bug: %s", e)

    def wheelEvent(self, event):
        try:
            if not self._drag_ready:
                return

            if not hasattr(self, "_scroll_callback") or self._scroll_callback is None:
                return

            delta = event.angleDelta().y()

            if delta == 0:
                return

            direction = 1 if delta < 0 else -1
            self._scroll_callback(direction)
            event.accept()
        except Exception as e:
            logger.warning("wheelEvent caused an unexpected bug: %s", e)

    def set_scroll_callback(self, callback):
        try:
            self._scroll_callback = callback
        except Exception as e:
            logger.warning("set_scroll_callback caused an unexpected bug: %s", e)

    def contains_japanese(self, text: str) -> bool:
        try:
            for ch in text:
                code = ord(ch)

                if (
                    0x3040 <= code <= 0x309F or
                    0x30A0 <= code <= 0x30FF or
                    0x4E00 <= code <= 0x9FFF
                ):
                    return True

            return False
        except Exception as e:
            logger.warning("contains_japanese caused an unexpected bug: %s", e)

    def reset_clickthrough_state(self):
        try:
            self._hover_timer.stop()
            self._drag_ready = False
            self.unsetCursor()
            self._set_idle_style()
        except Exception as e:
            logger.warning("reset_clickthrough_state caused an unexpected bug: %s", e)

    def moveEvent(self, event):
        try:
            self.geometryChanged.emit()
            super().moveEvent(event)
        except Exception as e:
            logger.warning("moveEvent caused an unexpected bug: %s", e)

    def resizeEvent(self, event):
        try:
            self.geometryChanged.emit()
            super().resizeEvent(event)
        except Exception as e:
            logger.warning("resizeEvent caused an unexpected bug: %s", e)

    def closeEvent(self, event):
        try:
            self.geometryChanged.emit()

            if getattr(self, "_force_close", False):
                event.accept()
                return

            self.hide()
            self.closedByUser.emit()
            event.ignore()
        except Exception as e:
            logger.warning("closeEvent caused an unexpected bug: %s", e)

class LyricStuff(QObject):
    def __init__(self, engine) -> None:
        try:
            super().__init__()
            self.engine = engine
            self.window = None
            self.floating_window = None
            self.translation_cache = {}
            self._status_callback = None
            self.LyricsFetcher = LyricsFetcher(self)
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def set_status_callback(self, callback):
        try:
            self._status_callback = callback
        except Exception as e:
            logger.warning("set_status_callback caused an unexpected bug: %s", e)

    def clear_status_callback(self, callback=None):
        try:
            if callback is None or self._status_callback == callback:
                self._status_callback = None
        except Exception as e:
            logger.warning("clear_status_callback caused an unexpected bug: %s", e)

    def emit_status(self, message: str):
        try:
            callback = getattr(self, "_status_callback", None)
            if callback is None:
                return
            try:
                callback(str(message))
            except RuntimeError:
                self._status_callback = None
        except Exception as e:
            logger.warning("emit_status caused an unexpected bug: %s", e)

    def show_window(self):
        try:
            if self.window is None:
                self.window = LyricsPopupWindow(
                    title="Lyrics",
                    minimum_size=(520, 520),
                    show_all=True
                )

                self._restore_geometry(
                    self.window,
                    self.engine.preset.lyrics_window_geometry
                )

                self.window.geometryChanged.connect(self._save_window_geometry)
                self.window.closedByUser.connect(self._lyrics_window_closed_by_user)

            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
        except Exception as e:
            logger.warning("show_window caused an unexpected bug: %s", e)

    def show_floating_window(self):
        try:
            if self.floating_window is None:
                self.floating_window = LyricsPopupWindow(
                    title="Floating Lyrics",
                    minimum_size=(420, 120),
                    show_all=False
                )

                self._restore_geometry(
                    self.floating_window,
                    self.engine.preset.floating_window_geometry
                )

                self.floating_window.geometryChanged.connect(self._save_window_geometry)
                self.floating_window.closedByUser.connect(self._floating_window_closed_by_user)

            self.floating_window.set_scroll_callback(self._handle_scroll)
            self.floating_window.show()
            self.floating_window.raise_()
        except Exception as e:
            logger.warning("show_floating_window caused an unexpected bug: %s", e)

    def hide_window(self):
        try:
            if self.window is not None:
                self._save_window_geometry()
                self.window.hide()
        except Exception as e:
            logger.warning("hide_window caused an unexpected bug: %s", e)

    def hide_floating_window(self):
        try:
            if self.floating_window is not None:
                self._save_window_geometry()
                self.floating_window.hide()
        except Exception as e:
            logger.warning("hide_floating_window caused an unexpected bug: %s", e)

    def _lyrics_window_closed_by_user(self):
        try:
            self.engine.preset.lyrics_window = False

            self.engine.player._set_checkbox_silent(self.engine.player.lyrics_window_cb,
                False
            )

            self.engine.player._autosave_current_preset()
        except Exception as e:
            logger.warning("_lyrics_window_closed_by_user caused an unexpected bug: %s", e)

    def _floating_window_closed_by_user(self):
        try:
            self.engine.preset.floating_lyrics = False

            self.engine.player._set_checkbox_silent(self.engine.player.floating_lyrics_cb,
                False
            )

            self.engine.player._autosave_current_preset()
        except Exception as e:
            logger.warning("_floating_window_closed_by_user caused an unexpected bug: %s", e)

    def update_window(self, lyrics_data: list, current_index: int = -1, highlight: bool = True):
        try:
            if self.window is None:
                return

            self.window.set_lyrics(lyrics_data, current_index, highlight)
        except Exception as e:
            logger.warning("update_window caused an unexpected bug: %s", e)

    def update_floating_window(self, lyrics_data: list, current_index: int = -1, reset_hover: bool = False):
        try:
            if self.floating_window is None:
                return

            if lyrics_data and current_index < 0:
                current_index = 0

            self.floating_window.set_lyrics(lyrics_data, current_index)

            if reset_hover:
                self.floating_window.reset_clickthrough_state()
        except Exception as e:
            logger.warning("update_floating_window caused an unexpected bug: %s", e)

    def romanize_lrc_lines(self, text: str) -> str:
        try:
            from pykakasi import kakasi
            ts_line_re = re.compile(r'^(\s*(?:\[\d{1,2}:\d{2}(?:\.\d{1,3})?\])+)(.*)$')

            def is_mostly_ascii(s: str) -> bool:
                try:
                    s = re.sub(r'\s+', '', s)

                    if not s:
                        return True

                    return sum(1 for c in s if ord(c) < 128) / len(s) > 0.9
                except Exception as e:
                    logger.warning("is_mostly_ascii caused an unexpected bug: %s", e)

            kks = kakasi()

            def romanize_jp(line: str) -> str | None:
                try:
                    t = line.strip()

                    if not t or is_mostly_ascii(t):
                        return None

                    result = kks.convert(t)

                    romaji = " ".join(part["hepburn"] for part in result).strip()
                    romaji = re.sub(r"\s+", " ", romaji)

                    if not romaji or romaji.lower() == t.lower():
                        return None

                    return romaji
                except Exception as e:
                    logger.warning("romanize_jp caused an unexpected bug: %s", e)

            output = []

            for line in text.splitlines():
                match = ts_line_re.match(line)

                if match:
                    tags, lyric = match.group(1), match.group(2)
                    romaji = romanize_jp(lyric)

                    if romaji:
                        output.append(f"{tags}{romaji}")
                    else:
                        output.append(line)
                else:
                    romaji = romanize_jp(line)
                    output.append(romaji if romaji else line)

            return "\n".join(output)
        except Exception as e:
            logger.warning("romanize_lrc_lines caused an unexpected bug: %s", e)

    def translate_lrc_lines(self, text: str, target: str = "en") -> str:
        try:
            self.emit_status("Translating...")
            cache_key = (target, text)

            cached = self.translation_cache.get(cache_key)
            if cached is not None:
                return cached

            ts_line_re = re.compile(
                r'^(\s*(?:\[\d{1,2}:\d{2}(?:\.\d{1,3})?\])+)(.*)$'
            )

            def is_mostly_ascii(s: str) -> bool:
                try:
                    s = re.sub(r'\s+', '', s)
                    if not s:
                        return True
                    return sum(1 for c in s if ord(c) < 128) / len(s) > 0.9
                except Exception as e:
                    logger.warning("is_mostly_ascii caused an unexpected bug: %s", e)

            def detect_lang_guess(s: str) -> str | None:
                # Japanese
                try:
                    if re.search(r'[\u3040-\u30ff]', s):
                        return "ja"

                    # Korean
                    if re.search(r'[\uac00-\ud7af]', s):
                        return "ko"

                    # Chinese or Japanese kanji-only.
                    if re.search(r'[\u4e00-\u9fff]', s):
                        return "ja"

                    return None
                except Exception as e:
                    logger.warning("detect_lang_guess caused an unexpected bug: %s", e)

            def translate_line(line: str) -> str | None:
                try:
                    raw = line.strip()

                    if not raw or is_mostly_ascii(raw):
                        return None

                    source = detect_lang_guess(raw)
                    if not source or source == target:
                        return None

                    try:
                        translator = GoogleTranslator(
                            source=source,
                            target=target
                        )

                        translated = translator.translate(raw)

                    except Exception as e:
                        logger.warning("🟡 Translation failed: %s", e)
                        return None

                    translated = translated.strip()

                    if not translated or translated == raw:
                        return None

                    return translated
                except Exception as e:
                    logger.warning("translate_line caused an unexpected bug: %s", e)

            output = []

            for line in text.splitlines():
                match = ts_line_re.match(line)

                if match:
                    tags, lyric = match.group(1), match.group(2)
                    translated = translate_line(lyric)

                    if translated:
                        output.append(f"{tags}{translated}")
                    else:
                        output.append(line)
                else:
                    translated = translate_line(line)
                    output.append(translated if translated else line)

            result = "\n".join(output)
            self.translation_cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning("translate_lrc_lines caused an unexpected bug: %s", e)

    def get_lyrics(self):
        try:
            artist, title, cover_path = self.engine.get_data()
            current_song = self.engine.get_current_song()

            if not current_song:
                logger.info("No current song")
                return None

            song_path_folder = os.path.dirname(current_song)
            lyric_path = os.path.join(song_path_folder, f"{artist} - {title}.lrc")

            if os.path.exists(lyric_path):
                return lyric_path
    
            if os.path.exists(current_song):
                lyric_path = os.path.splitext(current_song)[0] + ".lrc"
                if os.path.exists(lyric_path):
                    return lyric_path
                pass

            return None
        except Exception as e:
            logger.warning("get_lyrics caused an unexpected bug: %s", e)

    def convert_lyrics(self):
        try:
            artist, title, cover_path = self.engine.get_data()
            lyric_path = self.get_lyrics()

            if not lyric_path:
                try:
                    if self.engine.preset.online_lyrics:
                        logger.debug("Using LyricsFetcher for %s - %s", artist, title)
                        lyrics = self.LyricsFetcher.fetch(artist, title)
                        if lyrics:
                            if self.engine.preset.download_lyrics:
                                logger.info("🔵 Downloading lyrics for %s - %s", artist, title)
                                download_path = self.engine.get_current_song()
                                download_path = os.path.dirname(download_path)
                                lyric_path = os.path.join(download_path, f"{artist} - {title}.lrc")
                                with open(lyric_path, "w", encoding="utf-8") as f:
                                    f.write(lyrics)
                        else:
                            return {
                                "timed": False,
                                "lyrics": [{"time": None, "text": f"{artist} - {title}"}]
                            }
                    else:
                        return {
                            "timed": False,
                            "lyrics": [{"time": None, "text": f"{artist} - {title}"}]
                        }
                except Exception as e:
                    logger.warning("🟡 Failed to get lyrics: %s", e)
                    return {
                        "timed": False,
                        "lyrics": [{"time": None, "text": f"{artist} - {title}"}]
                    }

            if lyric_path:
                with open(lyric_path, "r", encoding="utf-8") as f:
                    lyrics = f.read()

            time_pattern = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")
            timed = bool(time_pattern.search(lyrics))

            if self.engine.preset.translated:
                lyrics = self.translate_lrc_lines(lyrics)

            if self.engine.preset.romaji:
                lyrics = self.romanize_lrc_lines(lyrics)

            converted = []

            for raw_line in lyrics.splitlines():
                line = raw_line.strip()
                if not line:
                    converted.append({"time": None, "text": " "})
                    continue

                matches = list(time_pattern.finditer(line))

                if matches:
                    text = time_pattern.sub("", line).strip()
                    if not text:
                        text = "♫"

                    for match in matches:
                        minutes = int(match.group(1))
                        seconds = int(match.group(2))
                        frac = (match.group(3) or "0").ljust(3, "0")
                        total_seconds = minutes * 60 + seconds + int(frac) / 1000
                        converted.append({"time": total_seconds, "text": text})
                else:
                    if re.match(r"^\[[a-zA-Z]+\s*:\s*.*\]$", line):
                        continue
                    converted.append({"time": None, "text": line})

            if timed:
                timed_lines = [line for line in converted if line.get("time") is not None]

                if timed_lines:
                    first_time = min(line["time"] for line in timed_lines)

                    if first_time > 1.25:
                        converted.append({"time": 0.0, "text": "♫"})

            converted.sort(key=lambda x: float("inf") if x["time"] is None else x["time"])

            return {
                "timed": timed,
                "lyrics": converted
            }
        except Exception as e:
            logger.warning("convert_lyrics caused an unexpected bug: %s", e)

    def current_lyric_index(self, current_seconds: float, lyrics_data: list) -> int:
        try:
            current_index = -1

            for i, line in enumerate(lyrics_data):
                t = line.get("time")
                if t is not None and current_seconds >= (t - 0.1):
                    current_index = i
                elif t is not None and current_seconds < t:
                    break

            return current_index
        except Exception as e:
            logger.warning("current_lyric_index caused an unexpected bug: %s", e)

    def set_lyrics(self, enabled: bool):
        try:
            self.engine.preset.lyrics_window = bool(enabled)

            if enabled:
                self.show_window()

                player = self.engine.player
                if hasattr(player, "current_lyrics_data"):
                    self.update_window(
                        player.current_lyrics_data,
                        player.current_lyrics_index,
                        player.current_lyrics_timed
                    )
            else:
                self.hide_window()
        except Exception as e:
            logger.warning("set_lyrics caused an unexpected bug: %s", e)

    def set_lyrics_on_top(self, enabled: bool):
        try:
            self.engine.preset.lyrics_window_on_top = bool(enabled)

            if self.window is None:
                if not self.engine.preset.lyrics_window:
                    return
                self.show_window()

            self.window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(enabled))

            if self.engine.preset.lyrics_window:
                self.window.show()
                if enabled:
                    self.window.raise_()
                    self.window.activateWindow()
        except Exception as e:
            logger.warning("set_lyrics_on_top caused an unexpected bug: %s", e)

    def set_floating(self, enabled: bool):
        try:
            self.engine.preset.floating_lyrics = bool(enabled)

            if enabled:
                self.show_floating_window()

                player = self.engine.player
                if hasattr(player, "current_lyrics_data"):
                    self.update_floating_window(
                        player.current_lyrics_data,
                        player.current_lyrics_index
                    )
            else:
                self.hide_floating_window()
        except Exception as e:
            logger.warning("set_floating caused an unexpected bug: %s", e)

    def set_floating_on_top(self, enabled: bool):
        try:
            self.engine.preset.floating_lyrics_on_top = bool(enabled)

            if self.floating_window is None:
                if not self.engine.preset.floating_lyrics:
                    return
                self.show_floating_window()

            self.floating_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(enabled))

            if self.engine.preset.floating_lyrics:
                self.floating_window.show()
                if enabled:
                    self.floating_window.raise_()
                    self.floating_window.activateWindow()
        except Exception as e:
            logger.warning("set_floating_on_top caused an unexpected bug: %s", e)

    def _handle_scroll(self, direction: int):
        try:
            if not hasattr(self.engine.player, "current_lyrics_data"):
                return

            player = self.engine.player
            data = player.current_lyrics_data

            if not data:
                return

            if player.current_lyrics_timed:
                current_index = player.current_lyrics_index

                if current_index < 0:
                    current_index = 0

                new_index = max(0, min(len(data) - 1, current_index + direction))

                time = data[new_index].get("time")
                if time is not None:
                    self.engine.set_time(float(time))

            else:
                current_index = player.current_lyrics_index

                if current_index < 0:
                    current_index = 0

                new_index = max(0, min(len(data) - 1, current_index + direction))

                player._highlight_current_lyric(new_index, force=True)
        except Exception as e:
            logger.warning("_handle_scroll caused an unexpected bug: %s", e)

    def _geometry_to_dict(self, window):
        try:
            if window is None:
                return None

            g = window.geometry()
            return {
                "x": g.x(),
                "y": g.y(),
                "w": g.width(),
                "h": g.height()
            }
        except Exception as e:
            logger.warning("_geometry_to_dict caused an unexpected bug: %s", e)

    def _restore_geometry(self, window, geometry):
        try:
            if window is None or not isinstance(geometry, dict):
                return

            try:
                x = int(geometry.get("x", window.x()))
                y = int(geometry.get("y", window.y()))
                w = int(geometry.get("w", window.width()))
                h = int(geometry.get("h", window.height()))

                window.setGeometry(QRect(x, y, w, h))
            except Exception as e:
                logger.warning("🟡 Window geometry restore failed: %s", e)
        except Exception as e:
            logger.warning("_restore_geometry caused an unexpected bug: %s", e)

    def _save_window_geometry(self):
        try:
            preset = self.engine.preset

            preset.lyrics_window_geometry = self._geometry_to_dict(self.window)
            preset.floating_window_geometry = self._geometry_to_dict(self.floating_window)

            self.engine.player._autosave_current_preset()
        except Exception as e:
            logger.warning("_save_window_geometry caused an unexpected bug: %s", e)

class LibraryListWidget(QListWidget):
    deletePressed = Signal()
    selectAllPressed = Signal()

    def __init__(self):
        try:
            super().__init__()
            self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def wheelEvent(self, event):
        try:
            smooth_wheel_scroll(self, event)
        except Exception as e:
            logger.warning("wheelEvent caused an unexpected bug: %s", e)

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_Delete:
                self.deletePressed.emit()
                return

            if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
                self.selectAll()
                self.selectAllPressed.emit()
                return

            super().keyPressEvent(event)
        except Exception as e:
            logger.warning("keyPressEvent caused an unexpected bug: %s", e)

class JumpSlider(QSlider):
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                value = QStyle.sliderValueFromPosition(
                    self.minimum(),
                    self.maximum(),
                    int(event.position().x()),
                    self.width()
                )

                self.setValue(value)
                self.sliderPressed.emit()
                self.sliderMoved.emit(value)

            super().mousePressEvent(event)
        except Exception as e:
            logger.warning("mousePressEvent caused an unexpected bug: %s", e)

class SongRowWidget(QWidget):
    def __init__(self, title_text: str, artist_text: str, pixmap: QPixmap | None = None, show_handle=False, row_height=60):
            try:
                super().__init__()
                self.setFixedHeight(row_height)

                layout = QHBoxLayout(self)
                layout.setContentsMargins(8, 4, 8, 4)
                layout.setSpacing(8)
                layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

                cover = QLabel()
                cover.setFixedSize(52, 52)
                cover.setScaledContents(False)
                cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cover.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                if pixmap and not pixmap.isNull():
                    cover.setPixmap(pixmap)

                cover_wrap = QVBoxLayout()
                cover_wrap.setContentsMargins(0, 0, 0, 0)
                cover_wrap.setSpacing(0)
                cover_wrap.addStretch(1)
                cover_wrap.addWidget(cover)
                cover_wrap.addStretch(1)
                layout.addLayout(cover_wrap)

                self.setObjectName("SongRowWidget")
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

                self.setStyleSheet("""
                QWidget#SongRowWidget {
                    background: transparent;
                }
                QWidget#SongRowWidget QWidget {
                    background: transparent;
                }
                QWidget#SongRowWidget QLabel {
                    background: transparent;
                }
                """)

                text_box = QWidget()
                text_layout = QVBoxLayout(text_box)
                text_layout.setContentsMargins(0, 0, 0, 0)
                text_layout.setSpacing(1)

                title = QLabel(title_text)
                title.setObjectName("QueueRowTitle")
                title.setStyleSheet("background: transparent;")
                title.setFont(self.parent().font() if self.parent() else QFont())
                title.setAlignment(Qt.AlignmentFlag.AlignLeft)
                title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

                artist = QLabel(artist_text)
                artist.setObjectName("MutedLabel")
                artist.setStyleSheet("""
                    background: transparent;
                    color: #9ca3af;
                """)
                artist.setAlignment(Qt.AlignmentFlag.AlignLeft)
                artist.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

                text_layout.setContentsMargins(0, 0, 0, 0)
                text_layout.setSpacing(0)
                text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                text_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)
                text_layout.addWidget(artist, 0, Qt.AlignmentFlag.AlignLeft)

                layout.addWidget(text_box, 1, Qt.AlignmentFlag.AlignVCenter)

                if show_handle:
                    handle = QLabel("☰")
                    handle.setFixedSize(28, 52)
                    handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    handle.setStyleSheet("""
                        background: transparent;
                        font-size: 18px;
                        padding: 0px;
                        margin: 0px;
                    """)
                    layout.addWidget(handle, 0, Qt.AlignmentFlag.AlignVCenter)
            except Exception as e:
                logger.warning("__init__ caused an unexpected bug: %s", e)

class QueueListWidget(QListWidget):
    deletePressed = Signal()
    selectAllPressed = Signal()

    HANDLE_WIDTH = 40

    def __init__(self, player):
        try:
            super().__init__()
            self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            self.player = player
            self._drag_allowed = False

            self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
            self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def wheelEvent(self, event):
        try:
            smooth_wheel_scroll(self, event)
        except Exception as e:
            logger.warning("wheelEvent caused an unexpected bug: %s", e)

    def mousePressEvent(self, event):
        try:
            self._drag_allowed = (
                event.position().x() >= self.viewport().width() - self.HANDLE_WIDTH
            )

            super().mousePressEvent(event)
        except Exception as e:
            logger.warning("mousePressEvent caused an unexpected bug: %s", e)

    def startDrag(self, supportedActions):
        try:
            if not self._drag_allowed:
                return

            super().startDrag(supportedActions)
        except Exception as e:
            logger.warning("startDrag caused an unexpected bug: %s", e)

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_Delete:
                self.deletePressed.emit()
                return

            if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
                self.selectAll()
                self.selectAllPressed.emit()
                return

            super().keyPressEvent(event)
        except Exception as e:
            logger.warning("keyPressEvent caused an unexpected bug: %s", e)

    def dropEvent(self, event):
        try:
            super().dropEvent(event)
            self.save_queue_order()
        except Exception as e:
            logger.warning("dropEvent caused an unexpected bug: %s", e)

    def save_queue_order(self):
        try:
            new_queue = []

            for i in range(self.count()):
                item = self.item(i)
                song_index = item.data(Qt.UserRole)

                if song_index is not None:
                    new_queue.append(int(song_index))

            self.player.engine.queue = new_queue
            self.player.engine.preset.queue = list(new_queue)
            self.player._autosave_current_preset()
        except Exception as e:
            logger.warning("save_queue_order caused an unexpected bug: %s", e)

class QueueItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        try:
            super().paint(painter, option, index)

            painter.save()

            rect = option.rect

            painter.setPen(option.palette.text().color())

            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)

            handle_rect = QRect(
                rect.right() - 34,
                rect.top(),
                28,
                rect.height()
            )

            painter.drawText(
                handle_rect,
                Qt.AlignmentFlag.AlignCenter,
                "☰"
            )

            painter.restore()
        except Exception as e:
            logger.warning("paint caused an unexpected bug: %s", e)
#endregion

#region Workers
class LoudnessWorker(QObject):
    finished = Signal(str, float)
    failed = Signal(str, str)

    def __init__(self, path: str, target_lufs: float):
        try:
            super().__init__()
            self.path = path
            self.target_lufs = target_lufs
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def run(self):
        try:
            try:
                from librosa import load as lload
                import pyloudnorm as pyln

                data, rate = lload(self.path, sr=None, mono=True)

                meter = pyln.Meter(rate)
                loudness = meter.integrated_loudness(data)

                gain_db = self.target_lufs - loudness
                self.finished.emit(self.path, gain_db)

            except Exception as e:
                self.failed.emit(self.path, str(e))
        except Exception as e:
            logger.warning("run caused an unexpected bug: %s", e)

class LyricsWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, lyric_stuff):
        try:
            super().__init__()
            self.lyric_stuff = lyric_stuff
            self._running = False
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def _emit_status(self, message: str):
        try:
            if not self._running:
                return
            try:
                self.status.emit(str(message))
            except RuntimeError:
                self._running = False
        except Exception as e:
            logger.warning("_emit_status caused an unexpected bug: %s", e)

    def run(self):
        try:
            self._running = True
            self.lyric_stuff.set_status_callback(self._emit_status)
            try:
                data = self.lyric_stuff.convert_lyrics()
                self.finished.emit(data)
            except Exception as e:
                self.failed.emit(str(e))
            finally:
                self._running = False
                self.lyric_stuff.clear_status_callback(self._emit_status)
        except Exception as e:
            logger.warning("run caused an unexpected bug: %s", e)

class LyricsResultBridge(QObject):
    loaded = Signal(object, int, str)
    failed = Signal(str, int, str)
    status = Signal(str, int, str)
#endregion


#region Random
class LyricsFetcher(QObject):
    def __init__(self, LyricStuff):
        try:
            super().__init__()
            self.lyric_stuff = LyricStuff
            self.SEARCH_HEADERS = {
                "user-agent": "Mozilla/5.0",
                "accept": "application/json",
                "origin": "https://www.musixmatch.com",
                "referer": "https://www.musixmatch.com/",
            }

            self.LYRICS_HEADERS = {
                "user-agent": "Mozilla/5.0",
            }
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def _get_json(self, url, params=None, headers=None, timeout=10):
        try:
            if params:
                query = urlencode(params, quote_via=quote)
                url = f"{url}?{query}"

            req = Request(url, headers=headers or {}, method="GET")

            try:
                with urlopen(req, timeout=timeout) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    logger.debug("Lyrics Response: %s", raw[:300])
                    return json.loads(raw)

            except HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                logger.debug(f"HTTP error: {e.code} {e.reason}")
                logger.debug("DEBUG BODY: %s", body[:300])

            except URLError as e:
                logger.debug(f"URL error: {e.reason}")

            except json.JSONDecodeError as e:
                logger.debug(f"JSON error: {e}")

            return {}
        except Exception as e:
            logger.warning("_get_json caused an unexpected bug: %s", e)

    def fetch(self, artist, title):
        try:
            logger.debug("Started Lyrics Fetch (%s - %s)", artist, title)
            song_looking_for = self.lyric_stuff.engine.get_current_song()
            self.MUSIXMATCH_USER_TOKEN = self.lyric_stuff.engine.preset.MUSIXMATCH_USER_TOKEN

            tracks = self.search_track(artist, title)
            self.lyric_stuff.emit_status("Trying Musixmatch...")
            if tracks:
                new_song = self.lyric_stuff.engine.get_current_song()
                if new_song != song_looking_for:
                    logger.debug("Fetch failed: song changed")
                    return None
                for item in tracks:
                    track = item.get("track", {})
                    track_id = track.get("track_id")

                    has_lyrics = track.get("has_lyrics")
                    has_subtitles = track.get("has_subtitles")

                    if not has_lyrics and not has_subtitles:
                        logger.debug(
                            "Skipping no-lyrics result: %s - %s",
                            track.get("artist_name"),
                            track.get("track_name"),
                        )
                        continue

                    if not track_id:
                        continue

                    logger.debug("Trying: %s - %s", track.get("artist_name"), track.get("track_name"))

                    lyrics = self.get_lyrics(track_id)

                    if lyrics:
                        logger.debug("🟣 Lyrics found")
                        return lyrics
            else:
                logger.debug("No Musixmatch results found.")

            logger.debug("Trying fallback providers...")
            self.lyric_stuff.emit_status("Trying fallback...")

            for fallback in (
                self.fetch_from_lrclib,
                self.fetch_from_lyrics_ovh,
                self.fetch_from_vocadb,
                self.fetch_from_vocaloid_wiki,
            ):
                try:
                    new_song = self.lyric_stuff.engine.get_current_song()
                    if new_song != song_looking_for:
                        logger.debug("Fetch failed: song changed")
                        return None
                    lyrics = fallback(artist, title)

                    if lyrics:
                        logger.debug("🟣 Lyrics found from fallback: %s", fallback.__name__)
                        return lyrics

                except Exception as e:
                    logger.warning("🟡 Fallback failed (%s): %s", fallback.__name__, e)

            logger.debug("No lyrics found.")
            return None
        except Exception as e:
            logger.warning("fetch caused an unexpected bug: %s", e)

    def search_track(self, artist, title):
        try:
            url = "https://apic-desktop.musixmatch.com/ws/1.1/track.search"

            params = {
                "q_artist": artist,
                "q_track": title,
                "page_size": 5,
                "s_track_rating": "desc",
                "app_id": "web-desktop-app-v1.0",
                "usertoken": self.MUSIXMATCH_USER_TOKEN,
            }

            data = self._get_json(url, params=params, headers=self.SEARCH_HEADERS)

            if not isinstance(data, dict):
                return []

            message = data.get("message")
            if not isinstance(message, dict):
                return []

            body = message.get("body")
            if not isinstance(body, dict):
                return []

            track_list = body.get("track_list")
            if isinstance(track_list, list):
                return track_list

            return []
        except Exception as e:
            logger.warning("search_track caused an unexpected bug: %s", e)

    def get_lyrics(self, track_id):
        try:
            endpoints = [
                ("track.subtitle.get", "subtitle", "subtitle_body", {"subtitle_format": "lrc"}),
                ("track.lyrics.get", "lyrics", "lyrics_body", {}),
            ]

            for endpoint_name, body_key, text_key, extra_params in endpoints:
                url = f"https://apic-desktop.musixmatch.com/ws/1.1/{endpoint_name}"

                params = {
                    "track_id": track_id,
                    "app_id": "web-desktop-app-v1.0",
                    "usertoken": self.MUSIXMATCH_USER_TOKEN,
                    **extra_params,
                }

                data = self._get_json(url, params=params, headers=self.LYRICS_HEADERS)

                if not isinstance(data, dict):
                    continue

                message = data.get("message")
                if not isinstance(message, dict):
                    continue

                header = message.get("header")
                if not isinstance(header, dict):
                    header = {}

                status_code = header.get("status_code")
                if status_code != 200:
                    logger.debug("%s failed. Status: %s", endpoint_name, status_code)
                    continue

                body = message.get("body")
                if not isinstance(body, dict):
                    logger.debug("%s returned non-dict body: %r", endpoint_name, body)
                    continue

                lyrics_obj = body.get(body_key)
                if not isinstance(lyrics_obj, dict):
                    logger.debug("%s returned non-dict %s: %r", endpoint_name, body_key, lyrics_obj)
                    continue

                lyrics = lyrics_obj.get(text_key)
                if isinstance(lyrics, str) and lyrics.strip():
                    return lyrics.split("*******")[0].strip()

            return None
        except Exception as e:
            logger.warning("get_lyrics caused an unexpected bug: %s", e)

    def clean_wiki_text(self, text: str):
        try:
            text = re.sub(r"\{\{[^{}]*\}\}", "", text)
            text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
            text = re.sub(r"==+.*?==+", "", text)
            return text.strip()
        except Exception as e:
            logger.warning("clean_wiki_text caused an unexpected bug: %s", e)

    def fetch_from_lrclib(self, artist, title):
        try:
            logger.debug("Trying LRCLIB...")
            self.lyric_stuff.emit_status("Trying LRCLIB...")
            url = "https://lrclib.net/api/search"

            params = {
                "artist_name": artist,
                "track_name": title,
            }

            data = self._get_json(url, params=params)

            if not isinstance(data, list) or not data:
                return None

            best = data[0]

            synced = best.get("syncedLyrics")
            plain = best.get("plainLyrics")

            if isinstance(synced, str) and synced.strip():
                logger.debug("Fallback success: LRCLIB synced")
                return synced.strip()

            if isinstance(plain, str) and plain.strip():
                logger.debug("Fallback success: LRCLIB plain")
                return plain.strip()

            logger.debug("Fallback failed: LRCLIB")
            return None
        except Exception as e:
            logger.warning("fetch_from_lrclib caused an unexpected bug: %s", e)

    def fetch_from_lyrics_ovh(self, artist, title):
        try:
            logger.debug("Trying lyrics.ovh...")
            self.lyric_stuff.emit_status("Trying lyrics.ovh...")
            url = f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"

            data = self._get_json(url)

            if not isinstance(data, dict):
                return None

            lyrics = data.get("lyrics")

            if isinstance(lyrics, str) and lyrics.strip():
                logger.debug("Fallback success: lyrics.ovh")
                return lyrics.strip()

            logger.debug("Fallback failed: lyrics.ovh")
            return None
        except Exception as e:
            logger.warning("fetch_from_lyrics_ovh caused an unexpected bug: %s", e)

    def fetch_from_vocaloid_wiki(self, artist, title):
        try:
            logger.debug("Trying Vocaloid Wiki...")
            self.lyric_stuff.emit_status("Trying Vocaloid Wiki...")
            url = "https://vocaloidlyrics.miraheze.org/w/api.php"

            params = {
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "titles": title,
                "format": "json",
                "formatversion": 2,
            }

            data = self._get_json(url, params=params)

            if not isinstance(data, dict):
                return None

            pages = data.get("query", {}).get("pages", [])

            if not pages:
                return None

            page = pages[0]

            if page.get("missing"):
                return None

            revisions = page.get("revisions")

            if not revisions:
                return None

            text = revisions[0]["slots"]["main"]["content"]
            text = self.clean_wiki_text(text)

            if len(text) > 50:
                logger.debug("Fallback success: Vocaloid Wiki")
                return text.strip()

            logger.debug("Fallback failed: Vocaloid Wiki")
            return None
        except Exception as e:
            logger.warning("fetch_from_vocaloid_wiki caused an unexpected bug: %s", e)

    def _get_text(self, url, headers=None, timeout=10):
        try:
            req = Request(url, headers=headers or {"user-agent": "Mozilla/5.0"}, method="GET")

            try:
                with urlopen(req, timeout=timeout) as response:
                    return response.read().decode("utf-8", errors="replace")
            except Exception as e:
                logger.debug("Text fetch failed: %s", e)
                return ""
        except Exception as e:
            logger.warning("_get_text caused an unexpected bug: %s", e)

    def fetch_vocadb_lyrics_id_from_page(self, song_id):
        try:
            text = self._get_text(f"https://vocadb.net/api/songs/{song_id}")
            try:
                song = json.loads(text)
            except json.JSONDecodeError:
                return None

            ids_to_try = [song_id]
            original_id = song.get("originalVersionId")
            if original_id:
                ids_to_try.append(original_id)

            for sid in ids_to_try:
                text = self._get_text(
                    f"https://vocadb.net/api/songs?query=id:{sid}&fields=lyrics&maxResults=1"
                )

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue

                items = data.get("items") or []
                if not items:
                    continue

                lyrics = items[0].get("lyrics") or []
                if lyrics:
                    lyrics_id = int(lyrics[0]["id"])
                    logger.debug("Found VocaDB lyricsId from API: %s", lyrics_id)
                    return lyrics_id
            html = self._get_text(f"https://vocadb.net/S/{song_id}/lyrics?lyricsId=")

            match = re.search(r'lyricsId=(\d+)', html)
            if match:
                return int(match.group(1))

            logger.debug("Could not find VocaDB lyricsId for song %s", song_id)
            return None
        except Exception as e:
            logger.warning("fetch_vocadb_lyrics_id_from_page caused an unexpected bug: %s", e)

    def fetch_from_vocadb(self, artist, title):
        try:
            logger.debug("Trying VocaDB...")
            self.lyric_stuff.emit_status("Trying VocaDB...")

            search_queries = [
                f"{artist} {title}",
                title,
                re.sub(r"\s*-\s*", " ", title),
                re.sub(r"\s*\(.*?\)\s*", " ", title).strip(),
            ]

            seen = set()

            for query in search_queries:
                query = " ".join(query.split())

                if not query or query in seen:
                    continue

                seen.add(query)

                url = "https://vocadb.net/api/songs"

                params = {
                    "query": query,
                    "maxResults": 10,
                    "fields": "Lyrics",
                    "nameMatchMode": "Auto",
                }

                data = self._get_json(url, params=params)

                if not isinstance(data, dict):
                    continue

                items = data.get("items")

                if not isinstance(items, list) or not items:
                    logger.debug("VocaDB no results for query: %s", query)
                    continue

                for song in items:
                    song_id = song.get("id")

                    if not song_id:
                        continue

                    lyrics_list = song.get("lyrics", [])

                    if not lyrics_list:
                        logger.debug(
                            "VocaDB song found but API returned no lyrics list: %s; trying page scrape",
                            song_id
                        )

                        lyrics = self.fetch_from_vocadb_by_song_id(song_id)

                        if lyrics:
                            return lyrics.strip()

                        continue

                    for lyric_entry in lyrics_list:
                        lyric_id = lyric_entry.get("id")

                        if not lyric_id:
                            continue

                        lyrics = self.fetch_vocadb_lyrics(lyric_id)

                        if lyrics:
                            logger.debug("Fallback success: VocaDB")
                            return lyrics.strip()

            logger.debug("Fallback failed: VocaDB no usable lyrics")
            return None
        except Exception as e:
            logger.warning("fetch_from_vocadb caused an unexpected bug: %s", e)

    def fetch_from_vocadb_by_song_id(self, song_id):
        try:
            logger.debug("Trying VocaDB song ID page scrape: %s", song_id)

            lyric_id = self.fetch_vocadb_lyrics_id_from_page(song_id)

            if lyric_id:
                return self.fetch_vocadb_lyrics(lyric_id)

            return None
        except Exception as e:
            logger.warning("fetch_from_vocadb_by_song_id caused an unexpected bug: %s", e)

    def fetch_vocadb_lyrics(self, lyric_id):
        try:
            logger.debug("Trying VocaDB lyric ID: %s", lyric_id)

            url = f"https://vocadb.net/api/songs/lyrics/{lyric_id}"
            data = self._get_json(url)

            if not isinstance(data, dict):
                return None

            lyrics = data.get("value")

            if isinstance(lyrics, str) and lyrics.strip():
                logger.debug("Fallback success: VocaDB lyric value")
                return lyrics.strip()

            logger.debug("VocaDB lyric failed. Data: %r", data)
            return None
        except Exception as e:
            logger.warning("fetch_vocadb_lyrics caused an unexpected bug: %s", e)

class ThemeThing(QObject):
    def __init__(self, player):
        try:
            super().__init__()
            self.player = player
            self.current_theme = DEFAULT_THEME.copy()
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def refresh_current_theme(self):
        try:
            if not hasattr(self.player, "current_theme") or self.player.current_theme is None:
                self.player.current_theme = DEFAULT_THEME.copy()

            self.current_theme = self.player.current_theme
            return self.current_theme
        except Exception as e:
            logger.warning("refresh_current_theme caused an unexpected bug: %s", e)

    def change_bg_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "bg", color.name())
        except Exception as e:
            logger.warning("change_bg_color caused an unexpected bug: %s", e)

    def change_text_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "text", color.name())
        except Exception as e:
            logger.warning("change_text_color caused an unexpected bug: %s", e)

    def change_muted_text_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "muted_text", color.name())
        except Exception as e:
            logger.warning("change_muted_text_color caused an unexpected bug: %s", e)

    def change_panel_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "panel", color.name())
        except Exception as e:
            logger.warning("change_panel_color caused an unexpected bug: %s", e)

    def change_panel_active_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "panel_active", color.name())
        except Exception as e:
            logger.warning("change_panel_active_color caused an unexpected bug: %s", e)

    def change_border_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "border", color.name())
        except Exception as e:
            logger.warning("change_border_color caused an unexpected bug: %s", e)

    def change_border_hover_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "border_hover", color.name())
        except Exception as e:
            logger.warning("change_border_hover_color caused an unexpected bug: %s", e)

    def change_border_selected_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "border_selected", color.name())
        except Exception as e:
            logger.warning("change_border_selected_color caused an unexpected bug: %s", e)

    def change_border_disabled_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "border_disabled", color.name())
        except Exception as e:
            logger.warning("change_border_disabled_color caused an unexpected bug: %s", e)

    def change_button_hover_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "button_hover", color.name())
        except Exception as e:
            logger.warning("change_button_hover_color caused an unexpected bug: %s", e)

    def change_button_pressed_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "button_pressed", color.name())
        except Exception as e:
            logger.warning("change_button_pressed_color caused an unexpected bug: %s", e)

    def change_accent_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "accent", color.name())
        except Exception as e:
            logger.warning("change_accent_color caused an unexpected bug: %s", e)

    def change_accent_hover_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "accent_hover", color.name())
        except Exception as e:
            logger.warning("change_accent_hover_color caused an unexpected bug: %s", e)

    def change_selection_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "selection", color.name())
        except Exception as e:
            logger.warning("change_selection_color caused an unexpected bug: %s", e)

    def change_slider_bg_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "slider_bg", color.name())
        except Exception as e:
            logger.warning("change_slider_bg_color caused an unexpected bug: %s", e)

    def change_disabled_text_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                set_theme_value(self, "disabled_text", color.name())
        except Exception as e:
            logger.warning("change_disabled_text_color caused an unexpected bug: %s", e)
#endregion


#region Main Things
@dataclass
class Preset:
    show_console: bool = False
    logging_level: int = 0
    main_window_geometry: dict | None = None
    lyrics_window_geometry: dict | None = None
    floating_window_geometry: dict | None = None
    muted: bool = False
    shuffle: bool = True
    repeat: bool = False
    current_song: int = 0
    volume: float = 100
    lyrics_window: bool = False
    lyrics_window_on_top: bool = False
    floating_lyrics: bool = False
    floating_lyrics_on_top: bool = False
    romaji: bool = False
    translated: bool = False
    library_sort_mode: int = 2
    library_show_images: bool = True
    normalize_audio: bool = True
    online_lyrics: bool = True
    download_lyrics: bool = True
    MUSIXMATCH_USER_TOKEN: str = ''
    queue: list[int] | None = None
    tab_order: list[str] | None = None



class Audio(QObject):
    songEnded = Signal()
    playbackStateChanged = Signal(int)
    mediaOpenedQt = Signal()
    smtcButtonPressedQt = Signal(int)
    def __init__(self, player) -> None:
        try:
            super().__init__()
            self.player = player
            self.preset = Preset()
            self.lyrics = LyricStuff(self)

            self.audio_player = MediaPlayer()
            self.audio_player.auto_play = False
            self.audio_player.command_manager.is_enabled = False
        
            self.history = deque(maxlen=50)
            self.forward_history = deque(maxlen=50)
            self.recent_shuffle = deque(maxlen=10)
            self.play_order = deque(maxlen=50)

            self.pause_timer = QTimer()
            self.pause_timer.setSingleShot(True)
            self.pause_timer.timeout.connect(self._pause_timer_finished)

            self._current_media_path = None
            self._can_use_forward = False
            self.queue = []
            self.play_order_pos = -1
            self._nav_locked = False
            self._pending_next_clicks = 0
            self._pending_back_clicks = 0
            self._metadata_cache = {}
            self._loudness_cache = {}
            self.target_lufs = -14.0
            self.normalize_audio = self.preset.normalize_audio
            self.online_lyrics = self.preset.online_lyrics
            self.download_lyrics = self.preset.download_lyrics
            self.queue_auto_enabled = True

            self._session = self.audio_player.playback_session
            self._session.add_playback_state_changed(self._on_playback_state_changed)
            self.audio_player.add_media_opened(self._on_media_opened)
            self.audio_player.add_media_ended(self._on_media_ended)
            self.audio_player.add_media_failed(self._on_media_failed)
            self._smtc = self.audio_player.system_media_transport_controls
            self._configure_smtc()

            self.playbackStateChanged.connect(self._apply_playback_state_on_qt_thread)
            self.mediaOpenedQt.connect(self._apply_media_opened_on_qt_thread)
            self.smtcButtonPressedQt.connect(self._handle_smtc_button_on_qt_thread)
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def _finish_nav(self):
        try:
            self._nav_locked = False

            if self._pending_back_clicks > 0:
                self._pending_back_clicks -= 1
                self.back()
                return

            if self._pending_next_clicks > 0:
                self._pending_next_clicks -= 1
                self.next()
                return
        except Exception as e:
            logger.warning("_finish_nav caused an unexpected bug: %s", e)

    def _unlock_nav(self):
        try:
            self._nav_locked = False
        except Exception as e:
            logger.warning("_unlock_nav caused an unexpected bug: %s", e)

    def _first_text(self, value, fallback: str) -> str:
        try:
            try:
                if value is None:
                    return fallback

                if isinstance(value, (list, tuple)):
                    if not value:
                        return fallback
                    value = value[0]

                value = str(value).strip()
                return value if value else fallback

            except Exception:
                return fallback
        except Exception as e:
            logger.warning("_first_text caused an unexpected bug: %s", e)

    def _extract_cover_from_mutagen(self, path: str, mf) -> str:
        try:
            try:
                cover_data = None
                mime = "image/jpeg"

                if mf is None:
                    return BLANK_PATH

                if hasattr(mf, "pictures") and mf.pictures:
                    pic = mf.pictures[0]
                    cover_data = pic.data
                    mime = getattr(pic, "mime", "image/jpeg") or "image/jpeg"

                if cover_data is None and hasattr(mf, "get"):
                    pics = mf.get("metadata_block_picture")

                    if pics:
                        pic = Picture(base64.b64decode(pics[0]))
                        cover_data = pic.data
                        mime = pic.mime or "image/jpeg"

                if cover_data is None and hasattr(mf, "tags") and mf.tags:
                    for key in mf.tags.keys():
                        if str(key).startswith("APIC"):
                            apic = mf.tags[key]
                            cover_data = apic.data
                            mime = getattr(apic, "mime", "image/jpeg") or "image/jpeg"
                            break

                if cover_data is None and hasattr(mf, "tags") and mf.tags:
                    covr = mf.tags.get("covr")

                    if covr:
                        cover_data = bytes(covr[0])
                        mime = "image/jpeg"

                if not cover_data:
                    return BLANK_PATH

                os.makedirs(TEMP_DIR, exist_ok=True)

                ext = "jpg" if mime in ("image/jpeg", "image/jpg") else "png"
                h = hashlib.sha256(path.encode("utf-8", errors="ignore")).hexdigest()
                cover_path = os.path.join(TEMP_DIR, f"cover_{h}.{ext}")

                if not os.path.exists(cover_path):
                    with open(cover_path, "wb") as f:
                        f.write(cover_data)

                return cover_path

            except Exception as e:
                logger.warning("🟡 Cover extraction failed for %s: %s", os.path.basename(path), e)
                return BLANK_PATH
        except Exception as e:
            logger.warning("_extract_cover_from_mutagen caused an unexpected bug: %s", e)

    def get_data_for_path(self, path: str):
        try:
            if not path or not os.path.isfile(path):
                return "Unknown Artist", os.path.basename(path or ""), BLANK_PATH

            cached = self._metadata_cache.get(path)
            if cached:
                return cached

            fallback_title = os.path.splitext(os.path.basename(path))[0]

            try:
                artist = "Unknown Artist"
                title = fallback_title

                easy = MutagenFile(path, easy=True)

                if easy is not None and hasattr(easy, "get"):
                    artist = self._first_text(easy.get("artist"), artist)
                    title = self._first_text(easy.get("title"), title)

                    if artist == "Unknown Artist":
                        artist = self._first_text(easy.get("albumartist"), artist)

                raw = MutagenFile(path)
                cover_path = self._extract_cover_from_mutagen(path, raw)

                result = (artist, title, cover_path)
                self._metadata_cache[path] = result
                return result

            except Exception as e:
                logger.warning("🟡 Failed to read metadata for %s: %s", os.path.basename(path), e)
                result = ("Unknown Artist", fallback_title, BLANK_PATH)
                self._metadata_cache[path] = result
                return result
        except Exception as e:
            logger.warning("get_data_for_path caused an unexpected bug: %s", e)

    def _apply_playback_state_on_qt_thread(self, state_value: int):
        try:
            try:
                state = MediaPlaybackState(state_value)

                if state == MediaPlaybackState.PLAYING:
                    pass
                elif state == MediaPlaybackState.PAUSED:
                    pass
                elif state == MediaPlaybackState.OPENING:
                    pass
                else:
                    self.player.pause_btn.setText("Pause")

                self._update_smtc_playback_status()

            except Exception as e:
                logger.warning("🟡 Qt playback-state apply failed: %s", e)
        except Exception as e:
            logger.warning("_apply_playback_state_on_qt_thread caused an unexpected bug: %s", e)

    def _apply_media_opened_on_qt_thread(self):
        try:
            if getattr(self, "_media_open_request_path", None) != self.get_current_song():
                return
            try:
                artist, title, cover_path = self.get_data()

                self.player._load_lyrics_for_current_song()

                self.player._set_now_playing_info(artist, title)
                self.player.setWindowTitle(
                    f"Yet Another Music Player — {self.player._get_current_preset_name()} — {artist} — {title}"
                )

                pixmap = QPixmap(cover_path)
                self.player.label.setPixmap(pixmap)
                self.player.cover_path = cover_path

                self.player._select_library_song_by_index(self.player.current_song)

                self._update_windows_popup(title, artist, cover_path)
                self._update_smtc_playback_status()

            except Exception as e:
                logger.warning("🟡 Qt media-opened apply failed: %s", e)
        except Exception as e:
            logger.warning("_apply_media_opened_on_qt_thread caused an unexpected bug: %s", e)

    def _configure_smtc(self):
        try:
            smtc = self._smtc
            smtc.is_enabled = True
            smtc.is_play_enabled = True
            smtc.is_pause_enabled = True
            smtc.is_next_enabled = True
            smtc.is_previous_enabled = True

            smtc.add_button_pressed(self._on_smtc_button_pressed)
        except Exception as e:
            logger.warning("_configure_smtc caused an unexpected bug: %s", e)

    def _on_smtc_button_pressed(self, sender, args):
        try:
            try:
                self.smtcButtonPressedQt.emit(int(args.button))
            except Exception as e:
                logger.warning("🟡 SMTC button event failed: %s", e)
        except Exception as e:
            logger.warning("_on_smtc_button_pressed caused an unexpected bug: %s", e)

    def _handle_smtc_button_on_qt_thread(self, button_value: int):
        try:
            try:
                button = SystemMediaTransportControlsButton(button_value)

                if button == SystemMediaTransportControlsButton.PLAY:
                    self.play()
                elif button == SystemMediaTransportControlsButton.PAUSE:
                    self.pause()
                elif button == SystemMediaTransportControlsButton.NEXT:
                    self.next()
                elif button == SystemMediaTransportControlsButton.PREVIOUS:
                    self.back()

            except Exception as e:
                logger.warning("SMTC Qt-thread button handling failed: %s", e)
        except Exception as e:
            logger.warning("_handle_smtc_button_on_qt_thread caused an unexpected bug: %s", e)

    def get_current_song(self):
        try:
            index = getattr(self.player, "current_song", 0)
            data = self.player.songs.get(str(index))

            if not data:
                return None

            path = data.get("path")
            if not path or not os.path.isfile(path):
                return None

            return path
        except Exception as e:
            logger.warning("get_current_song caused an unexpected bug: %s", e)

    def get_data(self):
        try:
            current_song = self.get_current_song()
            if not current_song:
                return "Unknown Artist", "Unknown Title", BLANK_PATH

            return self.get_data_for_path(current_song)
        except Exception as e:
            logger.warning("get_data caused an unexpected bug: %s", e)

    def db_to_linear(self, db):
        try:
            return 10 ** (db / 20)
        except Exception as e:
            logger.warning("db_to_linear caused an unexpected bug: %s", e)

    def start_loudness_analysis(self, path: str):
        try:
            try:
                logger.debug("Loudness Analysis Started: %s", path)
                if not self.normalize_audio:
                    return
                if not path:
                    return
                if path in self._loudness_cache:
                    return
                if not hasattr(self, "_loudness_threads"):
                    self._loudness_threads = {}
                if not hasattr(self, "_pending_loudness_paths"):
                    self._pending_loudness_paths = deque(maxlen=5)
                if len(self._loudness_threads) >= 1:
                    if path not in self._pending_loudness_paths:
                        self._pending_loudness_paths.append(path)
                    return
                if path in self._loudness_threads:
                    return

                thread = QThread()
                worker = LoudnessWorker(path, self.target_lufs)
                worker.moveToThread(thread)

                self._loudness_threads[path] = (thread, worker)

                thread.started.connect(worker.run)
                worker.finished.connect(self._loudness_finished)
                worker.failed.connect(self._loudness_failed)
                worker.finished.connect(thread.quit)
                worker.failed.connect(thread.quit)
                thread.finished.connect(worker.deleteLater)
                thread.finished.connect(thread.deleteLater)
                thread.finished.connect(
                    lambda p=path: self._clear_loudness_worker(p)
                )

                thread.start()

            except Exception as e:
                logger.warning("start_loudness_analysis crashed: %s", e)
        except Exception as e:
            logger.warning("start_loudness_analysis caused an unexpected bug: %s", e)

    def _loudness_finished(self, path: str, gain_db: float):
        try:
            try:
                self._loudness_cache[path] = gain_db

                logger.debug(
                    "Loudness gain ready: %.2f dB | %s",
                    gain_db,
                    os.path.basename(path)
                )

                if self.normalize_audio and path == self.get_current_song():
                    self.volume(self.preset.volume)
            except Exception as e:
                logger.warning("_loudness_finished crashed: %s", e)
        except Exception as e:
            logger.warning("_loudness_finished caused an unexpected bug: %s", e)

    def _loudness_failed(self, path: str, error: str):
        try:
            try:
                logger.warning("Loudness normalization failed for %s: %s", path, error)
                self._loudness_cache[path] = 0.0
            except Exception as e:
                logger.warning("_loudness_failed crashed: %s", e)
        except Exception as e:
            logger.warning("_loudness_failed caused an unexpected bug: %s", e)

    def _clear_loudness_worker(self, path: str):
        try:
            try:
                if hasattr(self, "_loudness_threads"):
                    self._loudness_threads.pop(path, None)
                if hasattr(self, "_pending_loudness_paths"):
                    while self._pending_loudness_paths:
                        next_path = self._pending_loudness_paths.popleft()
                        if (next_path and next_path not in self._loudness_cache and next_path not in self._loudness_threads):
                            QTimer.singleShot(0, lambda p=next_path:self.start_loudness_analysis(p))
                            break

            except Exception as e:
                logger.warning("_clear_loudness_worker crashed: %s", e)
        except Exception as e:
            logger.warning("_clear_loudness_worker caused an unexpected bug: %s", e)

    def get_loudness_gain(self, path, target_lufs=None):
        try:
            global LIB_AND_PYLN_IMPORTED
            if target_lufs is None:
                target_lufs = self.target_lufs

            cached = self._loudness_cache.get(path)
            if cached is not None:
                return cached

            try:
                if LIB_AND_PYLN_IMPORTED == False:
                    from librosa import load as lload
                    import pyloudnorm as pyln
                    LIB_AND_PYLN_IMPORTED = True
                data, rate = lload(path, sr=None, mono=True)

                if len(data.shape) > 1:
                    data = data.mean(axis=1)

                meter = pyln.Meter(rate)
                loudness = meter.integrated_loudness(data)

                gain_db = target_lufs - loudness

                self._loudness_cache[path] = gain_db

                logger.info(
                    "🟣 Loudness: %.2f LUFS | Gain: %.2f dB | %s",
                    loudness,
                    gain_db,
                    os.path.basename(path)
                )

                return gain_db

            except Exception as e:
                logger.warning("🟡 Loudness normalization failed: %s", e)
                return 0.0
        except Exception as e:
            logger.warning("get_loudness_gain caused an unexpected bug: %s", e)

    def _path_to_uri(self, path: str) -> Uri:
        try:
            full = str(Path(path).resolve())

            uri_str = "file:///" + full.replace("\\", "/")

            return Uri(uri_str)
        except Exception as e:
            logger.warning("_path_to_uri caused an unexpected bug: %s", e)

    def play(self, force_reload: bool = False):
        try:
            try:
                song = self.get_current_song()

                if not song:
                    QMessageBox.warning(self.player, "No songs", "No songs are loaded.")
                    return

                if not os.path.exists(song):
                    logger.warning("🟡 Song file missing: %s", song)
                    return

                if self.queue_auto_enabled and hasattr(self.player, "_fill_queue"):
                    try:
                        self.player._fill_queue()
                    except Exception as e:
                        logger.warning("🟡 _fill_queue failed: %s", e)

                if not self.play_order:
                    self.play_order = [self.player.current_song]
                    self.play_order_pos = 0
                artist, title, cover_path = self.get_data()
                must_reload = force_reload or self._current_media_path != song

                if must_reload:
                    try:
                        full_path = str(Path(song).resolve())
                        source = MediaSource.create_from_uri(self._path_to_uri(full_path))
                        self.audio_player.source = source
                        self._current_media_path = song
                        self._media_open_request_path = song
                        self.player._reset_progress_ui()
                    except Exception as e:
                        logger.warning("🟡 Media reload failed: %s", e)
                        return

                try:
                    self.audio_player.play()
                except Exception as e:
                    logger.warning("🟡 audio_player.play failed: %s", e)
                    return

                if self.normalize_audio and not self._session.playback_state == MediaPlaybackState.PAUSED and not self._session.playback_state == MediaPlaybackState.PLAYING:
                    self.start_loudness_analysis(song)

                self.volume(self.preset.volume)

                try:
                    self.player._set_now_playing_info(artist, title)
                    self.player.setWindowTitle(f"Yet Another Music Player — {self.player._get_current_preset_name()} — {artist} — {title}")
                except Exception as e:
                    logger.warning("🟡 UI update failed: %s", e)

                try:
                    pixmap = QPixmap(cover_path)
                    if not pixmap.isNull():
                        self.player.label.setPixmap(pixmap)
                    self.player.cover_path = cover_path
                except Exception as e:
                    logger.warning("🟡 Cover update failed: %s", e)

                try:
                    self.player._select_library_song_by_index(self.player.current_song)
                except Exception as e:
                    logger.warning("🟡 Library selection failed: %s", e)

                if not must_reload:
                    try:
                        self._update_windows_popup(title, artist, cover_path)
                        self._update_smtc_playback_status()
                    except Exception as e:
                        logger.warning("🟡 Popup/SMTC update failed: %s", e)

                if self.preset.lyrics_window:
                    try:
                        self.lyrics.show_window()
                    except Exception as e:
                        logger.warning("🟡 Lyrics window failed: %s", e)
                if self.preset.floating_lyrics:
                    try:
                        self.lyrics.show_floating_window()
                    except Exception as e:
                        logger.warning("🟡 Floating lyrics failed: %s", e)

            except Exception as e:
                logger.exception("💥 play crashed: %s", e)
        except Exception as e:
            logger.warning("play caused an unexpected bug: %s", e)

    def stop(self):
        try:
            self.audio_player.pause()
            self.audio_player.source = None
            self._current_media_path = None
            self.player._reset_progress_ui()
            self.player.pause_btn.setText("Pause")
            self._can_use_forward = False

            self.lyrics.hide_window()
            self.lyrics.hide_floating_window()

            try:
                self._smtc.playback_status = MediaPlaybackStatus.CLOSED
            except Exception as e:
                logger.warning("🟡 SMTC stop status failed: %s", e)
        except Exception as e:
            logger.warning("stop caused an unexpected bug: %s", e)

    def pause(self):
        try:
            try:
                state = self._session.playback_state

                if state == MediaPlaybackState.PLAYING:
                    self.audio_player.pause()
                    self.player.pause_btn.setText("Resume")
                    logger.debug("🟣 Paused")

                    self.pause_timer.start(5_000)

                else:
                    if self.pause_timer.isActive():
                        self.pause_timer.stop()
                    else:
                        if self.preset.lyrics_window:
                            self.lyrics.show_window()
                        if self.preset.floating_lyrics:
                            self.lyrics.show_floating_window()

                    self.audio_player.play()
                    self.player.pause_btn.setText("Pause")
                    logger.debug("🟣 Resumed")

            except Exception as e:
                logger.warning("🟡 pause crashed: %s", e)
        except Exception as e:
            logger.warning("pause caused an unexpected bug: %s", e)

    def _pause_timer_finished(self):
        try:
            if self.preset.lyrics_window:
                self.lyrics.hide_window()
            if self.preset.floating_lyrics:
                self.lyrics.hide_floating_window()
            logger.debug("Pause timer finished")
        except Exception as e:
            logger.warning("_pause_timer_finished caused an unexpected bug: %s", e)

    def set_shuffle(self, enabled: bool):
        try:
            self.preset.shuffle = bool(enabled)
        except Exception as e:
            logger.warning("set_shuffle caused an unexpected bug: %s", e)

    def set_repeat(self, enabled: bool):
        try:
            self.preset.repeat = bool(enabled)
        except Exception as e:
            logger.warning("set_repeat caused an unexpected bug: %s", e)

    def set_muted(self, muted: bool):
        try:
            self.preset.muted = bool(muted)
            self.audio_player.is_muted = self.preset.muted
        except Exception as e:
            logger.warning("set_muted caused an unexpected bug: %s", e)

    def volume(self, volume: float):
        try:
            try:
                self.preset.volume = volume

                final_volume = float(volume) / 100.0

                if self.normalize_audio:
                    song = self.get_current_song()

                    if song:
                        gain_db = self._loudness_cache.get(song, 0.0)
                        final_volume *= self.db_to_linear(gain_db)

                self.audio_player.volume = max(0.0, min(final_volume, 1.0))

            except Exception as e:
                logger.warning("🟡 volume crashed: %s", e)
        except Exception as e:
            logger.warning("volume caused an unexpected bug: %s", e)

    def next(self):
        try:
            try:
                if self._nav_locked:
                    self._pending_next_clicks = min(self._pending_next_clicks + 1, 5)
                    return

                self._nav_locked = True
                QTimer.singleShot(300, self._finish_nav)

                songs = self.player.get_song_list()

                if not songs:
                    self._finish_nav()
                    return

                old_index = self.player.current_song

                if self.queue_auto_enabled and self.queue:
                    try:
                        new_index = self.queue.pop(0)
                    except Exception:
                        self._finish_nav()
                        return

                    if self.play_order_pos < len(self.play_order) - 1:
                        self.play_order = self.play_order[:self.play_order_pos + 1]

                    self.play_order.append(new_index)
                    self.play_order_pos = len(self.play_order) - 1


                    if hasattr(self.player, "_fill_queue"):
                        try:
                            self.player._fill_queue()
                        except Exception:
                            pass

                elif self.play_order_pos < len(self.play_order) - 1:
                    self.play_order_pos += 1
                    new_index = self.play_order[self.play_order_pos]

                else:
                    if self.preset.shuffle:
                        new_index = self._pick_shuffle_song(old_index, songs)
                        self.recent_shuffle.append(new_index)
                    else:
                        new_index = (old_index + 1) % len(songs)

                    self.play_order.append(new_index)
                    self.play_order_pos = len(self.play_order) - 1

                self.history.append(old_index)

                self.player.current_song = new_index
                self.preset.current_song = new_index

                self.play(force_reload=True)

                self.player._autosave_current_preset()

            except Exception as e:
                logger.exception("next crashed: %s", e)
                self._finish_nav()
        except Exception as e:
            logger.warning("next caused an unexpected bug: %s", e)

    def back(self):
        try:
            try:
                if self._nav_locked:
                    self._pending_back_clicks = min(self._pending_back_clicks + 1, 5)
                    return

                self._nav_locked = True
                QTimer.singleShot(300, self._finish_nav)

                songs = self.player.get_song_list()

                if not songs:
                    self._finish_nav()
                    return

                leaving_index = self.player.current_song

                if self.play_order_pos > 0:
                    self.play_order_pos -= 1
                    previous_index = self.play_order[self.play_order_pos]
                    self.player.current_song = previous_index

                elif self.history:
                    previous_index = self.history.pop()
                    self.player.current_song = previous_index

                else:
                    self._finish_nav()
                    return

                if leaving_index not in self.queue:
                    self.queue.insert(0, leaving_index)

                if len(self.queue) > self.player.QUEUE_LIMIT:
                    self.queue = self.queue[:self.player.QUEUE_LIMIT]

                if hasattr(self.player, "_fill_queue"):
                    try:
                        self.player._fill_queue()
                    except Exception:
                        pass

                if hasattr(self.player, "_queue_changed"):
                    try:
                        self.player._queue_changed()
                    except Exception:
                        pass

                if hasattr(self.player, "_refresh_queue_list"):
                    try:
                        self.player._refresh_queue_list()
                    except Exception:
                        pass

                self.preset.current_song = self.player.current_song

                self.play(force_reload=True)

                self.player._autosave_current_preset()

            except Exception as e:
                logger.exception("back crashed: %s", e)
                self._finish_nav()
        except Exception as e:
            logger.warning("back caused an unexpected bug: %s", e)

    def _seconds_from_timespan(self, value) -> float:
        try:
            if value is None:
                return 0.0
            if hasattr(value, "total_seconds"):
                try:
                    return max(0.0, float(value.total_seconds()))
                except Exception:
                    pass

            if hasattr(value, "duration"):
                try:
                    return max(0.0, float(value.duration / 10_000_000))
                except Exception:
                    pass

            return 0.0
        except Exception as e:
            logger.warning("_seconds_from_timespan caused an unexpected bug: %s", e)

    def get_time(self):
        try:
            try:
                full_time = self._seconds_from_timespan(self._session.natural_duration)
                current_time = self._seconds_from_timespan(self._session.position)
                return full_time, current_time
            except Exception as e:
                logger.warning("🟡 get_time failed: %s", e)
                return 0, 0
        except Exception as e:
            logger.warning("get_time caused an unexpected bug: %s", e)

    def set_time(self, seconds: float):
        try:
            if seconds < 0:
                seconds = 0
            try:
                self._session.position = timedelta(seconds=float(seconds))
            except Exception as e:
                logger.warning("🟡 Seek failed: %s", e)
        except Exception as e:
            logger.warning("set_time caused an unexpected bug: %s", e)

    def _commit_current_to_timeline(self, index: int):
        try:
            if self.play_order_pos < len(self.play_order) - 1:
                self.play_order = self.play_order[:self.play_order_pos + 1]

            self.play_order.append(index)
            self.play_order_pos = len(self.play_order) - 1
        except Exception as e:
            logger.warning("_commit_current_to_timeline caused an unexpected bug: %s", e)

    def _pick_shuffle_song(self, old_index: int, songs: list[str]) -> int:
        try:
            if len(songs) == 1:
                return 0

            blocked = set(self.recent_shuffle)
            blocked.add(old_index)

            choices = [i for i in range(len(songs)) if i not in blocked]
            if not choices:
                choices = [i for i in range(len(songs)) if i != old_index]
            if not choices:
                choices = [old_index]

            return random.choice(choices)
        except Exception as e:
            logger.warning("_pick_shuffle_song caused an unexpected bug: %s", e)

    def _on_playback_state_changed(self, sender, args):
        try:
            try:
                state = int(self._session.playback_state)
                self.playbackStateChanged.emit(state)
            except Exception as e:
                logger.warning("🟡 Playback state event failed: %s", e)
        except Exception as e:
            logger.warning("_on_playback_state_changed caused an unexpected bug: %s", e)

    def _update_windows_popup(self, title, artist, cover_path):
        try:
            try:
                updater = self._smtc.display_updater
                updater.type = MediaPlaybackType.MUSIC
                updater.music_properties.title = title or "Unknown Title"
                updater.music_properties.artist = artist or "Unknown Artist"

                if cover_path and os.path.exists(cover_path):
                    try:
                        import asyncio
                        updater.thumbnail = asyncio.run(self._create_thumbnail_ref(cover_path))
                    except Exception as e:
                        logger.warning("🟡 Thumbnail load failed: %s", e)
                        updater.thumbnail = None
                else:
                    updater.thumbnail = None

                updater.update()
            except Exception as e:
                logger.warning("🟡 SMTC update failed: %s", e)
        except Exception as e:
            logger.warning("_update_windows_popup caused an unexpected bug: %s", e)

    def _update_smtc_playback_status(self):
        try:
            try:
                state = self._session.playback_state

                if state == MediaPlaybackState.PLAYING:
                    self._smtc.playback_status = MediaPlaybackStatus.PLAYING
                elif state == MediaPlaybackState.PAUSED:
                    self._smtc.playback_status = MediaPlaybackStatus.PAUSED
                else:
                    self._smtc.playback_status = MediaPlaybackStatus.CLOSED
            except Exception as e:
                logger.warning("🟡 SMTC playback status update failed: %s", e)
        except Exception as e:
            logger.warning("_update_smtc_playback_status caused an unexpected bug: %s", e)

    def _on_media_ended(self, sender, args):
        try:
            try:
                self.songEnded.emit()
            except Exception as e:
                logger.warning("🟡 Media ended event failed: %s", e)
        except Exception as e:
            logger.warning("_on_media_ended caused an unexpected bug: %s", e)

    def _on_media_failed(self, sender, args):
        try:
            try:
                self._smtc.playback_status = MediaPlaybackStatus.CLOSED

                logger.error("🔴 Media failed to play")
                logger.info("Current song: %s", self.get_current_song())

                for name in dir(args):
                    if name.startswith("_"):
                        continue
                    try:
                        value = getattr(args, name)
                        if not callable(value):
                            logger.info(f"{name}: {value}")
                    except Exception as ex:
                        logger.warning(f"{name}: <error reading: {ex}>")

            except Exception as e:
                logger.warning("🟡 Media failed event failed: %s", e)
        except Exception as e:
            logger.warning("_on_media_failed caused an unexpected bug: %s", e)

    def _on_media_opened(self, sender, args):
        try:
            try:
                self.mediaOpenedQt.emit()
            except Exception as e:
                logger.warning("🟡 Media opened event failed: %s", e)
        except Exception as e:
            logger.warning("_on_media_opened caused an unexpected bug: %s", e)

    def _update_history_limit(self):
        try:
            songs = self.player.get_song_list()
            size = len(songs)

            if size <= 0:
                new_limit = 50
            else:
                new_limit = max(3, min(50, size // 8))
            self.history = deque(list(self.history), maxlen=new_limit)
            self.forward_history = deque(list(self.forward_history), maxlen=new_limit)
        except Exception as e:
            logger.warning("_update_history_limit caused an unexpected bug: %s", e)

    async def _create_thumbnail_ref(self, cover_path: str):
        try:
            file = await StorageFile.get_file_from_path_async(str(Path(cover_path).resolve()))
            return RandomAccessStreamReference.create_from_file(file)
        except Exception as e:
            logger.warning("_create_thumbnail_ref caused an unexpected bug: %s", e)



class Player(QWidget):
    def __init__(self) -> None:
        try:
            print("Starting...")
            super().__init__()
            os.system('cls')
            self.engine = Audio(self)
            self.current_theme = DEFAULT_THEME.copy()
            self.theme = ThemeThing(self)
            self.songs: Dict[str, Dict] = {}
            self._loading_ui = False
            self._autosave_timer = QTimer(self)
            self._autosave_timer.setSingleShot(True)
            self._autosave_timer.setInterval(250)
            self._autosave_timer.timeout.connect(self._save_current_preset_silent)
            self.cover_path = BLANK_PATH
            self.current_song = self.engine.preset.current_song
            self._console_enabled = False
            self._old_stdout = sys.stdout
            self._old_stderr = sys.stderr
            self._old_stdin = sys.stdin
            console_close_bridge.closed.connect(self._console_closed_by_user)
            self._lyrics_bridge = LyricsResultBridge()
            self._lyrics_bridge.loaded.connect(self._lyrics_loaded)
            self._lyrics_bridge.failed.connect(self._lyrics_failed)
            self._lyrics_bridge.status.connect(self._lyrics_status_changed)
            self._lyrics_load_timer = QTimer(self)
            self._lyrics_load_timer.setSingleShot(True)
            self._lyrics_load_timer.timeout.connect(self._load_lyrics_for_current_song_now)
            self.tab_order = [
                "Player",
                "Lyrics",
                "Queue",
                "Library",
                "Settings"
            ]
            self._row_data_cache = {}
            self._row_pixmap_cache = {}

            self.setWindowTitle(f"Yet Another Music Player — {PROFILE_NAME}")
            self.setWindowIcon(QIcon(ICON_PATH))
            self.setMinimumSize(1120, 720)
            self.setAcceptDrops(True)

            root = QVBoxLayout(self)
            root.setContentsMargins(20, 20, 20, 20)
            root.setSpacing(14)

            self.tabs = QTabWidget()
            self.tabs.tabBar().setMovable(True)
            self.tabs.tabBar().tabMoved.connect(self._tabs_moved)
            root.addWidget(self.tabs)

            self.properties_tab = QWidget()
            properties_layout = QVBoxLayout(self.properties_tab)
            properties_layout.setContentsMargins(16, 16, 16, 16)
            properties_layout.setSpacing(14)

            self.library_tab = QWidget()
            library_tab_layout = QVBoxLayout(self.library_tab)
            library_tab_layout.setContentsMargins(16, 16, 16, 16)
            library_tab_layout.setSpacing(14)

            self.lyrics_tab = QWidget()
            lyrics_layout = QVBoxLayout(self.lyrics_tab)
            lyrics_layout.setContentsMargins(16, 16, 16, 16)
            lyrics_layout.setSpacing(14)

            self.settings_tab = QWidget()
            settings_root_layout = QVBoxLayout(self.settings_tab)
            settings_root_layout.setContentsMargins(0, 0, 0, 0)
            settings_scroll = QScrollArea()
            settings_scroll.setWidgetResizable(True)
            settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            settings_container = QWidget()
            settings_layout = QVBoxLayout(settings_container)
            settings_layout.setContentsMargins(16, 16, 16, 16)
            settings_layout.setSpacing(14)
            settings_scroll.setWidget(settings_container)
            settings_root_layout.addWidget(settings_scroll)

            self.queue_tab = QWidget()
            queue_layout = QVBoxLayout(self.queue_tab)
            queue_layout.setContentsMargins(16, 16, 16, 16)
            queue_layout.setSpacing(14)

            self.tabs.addTab(self.properties_tab, "Player")
            self.tabs.addTab(self.lyrics_tab, "Lyrics")
            self.tabs.addTab(self.queue_tab, "Queue")
            self.tabs.addTab(self.library_tab, "Library")
            self.tabs.addTab(self.settings_tab, "Settings")

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
            self.lyrics_window_cb = QCheckBox("Lyrics")
            self.lyrics_window_on_top_cb = QCheckBox("Always on Top")
            self.floating_lyrics_cb = QCheckBox("Floating Lyrics")
            self.floating_lyrics_on_top_cb = QCheckBox("Always on Top")
            self.romaji_cb = QCheckBox("Romaji")
            self.translated_cb = QCheckBox("Translation")

            self.settings_mute_cb = QCheckBox("Mute")
            self.settings_shuffle_cb = QCheckBox("Shuffle")
            self.settings_repeat_cb = QCheckBox("Repeat")
            self.settings_lyrics_window_cb = QCheckBox("Lyrics")
            self.settings_lyrics_window_on_top_cb = QCheckBox("Always on Top")
            self.settings_floating_lyrics_cb = QCheckBox("Floating Lyrics")
            self.settings_floating_lyrics_on_top_cb = QCheckBox("Always on Top")
            self.settings_romaji_cb = QCheckBox("Romaji")
            self.settings_translated_cb = QCheckBox("Translation")
        
            self.settings_normalize_audio_cb = QCheckBox("Normalize Audio")
            self.settings_online_lyrics_cb = QCheckBox("Online Lyrics")
            self.settings_download_lyrics_cb = QCheckBox("Download Lyrics")
            self.settings_MUSIXMATCH_USER_TOKEN_text = QLineEdit("Paste your MUSIXMATCH user token here")

            self.edit_theme_font_size_btn = QPushButton("Edit Font Size")
            self.reset_selected_theme_font_size_btn = QPushButton("Reset Font Size")

            self.volume_slider = JumpSlider(Qt.Horizontal)
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(int(self.engine.preset.volume))

            self.volume_value_label = QLabel(f"{int(self.engine.preset.volume)}%")
            self.volume_value_label.setObjectName("ValuePill")
            self.volume_value_label.setMinimumWidth(52)
            self.volume_value_label.setAlignment(Qt.AlignCenter)

            self.position_slider = JumpSlider(Qt.Horizontal)
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
            self.now_playing_artist.setObjectName("SongArtist")

            self.song_list = LibraryListWidget()
            self.song_list.setObjectName("SongList")
            self.song_list.setIconSize(QSize(52, 52))
            self.song_list.setMinimumHeight(260)
            self.song_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.song_list.deletePressed.connect(self._delete_selected_songs)

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

            options_layout = QVBoxLayout(options_group)
            options_layout.setSpacing(10)

            options_layout_1 = QHBoxLayout()
            options_layout_1.addWidget(self.shuffle_cb)
            options_layout_1.addWidget(self.repeat_cb)
            options_layout_1.addWidget(self.mute_cb)
            options_layout_1.addStretch()

            options_layout_2 = QHBoxLayout()
            options_layout_2.addWidget(self.lyrics_window_cb)
            options_layout_2.addWidget(self.lyrics_window_on_top_cb)
            options_layout_2.addWidget(self.floating_lyrics_cb)
            options_layout_2.addWidget(self.floating_lyrics_on_top_cb)
            options_layout_2.addStretch()

            options_layout_3 = QHBoxLayout()
            options_layout_3.addWidget(self.romaji_cb)
            options_layout_3.addWidget(self.translated_cb)
            options_layout_3.addStretch()

            options_layout.addLayout(options_layout_1)
            options_layout.addLayout(options_layout_2)
            options_layout.addLayout(options_layout_3)

            info_col.addWidget(volume_group)
            info_col.addWidget(controls_group)
            info_col.addWidget(options_group)
            info_col.addStretch(2)

            now_playing_layout.addLayout(cover_col, 0)
            now_playing_layout.addLayout(info_col, 1)

            properties_layout.addWidget(now_playing_group)
            properties_layout.addStretch(1)

            # =====================================================
            #                    LYRICS TAB
            # =====================================================

            self.lyrics_list = QListWidget()
            self.lyrics_list.setObjectName("LyricsList")
            self.lyrics_list.setSelectionMode(QAbstractItemView.NoSelection)
            self.lyrics_list.setFocusPolicy(Qt.NoFocus)
            self.lyrics_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

            self.sync_lyrics = True
            self._lyrics_auto_scrolling = False
            self._lyrics_user_scrolling = False

            self._lyrics_scroll_resume_timer = QTimer(self)
            self._lyrics_scroll_resume_timer.setSingleShot(True)
            self._lyrics_scroll_resume_timer.timeout.connect(self._resume_sync_scroll_after_user_scroll)

            self.lyrics_list.viewport().installEventFilter(self)
            self.lyrics_list.verticalScrollBar().installEventFilter(self)

            self.lyrics_status = QLabel("No lyrics Found")
            self.lyrics_status.setObjectName("MutedLabel")

            lyrics_layout_1 = QVBoxLayout()
            lyrics_layout_1.addWidget(self.lyrics_status, alignment=Qt.AlignLeft)
            lyrics_layout_1.addStretch()

            self.current_lyrics_data = []
            self.current_lyrics_index = -1
            self.current_lyrics_timed = False

            lyrics_group = QGroupBox("Lyrics")
            lyrics_group_layout = QVBoxLayout(lyrics_group)
            lyrics_group_layout.addLayout(lyrics_layout_1)
            lyrics_group_layout.addWidget(self.lyrics_list, 1)

            lyrics_layout.addWidget(lyrics_group, 1)

            # =====================================================
            #                    QUEUE TAB
            # =====================================================
            queue_group = QGroupBox("Queue")
            queue_group_layout = QVBoxLayout(queue_group)

            self.queue_list = QueueListWidget(self)
            self.queue_list.setObjectName("QueueList")
            self.queue_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

            queue_buttons = QHBoxLayout()
            self.add_to_queue_btn = QPushButton("Refresh Queue")
            self.remove_from_queue_btn = QPushButton("Remove Selected")

            queue_buttons.addWidget(self.add_to_queue_btn)
            queue_buttons.addWidget(self.remove_from_queue_btn)
            queue_buttons.addStretch()

            queue_hint = QLabel("Queue plays before shuffle/normal next.")
            queue_hint.setObjectName("MutedLabel")

            queue_group_layout.addWidget(queue_hint)
            queue_group_layout.addWidget(self.queue_list, 1)
            queue_group_layout.addLayout(queue_buttons)

            queue_layout.addWidget(queue_group, 1)

            # =====================================================
            #                    LIBRARY TAB
            # =====================================================
            library_group = QGroupBox("Songs")
            library_group_layout = QVBoxLayout(library_group)

            library_hint = QLabel("Drop supported files anywhere into the window")
            library_hint.setObjectName("MutedLabel")

            library_group_layout.addWidget(library_hint)
            library_group_layout.addWidget(self.song_list, 1)

            library_tab_layout.addWidget(library_group, 1)

            # =====================================================
            #                      Settings
            # =====================================================


            settings_group = QGroupBox("Settings")
            settings_boxed_layout = QVBoxLayout(settings_group)

            # =========================
            # Console Settings
            # =========================

            settings_console_group = QGroupBox("Console Settings")
            settings_console_layout = QVBoxLayout(settings_console_group)
            settings_console_layout_row_1 = QHBoxLayout()
            self.show_console_cb = QCheckBox("Show Console")
            self.logging_level_drop = QComboBox()
            self.logging_level_drop.addItems([
                "Debug",
                "Info",
                "Warning",
                "Error"
            ])
            self.logging_level_drop.setCurrentIndex(self.engine.preset.logging_level)

            settings_console_layout_row_1.addWidget(self.show_console_cb)
            settings_console_layout_row_1.addWidget(self.logging_level_drop)
            settings_console_layout.addLayout(settings_console_layout_row_1)
        
            # =========================
            # PRESET SETTINGS
            # =========================

            settings_preset_group = QGroupBox("Presets")
            settings_preset_layout = QVBoxLayout(settings_preset_group)
            settings_preset_layout.setSpacing(10)

            preset_hint = QLabel(f"Current preset: {PROFILE_NAME}")
            preset_hint.setObjectName("MutedLabel")
            self.preset_status_label = preset_hint

            preset_buttons_row_1 = QHBoxLayout()
            self.save_preset_btn = QPushButton("Save Current")
            self.save_as_new_preset_btn = QPushButton("Save as New")

            preset_buttons_row_1.addWidget(self.save_preset_btn)
            preset_buttons_row_1.addWidget(self.save_as_new_preset_btn)

            preset_buttons_row_2 = QHBoxLayout()
            self.load_preset_btn = QPushButton("Load Preset")
            self.export_preset_btn = QPushButton("Set Current as Default")

            preset_buttons_row_2.addWidget(self.load_preset_btn)
            preset_buttons_row_2.addWidget(self.export_preset_btn)

            self.preset_name = QLineEdit()
            self.preset_name.setText(PROFILE_NAME)
            self.preset_name.hide()

            self.preset_combo = QComboBox()
            self.preset_combo.hide()

            settings_preset_layout.addWidget(preset_hint)
            settings_preset_layout.addLayout(preset_buttons_row_1)
            settings_preset_layout.addLayout(preset_buttons_row_2)
            settings_preset_layout.addWidget(self.preset_name)
            settings_preset_layout.addWidget(self.preset_combo)

            # =========================
            # PLAYER SETTINGS
            # =========================

            settings_player_group = QGroupBox("Player Settings")
            settings_player_layout = QVBoxLayout(settings_player_group)
            settings_player_layout.setSpacing(10)

            settings_player_layout_1 = QHBoxLayout()
            settings_player_layout_1.addWidget(self.settings_shuffle_cb)
            settings_player_layout_1.addWidget(self.settings_repeat_cb)
            settings_player_layout_1.addWidget(self.settings_mute_cb)
            settings_player_layout_1.addWidget(self.settings_normalize_audio_cb)
            settings_player_layout_1.addStretch()

            settings_player_layout_2 = QHBoxLayout()
            settings_player_layout_2.addWidget(self.settings_lyrics_window_cb)
            settings_player_layout_2.addWidget(self.settings_lyrics_window_on_top_cb)
            settings_player_layout_2.addWidget(self.settings_floating_lyrics_cb)
            settings_player_layout_2.addWidget(self.settings_floating_lyrics_on_top_cb)
            settings_player_layout_2.addStretch()

            settings_player_layout_3 = QHBoxLayout()
            settings_player_layout_3.addWidget(self.settings_romaji_cb)
            settings_player_layout_3.addWidget(self.settings_translated_cb)
            settings_player_layout_3.addStretch()

            settings_player_layout.addLayout(settings_player_layout_1)
            settings_player_layout.addLayout(settings_player_layout_2)
            settings_player_layout.addLayout(settings_player_layout_3)

            # =========================
            # LYRICS SETTINGS
            # =========================


            settings_lyrics_group = QGroupBox("Lyrics Settings")
            settings_lyrics_layout = QVBoxLayout(settings_lyrics_group)

            settings_lyrics_layout_1 = QHBoxLayout()
            settings_lyrics_layout_1.addWidget(self.settings_online_lyrics_cb)
            settings_lyrics_layout_1.addWidget(self.settings_download_lyrics_cb)
            settings_lyrics_layout_1.addStretch()

            settings_lyrics_layout_2 = QHBoxLayout()
            settings_lyrics_layout_2.addWidget(self.settings_MUSIXMATCH_USER_TOKEN_text)
            self.settings_MUSIXMATCH_USER_TOKEN_text.setPlaceholderText("MUSIXMATCH USER TOKEN")
            settings_lyrics_layout_2.addStretch()

            settings_lyrics_layout.addLayout(settings_lyrics_layout_1)
            settings_lyrics_layout.addLayout(settings_lyrics_layout_2)

            # =========================
            # QUEUE SETTINGS
            # =========================738

            settings_queue_group = QGroupBox("Queue Settings")
            settings_queue_layout = QVBoxLayout(settings_queue_group)

            settings_queue_layout_1 = QHBoxLayout()

            settings_queue_layout.addLayout(settings_queue_layout_1)

            # =========================
            # LIBRARY SETTINGS
            # =========================

            settings_library_group = QGroupBox("Library Settings")
            settings_library_layout = QHBoxLayout(settings_library_group)

            self.library_sort_drop = QComboBox()
            self.library_sort_drop.addItems([
                "File Name",
                "Artist - Title",
                "Title - Artist",
            ])

            self.library_images_cb = QCheckBox("Show Images")

            settings_library_layout.addWidget(self.library_sort_drop, 1)
            settings_library_layout.addWidget(self.library_images_cb)
            settings_library_layout.addStretch()

            # =========================
            # THEME SETTINGS
            # =========================

            settings_theme_group = QGroupBox("Theme")
            settings_theme_layout = QVBoxLayout(settings_theme_group)

            self.theme_color_drop = QComboBox()
            self.theme_color_drop.addItems([
                "Background",
                "Text",
                "Muted Text",
                "Panel",
                "Active Panel",
                "Border",
                "Border Hover",
                "Selected Border",
                "Disabled Border",
                "Button Hover",
                "Button Pressed",
                "Accent",
                "Accent Hover",
                "Selection",
                "Slider Background",
                "Disabled Text",
            ])

            self.theme_color_keys = [
                "bg",
                "text",
                "muted_text",
                "panel",
                "panel_active",
                "border",
                "border_hover",
                "border_selected",
                "border_disabled",
                "button_hover",
                "button_pressed",
                "accent",
                "accent_hover",
                "selection",
                "slider_bg",
                "disabled_text",
            ]

            self.edit_theme_color_btn = QPushButton("Edit Color")
            self.reset_selected_theme_btn = QPushButton("Reset Selected")
            self.reset_all_theme_btn = QPushButton("Reset All")

            self.theme_font_size_drop = QComboBox()
            self.theme_font_size_drop.addItems([
                "Title Font",
                "Artist Font",
                "Lyrics Font",
                "Normal Text Font",
            ])

            self.theme_font_size_keys = [
                "title_font_size",
                "artist_font_size",
                "lyrics_font_size",
                "normal_font_size",
            ]

            self.theme_font_size_drop = QComboBox()
            self.theme_font_size_drop.addItems([
                "Title Font",
                "Artist Font",
                "Lyrics Font",
                "Normal Text Font",
            ])

            self.theme_font_size_keys = [
                "title_font_size",
                "artist_font_size",
                "lyrics_font_size",
                "normal_font_size",
            ]

            settings_theme_layout_1 = QHBoxLayout()
            settings_theme_layout_1.addWidget(self.theme_color_drop, 1)
            settings_theme_layout_1.addWidget(self.edit_theme_color_btn)
            settings_theme_layout_1.addWidget(self.reset_selected_theme_btn)
            settings_theme_layout_1.addWidget(self.reset_all_theme_btn)

            settings_theme_layout_2 = QHBoxLayout()
            settings_theme_layout_2.addWidget(self.theme_font_size_drop, 1)
            settings_theme_layout_2.addWidget(self.edit_theme_font_size_btn)
            settings_theme_layout_2.addWidget(self.reset_selected_theme_font_size_btn)

            settings_theme_layout.addLayout(settings_theme_layout_1)
            settings_theme_layout.addLayout(settings_theme_layout_2)

            # =========================
            # WIDGETS ADDED
            # =========================

            settings_boxed_layout.addWidget(settings_console_group)
            settings_boxed_layout.addWidget(settings_preset_group)
            settings_boxed_layout.addWidget(settings_player_group)
            settings_boxed_layout.addWidget(settings_lyrics_group)
            settings_boxed_layout.addWidget(settings_queue_group)
            settings_boxed_layout.addWidget(settings_library_group)
            settings_boxed_layout.addWidget(settings_theme_group)

            settings_layout.addWidget(settings_group)
            settings_layout.addStretch()

            # =====================================================
            #              SETTINGS CHECKBOX SYNC
            # =====================================================

            def connect_pair(main_cb, settings_cb, callback):
                try:
                    def changed(state):
                        try:
                            checked = state == Qt.CheckState.Checked.value

                            main_cb.blockSignals(True)
                            settings_cb.blockSignals(True)

                            main_cb.setChecked(checked)
                            settings_cb.setChecked(checked)

                            main_cb.blockSignals(False)
                            settings_cb.blockSignals(False)

                            callback(checked)
                            self._apply_ui_to_engine()
                        except Exception as e:
                            logger.warning("changed caused an unexpected bug: %s", e)

                    main_cb.stateChanged.connect(changed)
                    settings_cb.stateChanged.connect(changed)
                except Exception as e:
                    logger.warning("connect_pair caused an unexpected bug: %s", e)

            def connect_the_pairs_ig():
                try:
                    connect_pair(self.shuffle_cb, self.settings_shuffle_cb, self.engine.set_shuffle)
                    connect_pair(self.repeat_cb, self.settings_repeat_cb, self.engine.set_repeat)
                    connect_pair(self.mute_cb, self.settings_mute_cb, self.engine.set_muted)
                    connect_pair(self.lyrics_window_cb,self.settings_lyrics_window_cb,self.engine.lyrics.set_lyrics)
                    connect_pair(self.lyrics_window_on_top_cb, self.settings_lyrics_window_on_top_cb, self.engine.lyrics.set_lyrics_on_top)
                    connect_pair(self.floating_lyrics_cb, self.settings_floating_lyrics_cb, self.engine.lyrics.set_floating)
                    connect_pair(self.floating_lyrics_on_top_cb, self.settings_floating_lyrics_on_top_cb, self.engine.lyrics.set_floating_on_top)
                    connect_pair(self.romaji_cb, self.settings_romaji_cb, lambda checked: self._on_romaji_changed())
                    connect_pair(self.translated_cb, self.settings_translated_cb, lambda checked: self._on_translated_changed())
                except Exception as e:
                    logger.warning("connect_the_pairs_ig caused an unexpected bug: %s", e)
            connect_the_pairs_ig()

            # =====================================================
            #                    CONNECTIONS
            # =====================================================
            self.play_btn.clicked.connect(self.engine.play)
            self.stop_btn.clicked.connect(self.engine.stop)
            self.back_btn.clicked.connect(self.engine.back)
            self.pause_btn.clicked.connect(self.engine.pause)
            self.next_btn.clicked.connect(self.engine.next)

            self.mute_cb.setChecked(self.engine.preset.muted)
            self.shuffle_cb.setChecked(self.engine.preset.shuffle)
            self.repeat_cb.setChecked(self.engine.preset.repeat)
            self.lyrics_window_cb.setChecked(self.engine.preset.lyrics_window)
            self.lyrics_window_on_top_cb.setChecked(self.engine.preset.lyrics_window_on_top)
            self.floating_lyrics_cb.setChecked(self.engine.preset.floating_lyrics)
            self.floating_lyrics_on_top_cb.setChecked(self.engine.preset.floating_lyrics_on_top)
            self.romaji_cb.setChecked(self.engine.preset.romaji)
            self.translated_cb.setChecked(self.engine.preset.translated)

            self.volume_slider.valueChanged.connect(self.engine.volume)
            self.volume_slider.valueChanged.connect(self._update_volume_label)

            self._refresh_preset_dropdown()

            self.lyrics_list.itemDoubleClicked.connect(self._lyric_item_double_clicked)
            self.lyrics_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.lyrics_list.customContextMenuRequested.connect(self._lyrics_context_menu)

            self.mute_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.lyrics_window_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.lyrics_window_on_top_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.floating_lyrics_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.floating_lyrics_on_top_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.romaji_cb.stateChanged.connect(self._on_romaji_changed)
            self.translated_cb.stateChanged.connect(self._on_translated_changed)
            self.shuffle_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.repeat_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.volume_slider.valueChanged.connect(self._apply_ui_to_engine)
            self.position_slider.sliderPressed.connect(self._position_slider_pressed)
            self.position_slider.sliderMoved.connect(self._position_slider_moved)
            self.position_slider.sliderReleased.connect(self._position_slider_released)

            self.add_to_queue_btn.clicked.connect(self._add_selected_to_queue)
            self.remove_from_queue_btn.clicked.connect(self._remove_selected_from_queue)
            self.queue_list.deletePressed.connect(self._remove_selected_from_queue)
            self.song_list.itemDoubleClicked.connect(self._library_item_double_clicked)
            self.queue_list.itemDoubleClicked.connect(self._queue_item_double_clicked)

            self.save_preset_btn.clicked.connect(self._save_current_preset_button)
            self.save_as_new_preset_btn.clicked.connect(self._save_as_new_preset_dialog)
            self.load_preset_btn.clicked.connect(self._load_preset_dialog)
            self.export_preset_btn.clicked.connect(self._export_current_preset)
            self.show_console_cb.stateChanged.connect(lambda state: self.toggle_console(state == Qt.CheckState.Checked.value))
            self.show_console_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.logging_level_drop.currentIndexChanged.connect(self._set_logging_level)
            self.logging_level_drop.currentIndexChanged.connect(self._apply_ui_to_engine)
            # Console

            # Presets

            # Player
            self.settings_mute_cb.setChecked(self.engine.preset.muted)
            self.settings_shuffle_cb.setChecked(self.engine.preset.shuffle)
            self.settings_repeat_cb.setChecked(self.engine.preset.repeat)
            self.settings_lyrics_window_cb.setChecked(self.engine.preset.lyrics_window)
            self.settings_lyrics_window_on_top_cb.setChecked(self.engine.preset.lyrics_window_on_top)
            self.settings_floating_lyrics_cb.setChecked(self.engine.preset.floating_lyrics)
            self.settings_floating_lyrics_on_top_cb.setChecked(self.engine.preset.floating_lyrics_on_top)
            self.settings_romaji_cb.setChecked(self.engine.preset.romaji)
            self.settings_translated_cb.setChecked(self.engine.preset.translated)
            self.settings_normalize_audio_cb.setChecked(self.engine.preset.normalize_audio)
            self.settings_normalize_audio_cb.stateChanged.connect(self._apply_ui_to_engine)
            # Lyrics
            self.settings_online_lyrics_cb.setChecked(self.engine.preset.online_lyrics)
            self.settings_online_lyrics_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.settings_download_lyrics_cb.setChecked(self.engine.preset.download_lyrics)
            self.settings_download_lyrics_cb.stateChanged.connect(self._apply_ui_to_engine)
            self.settings_MUSIXMATCH_USER_TOKEN_text.setText(self.engine.preset.MUSIXMATCH_USER_TOKEN)
            self.settings_MUSIXMATCH_USER_TOKEN_text.textChanged.connect(self._apply_ui_to_engine)
            # Queue

            # Library
            self.library_sort_drop.currentIndexChanged.connect(self._library_settings_changed)
            self.library_images_cb.stateChanged.connect(self._library_settings_changed)
            # Theme
            self.edit_theme_color_btn.clicked.connect(self._edit_selected_theme_color)
            self.reset_selected_theme_btn.clicked.connect(self._reset_selected_theme_color)
            self.reset_all_theme_btn.clicked.connect(self._reset_all_theme)
            self.edit_theme_font_size_btn.clicked.connect(self._edit_selected_theme_font_size)
            self.reset_selected_theme_font_size_btn.clicked.connect(self._reset_selected_theme_font_size)

            self.engine.songEnded.connect(self._handle_song_end)
            for font_file in FONT_DIR.glob("*.ttf"):
                logger.debug(f"🟣 Loading: {font_file.name}")
                font_id = QFontDatabase.addApplicationFont(str(font_file))
                if font_id == -1:
                    logger.debug(f"🟣🟡 Failed: {font_file.name}")
                else:
                    text = QFontDatabase.applicationFontFamilies(font_id)
                    logger.debug(f"🟣 Loaded: {font_file.name} %s", text)
            apply_theme(QApplication.instance(), {"theme": self.current_theme})
        except Exception as e:
            logger.warning("__init__ caused an unexpected bug: %s", e)

    def _on_assets_downloaded(self):
            try:
                for font_file in FONT_DIR.glob("*.ttf"):
                    font_id = QFontDatabase.addApplicationFont(str(font_file))
                    if font_id == -1:
                        logger.debug(f"🟣🟡 Failed: {font_file.name}")
                    else:
                        logger.debug(f"🟣 Loaded: {font_file.name}")

                if os.path.exists(ICON_PATH):
                    self.setWindowIcon(QIcon(ICON_PATH))

                if os.path.exists(BLANK_PATH) and self.cover_path == BLANK_PATH:
                    self.pixmap = QPixmap(self.cover_path)
                    self.label.setPixmap(self.pixmap)

                apply_theme(QApplication.instance(), {"theme": self.current_theme})
            except Exception as e:
                logger.warning("_on_assets_downloaded caused an unexpected bug: %s", e)

    def _set_sync_scroll(self, value: bool):
        try:
            self.sync_lyrics = bool(value)
            self._lyrics_user_scrolling = False
            self._lyrics_scroll_resume_timer.stop()

            if self.sync_lyrics and 0 <= self.current_lyrics_index < self.lyrics_list.count():
                item = self.lyrics_list.item(self.current_lyrics_index)
                if item is not None:
                    self.smooth_scroll_to_item(item)

        except Exception as e:
            logger.warning("_set_sync_scroll caused an unexpected bug: %s", e)

    def _pause_sync_scroll_from_user_scroll(self):
        try:
            if self._lyrics_auto_scrolling:
                return

            self._lyrics_user_scrolling = True
            self.sync_lyrics = False

            self._lyrics_scroll_resume_timer.start(2500)

        except Exception as e:
            logger.warning("_pause_sync_scroll_from_user_scroll caused an unexpected bug: %s", e)

    def _resume_sync_scroll_after_user_scroll(self):
        try:
            self._lyrics_user_scrolling = False
            self.sync_lyrics = True

            if 0 <= self.current_lyrics_index < self.lyrics_list.count():
                item = self.lyrics_list.item(self.current_lyrics_index)
                if item is not None:
                    self.smooth_scroll_to_item(item)

        except Exception as e:
            logger.warning("_resume_sync_scroll_after_user_scroll caused an unexpected bug: %s", e)

    def eventFilter(self, obj, event):
        try:
            if obj in (self.lyrics_list.viewport(), self.lyrics_list.verticalScrollBar()):
                event_type = event.type()

                if event_type in (
                    QEvent.Type.Wheel,
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseMove,
                    QEvent.Type.KeyPress,
                ):
                    self._pause_sync_scroll_from_user_scroll()

            return super().eventFilter(obj, event)

        except Exception as e:
            logger.warning("eventFilter caused an unexpected bug: %s", e)
            return False

    def _get_row_data_cached(self, index: int):
        try:
            data = self.songs.get(str(index))
            path = data.get("path") if data else None

            if not path or not os.path.isfile(path):
                return "Unknown Artist", f"Missing song #{index}", BLANK_PATH

            if not hasattr(self, "_row_data_cache"):
                self._row_data_cache = {}

            cached = self._row_data_cache.get(path)
            if cached:
                return cached

            artist, title, cover_path = self.engine.get_data_for_path(path)

            result = (
                artist or "Unknown Artist",
                title or os.path.basename(path),
                cover_path if cover_path and os.path.exists(cover_path) else BLANK_PATH
            )

            self._row_data_cache[path] = result
            return result
        except Exception as e:
            logger.warning("_get_row_data_cached caused an unexpected bug: %s", e)

    def _get_row_pixmap_cached(self, cover_path: str):
            try:
                cover_path = cover_path if cover_path and os.path.exists(cover_path) else BLANK_PATH

                if not hasattr(self, "_row_pixmap_cache"):
                    self._row_pixmap_cache = {}

                cached = self._row_pixmap_cache.get(cover_path)
                if cached is not None and not cached.isNull():
                    return cached

                pixmap = QPixmap(cover_path)

                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        52, 52,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    if pixmap.width() != 52 or pixmap.height() != 52:
                        x = max(0, (pixmap.width() - 52) // 2)
                        y = max(0, (pixmap.height() - 52) // 2)
                        pixmap = pixmap.copy(x, y, 52, 52)

                self._row_pixmap_cache[cover_path] = pixmap
                return pixmap
            except Exception as e:
                logger.warning("_get_row_pixmap_cached caused an unexpected bug: %s", e)

    def _set_startup_loading_ui(self):
        try:
            if self.now_playing_title.text() != None:
                return
            self.now_playing_title.setText("Loading...")
            self.now_playing_artist.setText("Loading...")
            self.setWindowTitle("Yet Another Music Player — Loading...")
        except Exception as e:
            logger.warning("_set_startup_loading_ui caused an unexpected bug: %s", e)

    def _title_font(self, point_size: int | None = None, bold: bool = False) -> QFont:
        try:
            font = QFont(self._title_font_family())

            if point_size is None:
                point_size = self._theme_int(
                    "normal_font_size",
                    int(DEFAULT_THEME["normal_font_size"])
                )

            font.setPointSize(point_size)
            font.setBold(bold)
            return font
        except Exception as e:
            logger.warning("_title_font caused an unexpected bug: %s", e)

    def _theme_int(self, key: str, default: int) -> int:
        try:
            if not hasattr(self, "current_theme") or self.current_theme is None:
                return default

            try:
                return int(self.current_theme.get(key, default))
            except Exception:
                return default
        except Exception as e:
            logger.warning("_theme_int caused an unexpected bug: %s", e)

    def _reset_selected_theme_font_size(self):
        try:
            index = self.theme_font_size_drop.currentIndex()
            if index < 0 or index >= len(self.theme_font_size_keys):
                return

            key = self.theme_font_size_keys[index]
            if key not in DEFAULT_THEME:
                return

            set_theme_value(self.theme, key, DEFAULT_THEME[key])
        except Exception as e:
            logger.warning("_reset_selected_theme_font_size caused an unexpected bug: %s", e)

    def _edit_selected_theme_font_size(self):
        try:
            index = self.theme_font_size_drop.currentIndex()
            if index < 0 or index >= len(self.theme_font_size_keys):
                return

            key = self.theme_font_size_keys[index]
            current = self._theme_int(key, int(DEFAULT_THEME.get(key, 13)))

            value, ok = QInputDialog.getInt(
                self,
                "Edit Font Size",
                f"{self.theme_font_size_drop.currentText()} size:",
                current,
                6,
                72,
                1
            )

            if ok:
                set_theme_value(self.theme, key, int(value))
        except Exception as e:
            logger.warning("_edit_selected_theme_font_size caused an unexpected bug: %s", e)

    def smooth_scroll_to_item(self, item, duration=220):
        try:
            if item is None:
                return

            if not self.sync_lyrics:
                return

            list_widget = self.lyrics_list
            sb = list_widget.verticalScrollBar()
            rect = list_widget.visualItemRect(item)

            target = sb.value() + rect.top()
            target -= list_widget.viewport().height() // 2
            target += rect.height() // 2

            target = max(sb.minimum(), min(sb.maximum(), target))

            if target == sb.value():
                return

            self._lyrics_auto_scrolling = True

            anim = QPropertyAnimation(sb, b"value", list_widget)
            anim.setDuration(duration)
            anim.setStartValue(sb.value())
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            def done():
                try:
                    self._lyrics_auto_scrolling = False
                except Exception as e:
                    logger.warning("smooth_scroll_to_item done caused an unexpected bug: %s", e)

            anim.finished.connect(done)

            list_widget._smooth_scroll_anim = anim
            anim.start()

        except Exception as e:
            self._lyrics_auto_scrolling = False
            logger.warning("smooth_scroll_to_item caused an unexpected bug: %s", e)

    def _tabs_moved(self, from_index: int, to_index: int):
        try:
            self.engine.preset.tab_order = [
                self.tabs.tabText(i)
                for i in range(self.tabs.count())
            ]

            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_tabs_moved caused an unexpected bug: %s", e)

    def _update_tab_order(self):
        try:
            default_order = [
                "Player",
                "Lyrics",
                "Queue",
                "Library",
                "Settings",
            ]
            tab_order = self.engine.preset.tab_order or default_order
            if tab_order is None:
                logger.debug("🟣🔴 No tab order set")
                return
            #the yellow emoji is: 
            logger.debug("🟣 Updating tab order to %s", tab_order)
            widgets = {}

            for i in range(self.tabs.count()):
                widgets[self.tabs.tabText(i)] = self.tabs.widget(i)

            for i in range(self.tabs.count() - 1, -1, -1):
                self.tabs.removeTab(i)

            for tab in tab_order:
                widget = widgets.get(tab)

                if widget is not None:
                    self.tabs.addTab(widget, tab)
        except Exception as e:
            logger.warning("_update_tab_order caused an unexpected bug: %s", e)

    def _select_library_song_by_index(self, song_index: int):
        try:
            if not hasattr(self, "song_list"):
                return

            for row in range(self.song_list.count()):
                item = self.song_list.item(row)
                if item is None:
                    continue

                real_index = item.data(Qt.UserRole)
                if real_index is None:
                    continue

                if int(real_index) == int(song_index):
                    self.song_list.setCurrentRow(row)
                    return
        except Exception as e:
            logger.warning("_select_library_song_by_index caused an unexpected bug: %s", e)

    def _library_settings_changed(self):
        try:
            if getattr(self, "_loading_preset", False):
                return

            self.engine.preset.library_sort_mode = self.library_sort_drop.currentIndex()
            self.engine.preset.library_show_images = self.library_images_cb.isChecked()

            self._refresh_library_list()
            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_library_settings_changed caused an unexpected bug: %s", e)

    def _library_song_display(self, index: int) -> str:
        try:
            data = self.songs.get(str(index))
            path = data.get("path") if data else None

            if not path:
                return f"Missing song #{index}"

            if self.engine.preset.library_sort_mode == 0:
                return os.path.basename(path)

            old_current = self.current_song

            try:
                self.current_song = index
                artist, title, cover_path = self.engine.get_data()
            finally:
                self.current_song = old_current

            if self.engine.preset.library_sort_mode == 1:
                return f"{artist} - {title}"

            return f"{title} - {artist}"
        except Exception as e:
            logger.warning("_library_song_display caused an unexpected bug: %s", e)

    def _refresh_library_list(self):
        try:
            if not hasattr(self, "song_list"):
                return

            self.song_list.setUpdatesEnabled(False)
            try:
                self.song_list.clear()

                indexes = list(range(len(self.songs)))

                def sort_key(i):
                    try:
                        return self._library_song_display(i).lower()
                    except Exception as e:
                        logger.warning("sort_key caused an unexpected bug: %s", e)

                if self.engine.preset.library_sort_mode != 0:
                    indexes.sort(key=sort_key)
            
                for index in indexes:
                    data = self.songs.get(str(index))
                    path = data.get("path") if data else None

                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, index)
                    item.setSizeHint(QSize(260, 68))

                    artist = "Unknown Artist"
                    title = self._library_song_display(index)
                    pixmap = QPixmap(BLANK_PATH)

                    if path and os.path.isfile(path):
                        try:
                            artist, title, cover_path = self._get_row_data_cached(index)
                            pixmap = self._get_row_pixmap_cached(cover_path)
                        except Exception:
                            pixmap = QPixmap(BLANK_PATH)

                    self.song_list.addItem(item)
                    self.song_list.setItemWidget(item, SongRowWidget(title, artist, pixmap, show_handle=False, row_height=68))
            finally:
                self.song_list.setUpdatesEnabled(True)
        except Exception as e:
            logger.warning("_refresh_library_list caused an unexpected bug: %s", e)

    def _edit_selected_theme_color(self):
        try:
            index = self.theme_color_drop.currentIndex()

            if index < 0 or index >= len(self.theme_color_keys):
                return

            key = self.theme_color_keys[index]

            current = self.current_theme.get(key, DEFAULT_THEME.get(key, "#ffffff"))
            color = QColorDialog.getColor(
                initial=Qt.GlobalColor.white,
                parent=self,
                title=f"Choose {self.theme_color_drop.currentText()} Color"
            )

            if color.isValid():
                set_theme_value(self.theme, key, color.name())
        except Exception as e:
            logger.warning("_edit_selected_theme_color caused an unexpected bug: %s", e)

    def _reset_selected_theme_color(self):
        try:
            index = self.theme_color_drop.currentIndex()

            if index < 0 or index >= len(self.theme_color_keys):
                return

            key = self.theme_color_keys[index]

            if key not in DEFAULT_THEME:
                return

            set_theme_value(self.theme, key, DEFAULT_THEME[key])
        except Exception as e:
            logger.warning("_reset_selected_theme_color caused an unexpected bug: %s", e)

    def _reset_all_theme(self):
        try:
            self.current_theme = DEFAULT_THEME.copy()
            self.theme.current_theme = self.current_theme

            apply_theme(QApplication.instance(), {"theme": self.current_theme})

            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_reset_all_theme caused an unexpected bug: %s", e)

    def _queue_changed(self):
        try:
            self.engine.preset.queue = list(self.engine.queue)
            self._refresh_queue_list()
            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_queue_changed caused an unexpected bug: %s", e)

    def _fill_queue(self):
        try:
            if not self.engine.queue_auto_enabled:
                self.engine.queue.clear()
                self._queue_changed()
                return
            songs = self.get_song_list()
            if not songs:
                return

            self.QUEUE_LIMIT = 80

            all_indexes = list(range(len(songs)))

            blocked = set(self.engine.queue)
            blocked.add(self.current_song)

            needed = self.QUEUE_LIMIT - len(self.engine.queue)
            if needed <= 0:
                return

            choices = [i for i in all_indexes if i not in blocked]

            if len(choices) < needed:
                choices = [i for i in all_indexes if i != self.current_song]

            if not choices:
                return

            add_count = min(needed, len(choices))
            self.engine.queue.extend(random.sample(choices, add_count))

            self._queue_changed()
            QTimer.singleShot(1000, self._analyze_queue_loudness_top_5)
        except Exception as e:
            logger.warning("_fill_queue caused an unexpected bug: %s", e)

    def _queue_item_double_clicked(self, item):
        try:
            clicked_index = item.data(Qt.UserRole)

            if clicked_index is None:
                return

            try:
                clicked_index = int(clicked_index)
            except Exception:
                return

            try:
                queue_pos = self.engine.queue.index(clicked_index)
            except ValueError:
                return

            current_index = self.current_song

            selected_path = self.songs.get(str(clicked_index), {}).get("path")
            if not selected_path or not os.path.isfile(selected_path):
                return

            previous_queue_items = self.engine.queue[:queue_pos + 1]

            self.engine.play_order = [current_index] + previous_queue_items
            self.engine.play_order_pos = len(self.engine.play_order) - 1

            del self.engine.queue[:queue_pos + 1]
            self._fill_queue()

            self.current_song = clicked_index
            self.engine.preset.current_song = clicked_index

            self._refresh_queue_list()
            self.engine.play(force_reload=True)
            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_queue_item_double_clicked caused an unexpected bug: %s", e)

    def _queue_song_name(self, index: int) -> str:
        try:
            data = self.songs.get(str(index))
            if not data:
                return f"Missing song #{index}"

            path = data.get("path")
            if not path:
                return f"Missing song #{index}"

            artist, title, cover_path = self.engine.get_data_for_path(path)

            if self.engine.preset.library_sort_mode == 1:
                return f"{artist} - {title}"

            return f"{title} - {artist}"
        except Exception as e:
            logger.warning("_queue_song_name caused an unexpected bug: %s", e)

    def _refresh_queue_list(self):
        try:
            if not hasattr(self, "queue_list"):
                return

            self.queue_list.setUpdatesEnabled(False)
            try:
                self.queue_list.clear()
                self.queue_list.setIconSize(QSize(52, 52))

                for index in self.engine.queue:
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, index)
                    item.setSizeHint(QSize(260, 68))

                    artist, title, cover_path = self._get_row_data_cached(index)
                    pixmap = self._get_row_pixmap_cached(cover_path)

                    self.queue_list.addItem(item)
                    self.queue_list.setItemWidget(
                        item,
                        SongRowWidget(
                            title,
                            artist,
                            pixmap,
                            show_handle=True,
                            row_height=68
                        )
                    )
            finally:
                self.queue_list.setUpdatesEnabled(True)
        except Exception as e:
            logger.warning("_refresh_queue_list caused an unexpected bug: %s", e)

    def _analyze_queue_loudness_top_5(self):
        try:
            if not self.engine.preset.normalize_audio:
                return
            if getattr(self, "_queue_loudness_busy", False):
                return

            self._queue_loudness_busy = True

            try:
                MAX_ACTIVE_WORKERS = 1

                active_workers = len(getattr(self.engine, "_loudness_threads", {}))
                if active_workers >= MAX_ACTIVE_WORKERS:
                    return

                for queued_index in self.engine.queue[:5]:
                    data = self.songs.get(str(queued_index))
                    if not data:
                        continue

                    path = data.get("path")
                    if not path or not os.path.isfile(path):
                        continue

                    if path in self.engine._loudness_cache:
                        continue

                    if path in getattr(self.engine, "_loudness_threads", {}):
                        continue
                
                    self.engine.start_loudness_analysis(path)
                    break

            finally:
                self._queue_loudness_busy = False

            QTimer.singleShot(1500, self._analyze_queue_loudness_top_5)
        except Exception as e:
            logger.warning("_analyze_queue_loudness_top_5 caused an unexpected bug: %s", e)

    def _add_selected_to_queue(self):
        try:
            self.engine.queue_auto_enabled = True
            self.engine.queue.clear()
            self._fill_queue()
            self._queue_changed()
        except Exception as e:
            logger.warning("_add_selected_to_queue caused an unexpected bug: %s", e)

    def _remove_selected_from_queue(self):
        try:
            selected = sorted(
                {i.row() for i in self.queue_list.selectedIndexes()},
                reverse=True
            )

            for row in selected:
                if 0 <= row < len(self.engine.queue):
                    self.engine.queue.pop(row)

            self._fill_queue()
            self._queue_changed()
        except Exception as e:
            logger.warning("_remove_selected_from_queue caused an unexpected bug: %s", e)

    def _set_checkbox_silent(self, cb, state):
        try:
            cb.blockSignals(True)
            cb.setChecked(state)
            cb.blockSignals(False)
        except Exception as e:
            logger.warning("_set_checkbox_silent caused an unexpected bug: %s", e)

    def _geometry_to_dict(self, window):
        try:
            if window is None:
                return None

            g = window.geometry()
            return {
                "x": g.x(),
                "y": g.y(),
                "w": g.width(),
                "h": g.height()
            }
        except Exception as e:
            logger.warning("_geometry_to_dict caused an unexpected bug: %s", e)

    def _restore_geometry(self, geometry):
        try:
            if not isinstance(geometry, dict):
                return

            try:
                self.setGeometry(QRect(
                    int(geometry.get("x", self.x())),
                    int(geometry.get("y", self.y())),
                    int(geometry.get("w", self.width())),
                    int(geometry.get("h", self.height()))
                ))
            except Exception as e:
                logger.warning("🟡 Main window geometry restore failed: %s", e)
        except Exception as e:
            logger.warning("_restore_geometry caused an unexpected bug: %s", e)

    def _save_all_window_positions(self):
        try:
            self.engine.preset.main_window_geometry = self._geometry_to_dict(self)

            lyrics = self.engine.lyrics

            if lyrics.window is not None:
                self.engine.preset.lyrics_window_geometry = lyrics._geometry_to_dict(lyrics.window)

            if lyrics.floating_window is not None:
                self.engine.preset.floating_window_geometry = lyrics._geometry_to_dict(lyrics.floating_window)

            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_save_all_window_positions caused an unexpected bug: %s", e)

    def moveEvent(self, event):
        try:
            self._save_all_window_positions()
            super().moveEvent(event)
        except Exception as e:
            logger.warning("moveEvent caused an unexpected bug: %s", e)

    def resizeEvent(self, event):
        try:
            self._save_all_window_positions()
            super().resizeEvent(event)
        except Exception as e:
            logger.warning("resizeEvent caused an unexpected bug: %s", e)

    def _set_logging_level(self, index: int):
        try:
            levels = {
                0: (logging.DEBUG, "DEBUG", "🟣"),
                1: (logging.INFO, "INFO", "🔵"),
                2: (logging.WARNING, "WARNING", "🟡"),
                3: (logging.ERROR, "ERROR", "🔴"),
            }

            level, text, emoji = levels.get(
                index,
                (logging.INFO, "INFO", "🔵")
            )

            logger.setLevel(level)

            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.setLevel(logging.DEBUG)
                else:
                    handler.setLevel(level)

            self.engine.preset.logging_level = index

            logger.log(level, f"Logging Level: {text}")
        except Exception as e:
            logger.warning("_set_logging_level caused an unexpected bug: %s", e)

    def _set_console_logging(self, stream):
        try:
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    logger.removeHandler(handler)
                    try:
                        handler.close()
                    except Exception:
                        pass

            if stream is None:
                return

            console_handler = logging.StreamHandler(stream)
            console_handler.setLevel(logger.level)
            console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            logger.addHandler(console_handler)
        except Exception as e:
            logger.warning("_set_console_logging caused an unexpected bug: %s", e)

    def _reset_console_logging(self):
        try:
            for handler in logger.handlers:
                if (isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)):
                    handler.stream = sys.stdout
        except Exception as e:
            logger.warning("_reset_console_logging caused an unexpected bug: %s", e)

    def toggle_console(self, state: bool = True):
        try:
            if state:
                self.create_console()
            else:
                self.remove_console()
        except Exception as e:
            logger.warning("toggle_console caused an unexpected bug: %s", e)

    def create_console(self):
        try:
            if self._console_enabled:
                return

            ctypes.windll.kernel32.AllocConsole()
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)

            global _console_owner
            _console_owner = self
            kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, True)

            console_stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
            console_stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)

            sys.stdout = StreamToLogger(console_stdout, logger.info)
            sys.stderr = StreamToLogger(console_stderr, logger.error)
            sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")

            self._set_console_logging(console_stdout)

            self._console_enabled = True
            logger.info("Console enabled")
            logger.info(f"Version: {player_ver}")
        except Exception as e:
            logger.warning("create_console caused an unexpected bug: %s", e)

    def _console_closed_by_user(self):
        try:
            self._console_enabled = False
            self.engine.preset.show_console = False

            self._set_checkbox_silent(self.show_console_cb, False)
            self._set_console_logging(None)

            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_console_closed_by_user caused an unexpected bug: %s", e)

    def remove_console(self):
        try:
            if not self._console_enabled:
                return

            logger.info("Console disabled")

            self._set_console_logging(None)

            sys.stdout = self._old_stdout
            sys.stderr = self._old_stderr
            sys.stdin = self._old_stdin

            global _console_owner
            kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, False)
            _console_owner = None
            ctypes.windll.kernel32.FreeConsole()
            self._console_enabled = False
        except Exception as e:
            logger.warning("remove_console caused an unexpected bug: %s", e)

    def _scroll_plain_lyrics(self, index: int):
        try:
            if self.lyrics_list.count() == 0:
                return

            index = max(0, min(self.lyrics_list.count() - 1, index))
            self.current_lyrics_index = index

            for i in range(self.lyrics_list.count()):
                item = self.lyrics_list.item(i)
                if item is None:
                    continue

                font = item.font()
                font.setBold(False)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.gray)
                item.setBackground(Qt.GlobalColor.transparent)

            item = self.lyrics_list.item(index)
            if item is not None:
                self.smooth_scroll_to_item(item)

            self.engine.lyrics.update_window(self.current_lyrics_data, index, False)
        except Exception as e:
            logger.warning("_scroll_plain_lyrics caused an unexpected bug: %s", e)

    def _on_translated_changed(self):
        try:
            self._apply_ui_to_engine()

            if self.engine.get_current_song():
                self._load_lyrics_for_current_song()
                self._update_lyrics_highlight()
        except Exception as e:
            logger.warning("_on_translated_changed caused an unexpected bug: %s", e)

    def _on_romaji_changed(self):
        try:
            self._apply_ui_to_engine()

            if self.engine.get_current_song():
                self._load_lyrics_for_current_song()
                self._update_lyrics_highlight()
        except Exception as e:
            logger.warning("_on_romaji_changed caused an unexpected bug: %s", e)

    def _delete_selected_songs(self):
        try:
            selected = self.song_list.selectedIndexes()
            if not selected:
                return

            rows_to_delete = sorted({i.row() for i in selected}, reverse=True)
            playing_path_before_delete = self.engine._current_media_path

            old_paths = [
                self.songs[str(i)]["path"]
                for i in range(self.song_list.count())
                if str(i) in self.songs and "path" in self.songs[str(i)]
            ]

            for row in rows_to_delete:
                self.song_list.takeItem(row)

            remaining_paths = [
                path for i, path in enumerate(old_paths)
                if i not in rows_to_delete
            ]

            self.songs = {
                str(i): {"path": path}
                for i, path in enumerate(remaining_paths)
            }

            old_current = self.current_song

            if self.song_list.count() == 0:
                self.current_song = 0
            elif old_current in rows_to_delete:
                self.current_song = min(old_current, self.song_list.count() - 1)
            else:
                deleted_before_current = sum(1 for row in rows_to_delete if row < old_current)
                self.current_song = max(0, old_current - deleted_before_current)

            self.engine.preset.current_song = self.current_song

            valid_count = self.song_list.count()

            def remap_index(i):
                try:
                    if i in rows_to_delete:
                        return None

                    shift = sum(1 for row in rows_to_delete if row < i)
                    new_i = i - shift

                    if 0 <= new_i < valid_count:
                        return new_i

                    return None
                except Exception as e:
                    logger.warning("remap_index caused an unexpected bug: %s", e)

            self.engine.play_order = [
                new_i for i in self.engine.play_order
                if (new_i := remap_index(i)) is not None
            ]

            if self.engine.play_order:
                self.engine.play_order_pos = min(
                    self.engine.play_order_pos,
                    len(self.engine.play_order) - 1
                )
            else:
                self.engine.play_order_pos = -1

            self.engine.history = deque(
                [new_i for i in self.engine.history if (new_i := remap_index(i)) is not None],
                maxlen=self.engine.history.maxlen
            )

            self.engine.recent_shuffle = deque(
                [new_i for i in self.engine.recent_shuffle if (new_i := remap_index(i)) is not None],
                maxlen=self.engine.recent_shuffle.maxlen
            )

            valid_paths = {data["path"] for data in self.songs.values() if "path" in data}

            if playing_path_before_delete and playing_path_before_delete not in valid_paths:
                self.engine.stop()

            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_delete_selected_songs caused an unexpected bug: %s", e)

    def _save_current_preset_silent(self) -> None:
        try:
            if getattr(self, "_loading_ui", False):
                return

            try:
                os.makedirs(os.path.dirname(PRESET_PATH), exist_ok=True)
                with open(PRESET_PATH, "w", encoding="utf-8") as f:
                    json.dump(self._current_preset(), f, indent=2)
                logger.debug("🟣 Preset Autosaved")
            except Exception as e:
                logger.warning("🟡Preset autosave failed: %s", e)
        except Exception as e:
            logger.warning("_save_current_preset_silent caused an unexpected bug: %s", e)

    def _autosave_current_preset(self) -> None:
        try:
            if getattr(self, "_loading_ui", False):
                return

            if not hasattr(self, "_autosave_timer"):
                self._autosave_timer = QTimer(self)
                self._autosave_timer.setSingleShot(True)
                self._autosave_timer.setInterval(250)
                self._autosave_timer.timeout.connect(self._save_current_preset_silent)

            self._autosave_timer.start()
        except Exception as e:
            logger.warning("_autosave_current_preset caused an unexpected bug: %s", e)

    def _lyrics_context_menu(self, pos):
        try:
            item = self.lyrics_list.itemAt(pos)
            if item is None:
                return

            menu = QMenu(self)

            copy_action = menu.addAction("Copy current line")
            selected_action = menu.exec(self.lyrics_list.mapToGlobal(pos))

            if selected_action == copy_action:
                self._copy_lyric_line(item)
        except Exception as e:
            logger.warning("_lyrics_context_menu caused an unexpected bug: %s", e)

    def _copy_lyric_line(self, item):
        try:
            if item is None:
                return

            text = item.text()
            if not text:
                return

            clipboard = QApplication.clipboard()
            clipboard.setText(text)
        except Exception as e:
            logger.warning("_copy_lyric_line caused an unexpected bug: %s", e)

    def _lyric_item_double_clicked(self, item):
        try:
            lyric_time = item.data(Qt.UserRole)

            if lyric_time is None:
                return

            song = self.engine.get_current_song()
            if not song:
                return

            if self.engine._current_media_path != song:
                self.engine.play(force_reload=True)

            self.engine.set_time(float(lyric_time))
            self._update_position_slider()
            self._update_lyrics_highlight()
        except Exception as e:
            logger.warning("_lyric_item_double_clicked caused an unexpected bug: %s", e)

    def _play_song_at_index(self, row: int):
        try:
            if row < 0 or row >= self.song_list.count():
                return

            if str(row) not in self.songs:
                return

            current_index = self.current_song

            if row != current_index:
                if self.engine.play_order_pos >= 0 and current_index >= 0:
                    self.engine.history.append(current_index)

                self.current_song = row
                self.engine.preset.current_song = row
                self._select_library_song_by_index(self.current_song)
                self.engine._commit_current_to_timeline(row)

            self.engine.play(force_reload=True)
            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_play_song_at_index caused an unexpected bug: %s", e)

    def _library_item_double_clicked(self, item):
        try:
            index = item.data(Qt.UserRole)

            if index is None:
                return

            self._play_song_at_index(int(index))
        except Exception as e:
            logger.warning("_library_item_double_clicked caused an unexpected bug: %s", e)

    def _temp_load_lyrics_for_current_song(self):
        try:
            artist, title, _ = self.engine.get_data()

            loading_lyrics = {
                "timed": False,
                "lyrics": [
                    {
                        "time": None,
                        "text": f"{artist} - {title}"
                    }
                ]
            }

            self.current_lyrics_data = loading_lyrics["lyrics"]
            self.current_lyrics_timed = False
            self.current_lyrics_index = 0

            self.engine.lyrics.update_window(
                self.current_lyrics_data,
                0,
                False
            )

            self.engine.lyrics.update_floating_window(
                self.current_lyrics_data,
                0,
                reset_hover=True
            )
        except Exception as e:
            logger.warning("_temp_load_lyrics_for_current_song caused an unexpected bug: %s", e)

    def _load_lyrics_for_current_song(self):
        try:
            self._lyrics_request_id = getattr(self, "_lyrics_request_id", 0) + 1
            self.current_lyrics_data = []
            self.current_lyrics_index = -1
            self.lyrics_list.clear()
            self.lyrics_status.setText("Loading lyrics.")
            self._temp_load_lyrics_for_current_song()
            self._lyrics_load_timer.start(700)
        except Exception as e:
            logger.warning("_load_lyrics_for_current_song caused an unexpected bug: %s", e)

    def _load_lyrics_for_current_song_now(self):
        try:
            request_id = self._lyrics_request_id
            song_path = self.engine.get_current_song()

            self._plain_floating_title = ""
            self.current_lyrics_data = []
            self.current_lyrics_index = -1

            self.lyrics_list.blockSignals(True)
            self.lyrics_list.clear()
            self.lyrics_status.setText("Loading lyrics..")

        

            thread = QThread(self)
            worker = LyricsWorker(self.engine.lyrics)
            worker.moveToThread(thread)

            if not hasattr(self, "_lyrics_threads"):
                self._lyrics_threads = {}

            self._lyrics_threads[request_id] = (thread, worker)

            thread.started.connect(worker.run)

            safe_song_path = song_path or None

            worker.finished.connect(
                lambda data, rid=request_id, path=safe_song_path:
                    self._lyrics_bridge.loaded.emit(data, rid, path)
            )

            worker.failed.connect(
                lambda error, rid=request_id, path=safe_song_path:
                    self._lyrics_bridge.failed.emit(error, rid, path)
            )

            worker.status.connect(
                lambda message, rid=request_id, path=safe_song_path:
                    self._lyrics_bridge.status.emit(message, rid, path)
            )

            worker.finished.connect(thread.quit)
            worker.failed.connect(thread.quit)

            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda rid=request_id: self._lyrics_thread_finished(rid))

            thread.start()
        except Exception as e:
            logger.warning("_load_lyrics_for_current_song_now caused an unexpected bug: %s", e)

    def _lyrics_thread_finished(self, request_id=None):
        try:
            if request_id is None:
                self._lyrics_worker = None
                self._lyrics_thread = None
                return

            if hasattr(self, "_lyrics_threads"):
                self._lyrics_threads.pop(request_id, None)
        except Exception as e:
            logger.warning("_lyrics_thread_finished caused an unexpected bug: %s", e)

    def _lyrics_status_changed(self, message: str, request_id=None, song_path=None):
        try:
            if song_path != self.engine.get_current_song():
                return
            if request_id is not None and request_id != getattr(self, "_lyrics_request_id", None):
                return

            self.lyrics_status.setText(message)
        except Exception as e:
            logger.warning("_lyrics_status_changed caused an unexpected bug: %s", e)

    def _lyrics_failed(self, error: str, request_id=None, song_path=None):
        try:
            if song_path != self.engine.get_current_song():
                return
            if request_id is not None and request_id != getattr(self, "_lyrics_request_id", None):
                return

            if song_path and song_path != self.engine.get_current_song():
                return

            self.lyrics_list.blockSignals(False)
            self.lyrics_status.setText("Lyrics failed to load")
            logger.warning("🟡 Lyrics worker failed: %s", error)
        except Exception as e:
            logger.warning("_lyrics_failed caused an unexpected bug: %s", e)

    def _lyrics_loaded(self, data, request_id=None, song_path=None):
        try:
            if song_path != self.engine.get_current_song():
                return
            if request_id is not None and request_id != getattr(self, "_lyrics_request_id", None):
                return

            if song_path and song_path != self.engine.get_current_song():
                return
            try:
                self.current_lyrics_data = data["lyrics"] if data else []

                is_placeholder = (
                    len(self.current_lyrics_data) == 1
                    and self.current_lyrics_data[0].get("time") is None
                )

                if is_placeholder:
                    self.lyrics_status.setText("No lyrics Found")
                    logger.info("🔴 No Lyrics Available")
                    return

                self.current_lyrics_timed = bool(data.get("timed", False))

                if self.current_lyrics_timed:
                    self.lyrics_status.setText("Timed lyrics")
                    logger.info("🟢 Timed lyrics")
                else:
                    self.lyrics_status.setText("Plain lyrics")
                    logger.info("🟡 Plain lyrics" if self.current_lyrics_data else "🔴 No Lyrics Avaliable")

                self.lyrics_list.clear()

                for line in self.current_lyrics_data:
                    text = line.get("text", "")

                    item = QListWidgetItem(text)

                    item.setTextAlignment(Qt.AlignCenter)

                    item.setData(Qt.UserRole, line.get("time"))

                    font = item.font()
                    font.setPointSize(12)

                    if self.engine.lyrics.window and self.engine.lyrics.window.contains_japanese(text):
                        font.setFamily("Noto Sans JP")
                    else:
                        font.setFamily("Segoe UI Variable")

                    item.setFont(font)

                    self.lyrics_list.addItem(item)

                self.current_lyrics_index = -1
                self._update_lyrics_highlight()


            finally:
                self.lyrics_list.blockSignals(False)
        except Exception as e:
            logger.warning("_lyrics_loaded caused an unexpected bug: %s", e)

    def _highlight_current_lyric(self, index: int, force: bool = False):
        try:
            old_index = self.current_lyrics_index

            if old_index == index and not force:
                return

            self.current_lyrics_index = index

            for i in range(self.lyrics_list.count()):
                item = self.lyrics_list.item(i)
                if item is None:
                    continue

                active = i == index

                font = item.font()
                font.setBold(active)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.white if active else Qt.GlobalColor.gray)
                item.setBackground(Qt.GlobalColor.transparent)

            if 0 <= index < self.lyrics_list.count():
                item = self.lyrics_list.item(index)
                self.smooth_scroll_to_item(item)

            self.engine.lyrics.update_window(self.current_lyrics_data, index, True)
            self.engine.lyrics.update_floating_window(self.current_lyrics_data, index)
        except Exception as e:
            logger.warning("_highlight_current_lyric caused an unexpected bug: %s", e)

    def _clear_lyrics_highlight(self):
        try:
            self.current_lyrics_index = -1

            for i in range(self.lyrics_list.count()):
                item = self.lyrics_list.item(i)
                if item is None:
                    continue

                font = item.font()
                font.setBold(False)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.gray)
                item.setBackground(Qt.GlobalColor.transparent)

            self.engine.lyrics.update_window(self.current_lyrics_data, -1)
            self.engine.lyrics.update_floating_window(self.current_lyrics_data, -1)
        except Exception as e:
            logger.warning("_clear_lyrics_highlight caused an unexpected bug: %s", e)

    def _update_lyrics_highlight(self):
        try:
            if not self.current_lyrics_data or self.lyrics_list.count() == 0:
                return

            full_time, current_time = self.engine.get_time()

            if self.current_lyrics_timed:
                index = self.engine.lyrics.current_lyric_index(
                    current_time,
                    self.current_lyrics_data
                )

                if index != self.current_lyrics_index:
                    if index < 0:
                        self._clear_lyrics_highlight()
                    else:
                        self._highlight_current_lyric(index)

                return

            artist, title, cover_path = self.engine.get_data()
            plain_title = f"{artist} - {title}"

            if full_time > 0 and len(self.current_lyrics_data) > 1:
                ratio = max(0.0, min(current_time / full_time, 1.0))
                plain_index = int(ratio * (len(self.current_lyrics_data) - 1))
            else:
                plain_index = 0

            if plain_index != self.current_lyrics_index:
                self._scroll_plain_lyrics(plain_index)

            self.engine.lyrics.update_floating_window(
                [{"time": None, "text": plain_title}],
                0
            )
        except Exception as e:
            logger.warning("_update_lyrics_highlight caused an unexpected bug: %s", e)

    def dragEnterEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    path = url.toLocalFile()

                    if os.path.isdir(path) or is_supported_library_file(path):
                        event.acceptProposedAction()
                        return

            event.ignore()
        except Exception as e:
            logger.warning("dragEnterEvent caused an unexpected bug: %s", e)

    def dropEvent(self, event):
        try:
            if not isValid(self.song_list):
                logger.warning("🟡 song_list was deleted, skipping dropEvent")
                return

            added = False
            last_index = None
            existing_paths = {d.get("path") for d in self.songs.values()}

            for url in event.mimeData().urls():
                dropped_path = url.toLocalFile()

                for path in collect_supported_audio_paths(dropped_path):
                    if path in existing_paths:
                        continue

                    index = str(len(self.songs))
                    self.songs[index] = {"path": path}
                    existing_paths.add(path)
                    last_index = int(index)
                    added = True

                    logger.debug("🟣 Added: %s", path)

            if last_index is not None:
                self.current_song = last_index
                self.engine.preset.current_song = last_index

                artist, title, cover_path = self.engine.get_data_for_path(
                    self.songs[str(last_index)]["path"]
                )

                if os.path.exists(cover_path):
                    pixmap = QPixmap(cover_path)
                    if not pixmap.isNull():
                        self.label.setPixmap(pixmap)
                        self.cover_path = cover_path

                self.setWindowTitle(
                    f"Yet Another Music Player — {self._get_current_preset_name()} — {artist} — {title}"
                )

            if added:
                self._refresh_library_list()
                self.engine._update_history_limit()
                self._autosave_current_preset()
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception as e:
            logger.warning("dropEvent caused an unexpected bug: %s", e)

    def get_song_list(self) -> List[str]:
        try:
            songs = []

            for data in self.songs.values():
                path = data.get("path")
                if path and os.path.isfile(path):
                    songs.append(path)

            return songs
        except Exception as e:
            logger.warning("get_song_list caused an unexpected bug: %s", e)

    def _reset_progress_ui(self):
        try:
            self.position_slider.blockSignals(True)
            self.position_slider.setRange(0, 0)
            self.position_slider.setValue(0)
            self.position_slider.blockSignals(False)
            self.time_label.setText("0:00 / 0:00")
        except Exception as e:
            logger.warning("_reset_progress_ui caused an unexpected bug: %s", e)

    def _update_preset_status_label(self):
        try:
            if hasattr(self, "preset_status_label"):
                self.preset_status_label.setText(
                    f"Current preset: {self._get_current_preset_name()}"
                )
        except Exception as e:
            logger.warning("_update_preset_status_label caused an unexpected bug: %s", e)

    def _save_current_preset_button(self):
        try:
            self.preset_name.setText(self._get_current_preset_name())
            self._save_preset_file()
            self._update_preset_status_label()
        except Exception as e:
            logger.warning("_save_current_preset_button caused an unexpected bug: %s", e)

    def _save_as_new_preset_dialog(self):
        try:
            name, ok = QInputDialog.getText(
                self,
                "Save as New Preset",
                "Preset name:"
            )

            if not ok:
                return

            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Invalid name", "Preset name cannot be empty.")
                return

            self.preset_name.setText(name)
            self._save_preset_file()
            self._update_preset_status_label()
        except Exception as e:
            logger.warning("_save_as_new_preset_dialog caused an unexpected bug: %s", e)

    def _load_preset_dialog(self):
        try:
            self._refresh_preset_dropdown()

            presets = [
                self.preset_combo.itemText(i)
                for i in range(self.preset_combo.count())
            ]

            if not presets:
                QMessageBox.warning(self, "No presets", "No presets were found.")
                return

            current = self._get_current_preset_name()
            current_index = presets.index(current) if current in presets else 0

            name, ok = QInputDialog.getItem(
                self,
                "Load Preset",
                "Choose preset:",
                presets,
                current_index,
                False
            )

            if not ok or not name:
                return

            self.preset_combo.setCurrentText(name)
            self._load_preset_file()
            self._update_preset_status_label()
        except Exception as e:
            logger.warning("_load_preset_dialog caused an unexpected bug: %s", e)

    def _preset_folder(self, name: str) -> str:
        try:
            return os.path.join(APPDATA_DIR, name)
        except Exception as e:
            logger.warning("_preset_folder caused an unexpected bug: %s", e)

    def _preset_path(self, name: str) -> str:
        try:
            return os.path.join(self._preset_folder(name), "preset.json")
        except Exception as e:
            logger.warning("_preset_path caused an unexpected bug: %s", e)

    def _settings_path(self) -> str:
        try:
            return os.path.join(APPDATA_DIR, "settings.json")
        except Exception as e:
            logger.warning("_settings_path caused an unexpected bug: %s", e)

    def _set_current_preset_name(self, name: str) -> None:
        try:
            global PROFILE_NAME, PROFILE_DIR, TEMP_DIR, PRESET_PATH
            PROFILE_NAME = name
            PROFILE_DIR = os.path.join(APPDATA_DIR, PROFILE_NAME)
            TEMP_DIR = os.path.join(PROFILE_DIR, "Temp")
            PRESET_PATH = os.path.join(PROFILE_DIR, "preset.json")

            os.makedirs(PROFILE_DIR, exist_ok=True)
            os.makedirs(TEMP_DIR, exist_ok=True)

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
        except Exception as e:
            logger.warning("_set_current_preset_name caused an unexpected bug: %s", e)

    def _get_current_preset_name(self) -> str:
        try:
            try:
                if not os.path.isfile(self._settings_path()):
                    return "Default"
                with open(self._settings_path(), "r", encoding="utf-8") as f:
                    return json.load(f).get("Current Preset", "Default")
            except Exception:
                return "Default"
        except Exception as e:
            logger.warning("_get_current_preset_name caused an unexpected bug: %s", e)

    def _refresh_preset_dropdown(self) -> None:
        try:
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
        except Exception as e:
            logger.warning("_refresh_preset_dropdown caused an unexpected bug: %s", e)

    def _save_preset_file(self) -> None:
        try:
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
        except Exception as e:
            logger.warning("_save_preset_file caused an unexpected bug: %s", e)

    def _load_preset_file(self) -> None:
        try:
            name = self.preset_combo.currentText().strip()
            if not name:
                return

            path = self._preset_path(name)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._set_current_preset_name(name)
                self._apply_preset_to_ui(data)

            except Exception as e:
                QMessageBox.critical(self, "Preset load failed", str(e))
                return

            self.setWindowTitle(
                f"Yet Another Music Player — {self._get_current_preset_name()} — {self._get_current_song_name()}"
            )
        except Exception as e:
            logger.warning("_load_preset_file caused an unexpected bug: %s", e)

    def _export_current_preset(self) -> None:
        try:
            try:
                preset_name = self.preset_combo.currentText().strip() or self._get_current_preset_name()
                path = self._preset_path(preset_name)

                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._current_preset(), f, indent=2)

                self._set_current_preset_name(preset_name)
                self._refresh_preset_dropdown()
                self.preset_combo.setCurrentText(preset_name)

                QMessageBox.information(
                    self,
                    "Default preset updated",
                    f'"{preset_name}" is now the default preset.'
                )
            except Exception as e:
                QMessageBox.critical(self, "Preset export failed", str(e))
        except Exception as e:
            logger.warning("_export_current_preset caused an unexpected bug: %s", e)

    def _current_preset(self) -> Dict:
        try:
            songs = [data["path"] for data in self.songs.values() if "path" in data]
            return {
                "preset": asdict(self.engine.preset),
                "songs": songs,
                "theme": self.current_theme.copy(),
            }
        except Exception as e:
            logger.warning("_current_preset caused an unexpected bug: %s", e)

    def _handle_song_end(self):
        try:
            songs = self.get_song_list()
            if not songs:
                return

            self._reset_progress_ui()

            if self.engine.preset.repeat:
                self.engine.play(force_reload=True)
            else:
                self.engine.next()
        except Exception as e:
            logger.warning("_handle_song_end caused an unexpected bug: %s", e)

    def _update_volume_label(self, value):
        try:
            self.volume_value_label.setText(f"{value}%")
        except Exception as e:
            logger.warning("_update_volume_label caused an unexpected bug: %s", e)

    def _title_font_family(self) -> str:
        try:
            if not hasattr(self, "current_theme") or self.current_theme is None:
                return DEFAULT_THEME["title_font"]

            return self.current_theme.get("title_font", DEFAULT_THEME["title_font"])
        except Exception as e:
            logger.warning("_title_font_family caused an unexpected bug: %s", e)

    def _title_font(self, point_size: int | None = None, bold: bool = False) -> QFont:
        try:
            font = QFont(self._title_font_family())

            if point_size is not None:
                font.setPointSize(point_size)

            font.setBold(bold)
            return font
        except Exception as e:
            logger.warning("_title_font caused an unexpected bug: %s", e)

    def _repolish_widget(self, widget):
        try:
            if widget is None:
                return

            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.updateGeometry()
                widget.update()
            except Exception:
                pass
        except Exception as e:
            logger.warning("_repolish_widget caused an unexpected bug: %s", e)

    def _apply_title_font_to_song_text_widgets(self):
        try:
            title_font = self._title_font(self._theme_int("title_font_size", 15), True)
            artist_font = self._title_font(self._theme_int("artist_font_size", 11), True)
            item_font = self._title_font(self._theme_int("normal_font_size", 13), True)

            title_family = self._title_font_family()
            text_color = self.current_theme.get("text", DEFAULT_THEME["text"])
            muted_color = self.current_theme.get("muted_text", DEFAULT_THEME["muted_text"])

            title_label = getattr(self, "now_playing_title", None)
            if title_label is not None:
                title_label.setFont(title_font)
                title_label.setStyleSheet(f"""
                    font-family: "{title_family}";
                    font-size: {title_font.pointSize()}pt;
                    font-weight: 700;
                    color: {text_color};
                    background-color: transparent;
                """)
                self._repolish_widget(title_label)

            artist_label = getattr(self, "now_playing_artist", None)
            if artist_label is not None:
                artist_label.setFont(artist_font)
                artist_label.setStyleSheet(f"""
                    font-family: "{title_family}";
                    font-size: {artist_font.pointSize()}pt;
                    font-weight: 600;
                    color: {muted_color};
                    background-color: transparent;
                """)
                self._repolish_widget(artist_label)

            for list_widget in (
                getattr(self, "song_list", None),
                getattr(self, "queue_list", None),
            ):
                if list_widget is None:
                    continue

                list_widget.setFont(item_font)

                for row in range(list_widget.count()):
                    item = list_widget.item(row)
                    if item is not None:
                        item.setFont(item_font)

                self._repolish_widget(list_widget.viewport())
                self._repolish_widget(list_widget)
        except Exception as e:
            logger.warning("_apply_title_font_to_song_text_widgets caused an unexpected bug: %s", e)

    def _set_now_playing_info(self, artist: str, title: str):
        try:
            self.now_playing_title.setText(title or "Unknown Title")
            self.now_playing_artist.setText(artist or "Unknown Artist")

            title_font = self._title_font(self._theme_int("title_font_size", 15), True)
            artist_font = self._title_font(self._theme_int("artist_font_size", 11), True)

            self.now_playing_title.setFont(title_font)
            self.now_playing_artist.setFont(artist_font)
        except Exception as e:
            logger.warning("_set_now_playing_info caused an unexpected bug: %s", e)

    def _position_slider_moved(self, value):
        try:
            full_time = self.position_slider.maximum()
            self.time_label.setText(
                f"{self._format_time(value)} / {self._format_time(full_time)}"
            )
        except Exception as e:
            logger.warning("_position_slider_moved caused an unexpected bug: %s", e)

    def _format_time(self, seconds: float) -> str:
        try:
            total_seconds = max(0, int(seconds))
            minutes = total_seconds // 60
            secs = total_seconds % 60
            return f"{minutes}:{secs:02d}"
        except Exception as e:
            logger.warning("_format_time caused an unexpected bug: %s", e)

    def _update_position_slider(self):
        try:
            if self._dragging_position:
                return

            full_time, current_time = self.engine.get_time()

            full_time_int = max(0, int(full_time))
            current_time_int = min(int(current_time), full_time_int)

            self.position_slider.blockSignals(True)
            self.position_slider.setRange(0, full_time_int)
            self.position_slider.setValue(current_time_int)
            self.position_slider.blockSignals(False)

            self.time_label.setText(
                f"{self._format_time(current_time)} / {self._format_time(full_time)}"
            )

            self._update_lyrics_highlight()
        except Exception as e:
            logger.warning("_update_position_slider caused an unexpected bug: %s", e)

    def _position_slider_pressed(self):
        try:
            self._dragging_position = True
        except Exception as e:
            logger.warning("_position_slider_pressed caused an unexpected bug: %s", e)

    def _position_slider_released(self):
        try:
            value = self.position_slider.value()
            self.engine.set_time(value)

            self._dragging_position = False

            self.time_label.setText(
                f"{self._format_time(value)} / {self._format_time(self.position_slider.maximum())}"
            )

            QTimer.singleShot(300, self._update_position_slider)
        except Exception as e:
            logger.warning("_position_slider_released caused an unexpected bug: %s", e)

    def _get_current_song_name(self):
        try:
            artist, title, cover_path = self.engine.get_data()
            self.cover_path = cover_path
            pixmap = QPixmap(self.cover_path)
            self.label.setPixmap(pixmap)
            self._set_now_playing_info(artist, title)
            return f"{artist} - {title}"
        except Exception as e:
            logger.warning("_get_current_song_name caused an unexpected bug: %s", e)

    def _apply_preset_to_ui(self, data: Dict) -> None:
        try:
            self._loading_ui = True

            try:
                theme = data.get("theme", {})
                self.current_theme = DEFAULT_THEME.copy()
                self.current_theme.update(theme)
                apply_theme(QApplication.instance(), {"theme": self.current_theme})

                preset_dict = dict(data.get("preset", {}))
                valid = {k: v for k, v in preset_dict.items() if k in Preset.__dataclass_fields__}
                p = Preset(**valid)
                self.engine.preset = p
                self._restore_geometry(p.main_window_geometry)

                loaded_songs = data.get("songs", [])

                self.songs = {}
                self.song_list.clear()

                for path in loaded_songs:
                    if not path or not os.path.isfile(path):
                        continue

                    index = str(len(self.songs))
                    self.songs[index] = {"path": path}
                    self.song_list.addItem(os.path.basename(path))

                self.engine.stop()
                self.engine._current_media_path = None
                self.engine.play_order = []
                self.engine.play_order_pos = -1
                self.engine.history.clear()
                self.engine.recent_shuffle.clear()

                if self.songs:
                    self.current_song = max(0, min(p.current_song, len(self.songs) - 1))
                else:
                    self.current_song = 0

                self.engine.preset.current_song = self.current_song

                self.pause_btn.setText("Pause")

                saved_queue = data.get("preset", {}).get("queue", [])

                if isinstance(saved_queue, list):
                    self.engine.queue = [
                        int(i) for i in saved_queue
                        if str(i) in self.songs
                    ]
                else:
                    self.engine.queue = []

                self._fill_queue()
                self._refresh_queue_list()

                widgets_to_block = [
                    self.mute_cb,
                    self.lyrics_window_cb,
                    self.lyrics_window_on_top_cb,
                    self.floating_lyrics_cb,
                    self.floating_lyrics_on_top_cb,
                    self.romaji_cb,
                    self.translated_cb,
                    self.shuffle_cb,
                    self.repeat_cb,

                    self.settings_mute_cb,
                    self.settings_lyrics_window_cb,
                    self.settings_lyrics_window_on_top_cb,
                    self.settings_floating_lyrics_cb,
                    self.settings_floating_lyrics_on_top_cb,
                    self.settings_romaji_cb,
                    self.settings_translated_cb,
                    self.settings_shuffle_cb,
                    self.settings_repeat_cb,
                    self.settings_normalize_audio_cb,

                    self.settings_online_lyrics_cb,
                    self.settings_download_lyrics_cb,
                    self.settings_MUSIXMATCH_USER_TOKEN_text,

                    self.volume_slider,
                    self.show_console_cb,
                    self.logging_level_drop,

                    self.library_sort_drop,
                    self.library_images_cb,
                ]

                for widget in widgets_to_block:
                    widget.blockSignals(True)

                self.show_console_cb.setChecked(bool(p.show_console))
                self.logging_level_drop.setCurrentIndex(int(p.logging_level))

                self.mute_cb.setChecked(bool(p.muted))
                self.settings_mute_cb.setChecked(bool(p.muted))
                self.lyrics_window_cb.setChecked(bool(p.lyrics_window))
                self.settings_lyrics_window_cb.setChecked(bool(p.lyrics_window))
                self.lyrics_window_on_top_cb.setChecked(bool(p.lyrics_window_on_top))
                self.settings_lyrics_window_on_top_cb.setChecked(bool(p.lyrics_window_on_top))
                self.floating_lyrics_cb.setChecked(bool(p.floating_lyrics))
                self.settings_floating_lyrics_cb.setChecked(bool(p.floating_lyrics))
                self.floating_lyrics_on_top_cb.setChecked(bool(p.floating_lyrics_on_top))
                self.settings_floating_lyrics_on_top_cb.setChecked(bool(p.floating_lyrics_on_top))
                self.shuffle_cb.setChecked(bool(p.shuffle))
                self.settings_shuffle_cb.setChecked(bool(p.shuffle))
                self.repeat_cb.setChecked(bool(p.repeat))
                self.settings_repeat_cb.setChecked(bool(p.repeat))
                self.volume_slider.setValue(int(p.volume))
                self._update_volume_label(int(p.volume))
                self.romaji_cb.setChecked(bool(p.romaji))
                self.settings_romaji_cb.setChecked(bool(p.romaji))
                self.translated_cb.setChecked(bool(p.translated))
                self.settings_translated_cb.setChecked(bool(p.translated))
                self.library_sort_drop.setCurrentIndex(p.library_sort_mode)
                self.library_images_cb.setChecked(bool(p.library_show_images))
                self.settings_normalize_audio_cb.setChecked(bool(p.normalize_audio))
                self.settings_online_lyrics_cb.setChecked(bool(p.online_lyrics))
                self.settings_download_lyrics_cb.setChecked(bool(p.download_lyrics))
                self.settings_MUSIXMATCH_USER_TOKEN_text.setText(str(p.MUSIXMATCH_USER_TOKEN))
                self.tab_order = p.tab_order

                for widget in widgets_to_block:
                    widget.blockSignals(False)

                self.toggle_console(bool(p.show_console))
                self._set_logging_level(int(p.logging_level))

                if self.song_list.count() > 0:
                    self._select_library_song_by_index(self.current_song)
                    self.setWindowTitle(
                        f"Yet Another Music Player — {self._get_current_preset_name()} — {self._get_current_song_name()}"
                    )
                else:
                    self._set_now_playing_info("Unknown Artist", "Nothing playing")
                    self.label.setPixmap(QPixmap(BLANK_PATH))
                    self.setWindowTitle(
                        f"Yet Another Music Player — {self._get_current_preset_name()}"
                    )
            
                if p.lyrics_window:
                    self.engine.lyrics.show_window()
                    self.engine.lyrics.set_lyrics_on_top(p.lyrics_window_on_top)

                if p.floating_lyrics:
                    self.engine.lyrics.show_floating_window()
                    self.engine.lyrics.set_floating_on_top(p.floating_lyrics_on_top)

                self.engine.online_lyrics = p.online_lyrics
                self.engine.preset.online_lyrics = p.online_lyrics
                self.engine.download_lyrics = p.download_lyrics
                self.engine.preset.download_lyrics = p.download_lyrics
                self.engine.preset.normalize_audio = p.normalize_audio
                self.engine.normalize_audio = p.normalize_audio

                self.engine.lyrics.MUSIXMATCH_USER_TOKEN = p.MUSIXMATCH_USER_TOKEN
                self._update_tab_order()
                QTimer.singleShot(100, self._library_settings_changed)
                QTimer.singleShot(300, self._fill_queue)

            finally:
                self._loading_ui = False

            self._apply_ui_to_engine()
        except Exception as e:
            logger.warning("_apply_preset_to_ui caused an unexpected bug: %s", e)

    def _apply_ui_to_engine(self) -> None:
        try:
            if getattr(self, "_loading_ui", False):
                return
            try:
                sender = self.sender()
                obj = sender.text()
                logger.debug(f"{obj} Changed")
            except:
                pass
            p = self.engine.preset
            p.show_console = self.show_console_cb.isChecked()
            p.logging_level = self.logging_level_drop.currentIndex()
            self.engine.preset.logging_level = self.logging_level_drop.currentIndex()
            p.muted = self.mute_cb.isChecked()
            p.lyrics_window = self.lyrics_window_cb.isChecked()
            p.lyrics_window_on_top = self.lyrics_window_on_top_cb.isChecked()
            p.floating_lyrics = self.floating_lyrics_cb.isChecked()
            p.floating_lyrics_on_top = self.floating_lyrics_on_top_cb.isChecked()
            p.shuffle = self.shuffle_cb.isChecked()
            p.repeat = self.repeat_cb.isChecked()
            p.current_song = self.current_song
            p.volume = self.volume_slider.value()
            p.romaji = self.romaji_cb.isChecked()
            p.translated = self.translated_cb.isChecked()
            p.queue = list(self.engine.queue)
            p.normalize_audio = self.settings_normalize_audio_cb.isChecked()
            p.online_lyrics = self.settings_online_lyrics_cb.isChecked()
            p.download_lyrics = self.settings_download_lyrics_cb.isChecked()
            p.MUSIXMATCH_USER_TOKEN = self.settings_MUSIXMATCH_USER_TOKEN_text.text()
            p.tab_order = self.tab_order

            self.engine.online_lyrics = p.online_lyrics
            self.engine.download_lyrics = p.download_lyrics
            self.engine.normalize_audio = p.normalize_audio
            self.engine.set_shuffle(p.shuffle)
            self.engine.set_repeat(p.repeat)
            self.engine.set_muted(p.muted)
            self.engine.volume(p.volume)

            self.engine.lyrics.set_lyrics(p.lyrics_window)
            self.engine.lyrics.set_floating(p.floating_lyrics)

            if p.lyrics_window:
                self.engine.lyrics.set_lyrics_on_top(p.lyrics_window_on_top)

            if p.floating_lyrics:
                self.engine.lyrics.set_floating_on_top(p.floating_lyrics_on_top)

            logger.debug("🟣 Settings changed/applied")
            self._autosave_current_preset()
        except Exception as e:
            logger.warning("_apply_ui_to_engine caused an unexpected bug: %s", e)

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            try:
                self._save_all_window_positions()
                self._save_current_preset_silent()
                self.engine.stop()

                if self.engine.lyrics.window is not None:
                    self.engine.lyrics.window._force_close = True
                    self.engine.lyrics.window.close()
                    self.engine.lyrics.window = None

                if self.engine.lyrics.floating_window is not None:
                    self.engine.lyrics.floating_window._force_close = True
                    self.engine.lyrics.floating_window.close()
                    self.engine.lyrics.floating_window = None

            except Exception as e:
                logger.warning("🟡 Failed during exit cleanup: %s", e)

            super().closeEvent(event)
        except Exception as e:
            logger.warning("closeEvent caused an unexpected bug: %s", e)
#endregion


#region Theme
QSS_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-size: {normal_font_size}pt;
}}
QWidget#SongRowWidget {{
    background: transparent;
}}

/* Tabs */
QTabWidget::pane {{
    border: 0;
    background: transparent;
}}
QTabBar::tab {{
    background: {panel};
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-size: 14px;
    font-weight: 600;
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
QSlider {{
    background: transparent;
    border: none;
}}
QSlider::groove:horizontal {{
    height: 6px;
    border: none;
    background: transparent;
}}

QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 3px;
}}

QSlider::add-page:horizontal {{
    background: {slider_bg};
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

QListWidget#LyricsList {{
    background-color: transparent;
    border: 0;
    padding: 12px;
}}
QListWidget#LyricsList::item {{
    padding: 10px 8px;
    border-radius: 8px;
}}

QLabel {{
    color: {text};
    background-color: transparent;
    background: transparent;
}}

QLabel#SongTitle {{
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-size: {artist_font_size}pt;
    font-weight: 700;
    color: {text};
}}

QLabel#SongArtist {{
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-size: {lyrics_font_size}pt;
    font-weight: 600;
    color: {muted_text};
}}

QLabel#QueueRowTitle {{
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-weight: 600;
}}

QListWidget#SongList,
QListWidget#QueueList {{
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
}}

QListWidget#SongList::item,
QListWidget#QueueList::item {{
    font-family: "{title_font}", "{font}", "Spotify Mix UI", "Segoe UI", system-ui;
    font-weight: 600;
    padding: 0px;
}}

QLabel#LyricsLabel {{
    background-color: {lyrics_bg};
    color: {lyrics_text};
    border-radius: 10px;
    padding: 12px;
}}

QLabel#FloatingLyricsLabel {{
    background-color: {floating_lyrics_bg};
    color: {floating_lyrics_text};
    border-radius: 10px;
    padding: 12px;
}}
"""


DEFAULT_THEME = {
    "font": "Spotify Mix UI",
    "title_font": "Spotify Mix UI Title",
    "lyrics_en_font": "Segoe UI Variable",
    "lyrics_jp_font": "Noto Sans JP",
    "bg": "#0f1115",
    "text": "#e6e9ef",
    "muted_text": "#9aa4b2",

    "title_font_size": 15,
    "artist_font_size": 11,
    "lyrics_font_size": 12,
    "normal_font_size": 10,

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

    "lyrics_bg": "#1f2430",
    "lyrics_text": "#e6e9ef",

    "floating_lyrics_bg": "#1f2430",
    "floating_lyrics_text": "#e6e9ef"
}


def apply_theme(app: QApplication, settings: dict):
    try:
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
    except Exception as e:
        logger.warning("apply_theme caused an unexpected bug: %s", e)

def set_theme_value(self, key: str, value: str):
    try:
        if self.current_theme is None:
            self.current_theme = DEFAULT_THEME.copy()

        self.current_theme[key] = value

        if hasattr(self, "player"):
            self.player.current_theme = self.current_theme

        apply_theme(QApplication.instance(), {"theme": self.current_theme})

        if hasattr(self, "player") and hasattr(self.player, "_apply_title_font_to_song_text_widgets"):
            self.player._apply_title_font_to_song_text_widgets()
    except Exception as e:
        logger.warning("set_theme_value caused an unexpected bug: %s", e)
#endregion

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Player()
    w.show()

    def _load_everything_else():
        _load_auto_preset(w)
        if w.song_list.count() > 0:
            w._set_startup_loading_ui()
    QTimer.singleShot(0, _load_everything_else)
    assets_ready_bridge.ready.connect(w._on_assets_downloaded)
    threading.Thread(target=_download_missing_assets_then_notify, daemon=True).start()

    sys.exit(app.exec())
