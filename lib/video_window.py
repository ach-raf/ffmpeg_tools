import sys
import os
import time
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMainWindow

from PySide6.QtCore import QDir, Qt, QUrl, QDateTime, QTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
    QSpinBox,
    QComboBox,
    QDateTimeEdit,
    QTimeEdit,
    QInputDialog,
)
from PySide6.QtGui import QIcon, QAction, QColor, QPalette


import datetime
import lib.media_info as media_info
import lib.encoding as encoding
import subprocess
import threading


# -------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
# -------------------------------------------------------------------------------
APP_NAME = "Ffmpeg encoder"
# Qdialogue filter
VIDEO_FILTER = "Videos(*.mp4 *.mkv *.avi *.mov *.gif *.3gp)"
SUB_FILTER = "Subtitle(*.srt *.ass *.sub)"
GIF_FILTER = "GIF(*.gif)"
IMAGE_FILTER = "Images(*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
AUDIO_FILTER = "Audio(*.wav *.mp3 *.flac *.aac *.ogg)"
PLAY_PAUSE_STATE = 0
# -------------------------------------------------------------------------------


def time_select_format(time):
    date_time = datetime.datetime.fromtimestamp(time / 1000.0)
    date_time = date_time.replace(hour=date_time.hour - 1)
    return f'{date_time.strftime("%H:%M:%S")}'


def trim_time_format(_date):
    _hours = str(_date.time().hour()).zfill(2)
    _minutes = str(_date.time().minute()).zfill(2)
    _seconds = str(_date.time().second()).zfill(2)

    return f"{_hours}:{_minutes}:{_seconds}"


def time_edit_format(_time):
    return QTime.fromString(_time, "HH:mm:ss")


def get_modern_stylesheet():
    """Returns a modern dark theme stylesheet for the application"""
    return """
    /* Main Window */
    QMainWindow {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    
    /* Menu Bar */
    QMenuBar {
        background-color: #252525;
        color: #E0E0E0;
        border-bottom: 1px solid #3A3A3A;
        padding: 4px;
        font-size: 13px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }
    
    QMenuBar::item:selected {
        background-color: #3A3A3A;
    }
    
    QMenuBar::item:pressed {
        background-color: #4A4A4A;
    }
    
    /* Menu Dropdown */
    QMenu {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        padding: 4px;
    }
    
    QMenu::item {
        padding: 8px 24px 8px 32px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #3A3A3A;
    }
    
    QMenu::separator {
        height: 1px;
        background-color: #3A3A3A;
        margin: 4px 8px;
    }
    
    /* Labels */
    QLabel {
        color: #E0E0E0;
        background-color: transparent;
        font-size: 13px;
    }
    
    /* File location labels - slightly muted */
    QLabel[class="file_info"] {
        color: #B0B0B0;
        font-size: 12px;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #3A3A3A;
        color: #E0E0E0;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        min-height: 32px;
    }
    
    QPushButton:hover {
        background-color: #4A4A4A;
    }
    
    QPushButton:pressed {
        background-color: #2A2A2A;
    }
    
    QPushButton:disabled {
        background-color: #2A2A2A;
        color: #808080;
    }
    
    /* Play/Pause Button */
    QPushButton[class="play_button"] {
        background-color: #0078D4;
        min-width: 40px;
        min-height: 40px;
        border-radius: 20px;
    }
    
    QPushButton[class="play_button"]:hover {
        background-color: #1084E0;
    }
    
    QPushButton[class="play_button"]:pressed {
        background-color: #006CBE;
    }
    
    /* Slider */
    QSlider::groove:horizontal {
        background-color: #3A3A3A;
        height: 6px;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background-color: #0078D4;
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }
    
    QSlider::handle:horizontal:hover {
        background-color: #1084E0;
        width: 20px;
        height: 20px;
        margin: -7px 0;
        border-radius: 10px;
    }
    
    QSlider::handle:horizontal:pressed {
        background-color: #006CBE;
    }
    
    QSlider::sub-page:horizontal {
        background-color: #0078D4;
        border-radius: 3px;
    }
    
    /* SpinBox */
    QSpinBox {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        min-width: 80px;
    }

    QSpinBox:hover {
        border-color: #4A4A4A;
    }

    QSpinBox:focus {
        border-color: #0078D4;
        background-color: #252525;
    }

    QSpinBox::up-button {
        background-color: #3A3A3A;
        border-top-right-radius: 6px;
        width: 20px;
        border-left: 1px solid #3A3A3A;
    }

    QSpinBox::up-button:hover {
        background-color: #4A4A4A;
    }

    QSpinBox::up-button:pressed {
        background-color: #2A2A2A;
    }

    QSpinBox::down-button {
        background-color: #3A3A3A;
        border-bottom-right-radius: 6px;
        width: 20px;
        border-left: 1px solid #3A3A3A;
    }

    QSpinBox::down-button:hover {
        background-color: #4A4A4A;
    }

    QSpinBox::down-button:pressed {
        background-color: #2A2A2A;
    }
    
    /* ComboBox */
    QComboBox {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        min-width: 200px;
    }

    QComboBox:hover {
        border-color: #4A4A4A;
    }

    QComboBox:focus {
        border-color: #0078D4;
        background-color: #252525;
    }

    QComboBox::drop-down {
        border: none;
        width: 30px;
        border-left: 1px solid #3A3A3A;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }

    QComboBox::drop-down:hover {
        background-color: #4A4A4A;
    }

    QComboBox QAbstractItemView {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        selection-background-color: #3A3A3A;
        selection-color: #E0E0E0;
        padding: 4px;
    }

    QComboBox QAbstractItemView::item {
        padding: 6px 12px;
        border-radius: 4px;
    }

    QComboBox QAbstractItemView::item:hover {
        background-color: #4A4A4A;
    }

    QComboBox QAbstractItemView::item:selected {
        background-color: #0078D4;
    }
    
    /* Time Edit / DateTime Edit */
    QTimeEdit, QDateTimeEdit {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        min-width: 120px;
    }
    
    QTimeEdit:hover, QDateTimeEdit:hover {
        border-color: #4A4A4A;
    }
    
    QTimeEdit:focus, QDateTimeEdit:focus {
        border-color: #0078D4;
        background-color: #252525;
    }
    
    QTimeEdit::up-button, QDateTimeEdit::up-button {
        background-color: #3A3A3A;
        border-top-right-radius: 6px;
        width: 20px;
        border-left: 1px solid #3A3A3A;
    }
    
    QTimeEdit::up-button:hover, QDateTimeEdit::up-button:hover {
        background-color: #4A4A4A;
    }
    
    QTimeEdit::down-button, QDateTimeEdit::down-button {
        background-color: #3A3A3A;
        border-bottom-right-radius: 6px;
        width: 20px;
        border-left: 1px solid #3A3A3A;
    }
    
    QTimeEdit::down-button:hover, QDateTimeEdit::down-button:hover {
        background-color: #4A4A4A;
    }
    
    /* Video Widget */
    QVideoWidget {
        background-color: #000000;
        border-radius: 8px;
        border: 1px solid #3A3A3A;
    }
    
    /* Central Widget */
    QWidget {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    
    /* Scrollbar (if needed) */
    QScrollBar:vertical {
        background-color: #252525;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #4A4A4A;
        min-height: 30px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #5A5A5A;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QScrollBar:horizontal {
        background-color: #252525;
        height: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #4A4A4A;
        min-width: 30px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #5A5A5A;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    
    /* Tooltip */
    QToolTip {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 4px;
        padding: 4px 8px;
    }
    
    /* Status Bar */
    QStatusBar {
        background-color: #252525;
        color: #E0E0E0;
        border-top: 1px solid #3A3A3A;
    }
    
    /* File Dialog styling (limited support) */
    QFileDialog {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    """


class VideoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setWindowTitle(APP_NAME)

        # Apply modern dark theme stylesheet
        self.setStyleSheet(get_modern_stylesheet())

        self.media_info = media_info.MediaInfo()

        self.video_player = QMediaPlayer()
        self.audio_player = QAudioOutput()
        self.video_player.setAudioOutput(self.audio_player)

        video_widget = QVideoWidget()

        # Create open action
        open_video_action = QAction(QIcon("open.png"), "&Open video", self)
        open_video_action.setShortcut("Ctrl+O")
        open_video_action.setStatusTip("Open video")
        open_video_action.triggered.connect(self.open_video)

        open_subtitle_action = QAction(QIcon("open.png"), "&Open subtitle", self)
        open_subtitle_action.setStatusTip("Open subtitle")
        open_subtitle_action.triggered.connect(self.open_subtitle)

        # Create exit action
        exit_action = QAction(QIcon("exit.png"), "&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.exit_call)

        menu_bar = self.menuBar()
        # add FILE menu and add open and exit action
        file_menu = menu_bar.addMenu("&File")
        # fileMenu.addAction(newAction)
        file_menu.addAction(open_video_action)
        file_menu.addAction(open_subtitle_action)
        file_menu.addAction(exit_action)

        # Create trim_menu_bar and add basic trim action
        trim_menu = menu_bar.addMenu("&Trim")

        # Create basic trim action
        trim_basic_action = QAction("Basic", self)
        trim_basic_action.setStatusTip("Basic trim")
        trim_basic_action.triggered.connect(self.trim_basic)

        trim_duration_action = QAction("Duration", self)
        trim_duration_action.setStatusTip("Trim with duration (in seconds)")
        trim_duration_action.triggered.connect(self.trim_duration)

        trim_menu.addAction(trim_basic_action)
        trim_menu.addAction(trim_duration_action)

        hard_subs_action = trim_menu.addMenu("With hard subtitles")
        hard_subs_action.setStatusTip("Trim with hard subtitles")

        trim_internal_subs_action = QAction("Internal subtitles", self)
        trim_internal_subs_action.setStatusTip("Internal subtitles")
        trim_internal_subs_action.triggered.connect(self.trim_with_internal_subs)

        trim_external_subs_action = QAction("External subtitles", self)
        trim_external_subs_action.setStatusTip("External subtitles")
        trim_external_subs_action.triggered.connect(self.trim_with_external_subs)

        hard_subs_action.addAction(trim_internal_subs_action)
        hard_subs_action.addAction(trim_external_subs_action)

        encode_menu = menu_bar.addMenu("&Encode")
        encode_menu.setStatusTip("Convert video to another format")

        # Create lossless encoding action
        lossless_action = QAction("Lossless MP4", self)
        lossless_action.setStatusTip("Lossless MP4")
        lossless_action.triggered.connect(self.lossless_mp4)

        encode_menu.addAction(lossless_action)

        web_mp4_action = QAction("Web MP4", self)
        web_mp4_action.setStatusTip("Sharable MP4 on the web")
        web_mp4_action.triggered.connect(self.encode_web_mp4)

        encode_menu.addAction(web_mp4_action)

        # Create batch encoding action
        encoding_action = QAction("Encode mp4", self)
        encoding_action.setStatusTip("Encode all videos inside a folder")
        encoding_action.triggered.connect(self.batch_encode)

        # Create batch extract subtitles action
        extract_susbs_action = QAction("Extract subtitles", self)
        extract_susbs_action.setStatusTip("Extract all subtitles inside a folder")
        extract_susbs_action.triggered.connect(self.batch_extract_subs)

        # Create encoding menu bar and add encoding action
        encoding_menu = menu_bar.addMenu("&Batch")
        # fileMenu.addAction(newAction)
        encoding_menu.addAction(encoding_action)
        encoding_menu.addAction(extract_susbs_action)

        encoding_menu = menu_bar.addMenu("&Extra")

        brun_subs_action = encoding_menu.addMenu("Burn subtitles")
        brun_subs_action.setStatusTip("Burn subtitles")

        brun_internal_subs_action = QAction("Internal subtitles", self)
        brun_internal_subs_action.setStatusTip("Internal subtitles")
        brun_internal_subs_action.triggered.connect(self.burn_internal_subs)

        burn_external_subs_action = QAction("External subtitles", self)
        burn_external_subs_action.setStatusTip("External subtitles")
        burn_external_subs_action.triggered.connect(self.burn_external_subs)

        brun_subs_action.addAction(brun_internal_subs_action)
        brun_subs_action.addAction(burn_external_subs_action)

        # Create gif action
        to_gif_action = QAction("Convert to gif", self)
        to_gif_action.setStatusTip("Convert to gif")
        to_gif_action.triggered.connect(self.to_gif)

        # Create extract subs action
        extract_subs_action = QAction("Extract subtitle", self)
        extract_subs_action.setStatusTip("Extract subtitle")
        extract_subs_action.triggered.connect(self.extract_subtitle)

        loop_video_action = QAction("Loop video", self)
        loop_video_action.setStatusTip("Loop video")
        loop_video_action.triggered.connect(self.loop_video)

        video_to_frames_action = QAction("Export Frames", self)
        video_to_frames_action.setStatusTip("Export Frames")
        video_to_frames_action.triggered.connect(self.export_frames)

        # Create convert menu bar and add gif and extract_subs action
        encoding_menu.addAction(to_gif_action)
        encoding_menu.addAction(extract_subs_action)
        encoding_menu.addAction(loop_video_action)
        encoding_menu.addAction(video_to_frames_action)

        # Create trim_preset action
        trim_internal_preset_action = QAction("Trim internal preset", self)
        trim_internal_preset_action.setStatusTip("Trim internal preset")
        trim_internal_preset_action.triggered.connect(self.trim_internal_preset)

        trim_external_preset_action = QAction("Trim external preset", self)
        trim_external_preset_action.setStatusTip("Trim external preset")
        trim_external_preset_action.triggered.connect(self.trim_external_preset)

        # Create presets menu bar and add trim_preset action
        presets_menu = menu_bar.addMenu("&Presets")
        presets_menu.addAction(trim_internal_preset_action)
        presets_menu.addAction(trim_external_preset_action)

        # Add extract audio action
        extract_audio_action = QAction("Extract Audio Only", self)
        extract_audio_action.setStatusTip("Extract audio from video")
        extract_audio_action.triggered.connect(self.extract_audio)
        encoding_menu.addAction(extract_audio_action)

        # Add image+audio to video action
        image_audio_to_video_action = QAction("Image + Audio to Video", self)
        image_audio_to_video_action.setStatusTip(
            "Create video from image and audio file"
        )
        image_audio_to_video_action.triggered.connect(self.image_audio_to_video)
        encoding_menu.addAction(image_audio_to_video_action)

        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play)
        self.play_button.setProperty("class", "play_button")

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)

        self.label_current_time = QLabel("00:00:00", self)
        self.label_current_time.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )

        self.label_duration_time = QLabel("00:00:00", self)
        self.label_duration_time.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )

        self.label_file_location = QLabel("No file has been selected", self)
        self.label_file_location.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.label_file_location.setProperty("class", "file_info")

        self.label_subtitle_location = QLabel("No subtitle has been selected", self)
        self.label_subtitle_location.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.label_subtitle_location.setProperty("class", "file_info")

        self.label_audio_channel = QLabel("Audio track: ", self)
        self.label_audio_channel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.audio_channel_select = QComboBox()
        self.audio_channel_select.currentIndexChanged.connect(
            self.audio_channel_value_change
        )

        self.label_subtitle_channel = QLabel("Subtitle track: ", self)
        self.label_subtitle_channel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.subtitle_channel_select = QComboBox()
        self.subtitle_channel_select.currentIndexChanged.connect(
            self.subtitle_channel_value_change
        )

        # Store track data for index mapping
        self.audio_tracks = []
        self.subtitle_tracks = []

        self.label_trim_start = QLabel("Trim start:", self)
        self.label_trim_start.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.label_trim_end = QLabel("Trim end:", self)
        self.label_trim_end.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.error_label = QLabel()
        self.error_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # creating trim start widget
        self.trim_start_date_time_edit = QTimeEdit(self)
        self.trim_start_date_time_edit.dateTimeChanged.connect(
            self.trim_start_value_change
        )
        self.trim_start_date_time_edit.setDisplayFormat("hh:mm:ss")
        time = QTime(0, 0, 0)
        self.trim_start_date_time_edit.setTime(time)

        # creating trim end widget
        self.trim_end_date_time_edit = QTimeEdit(self)
        self.trim_end_date_time_edit.dateTimeChanged.connect(self.trim_end_value_change)
        self.trim_end_date_time_edit.setDisplayFormat("hh:mm:ss")
        time = QTime(0, 0, 0)
        self.trim_end_date_time_edit.setTime(time)

        # Create buttons to set start and end times from current video position
        self.set_start_time_button = QPushButton("Set Start", self)
        self.set_start_time_button.setToolTip(
            "Set start time to current video position"
        )
        self.set_start_time_button.clicked.connect(self.set_start_time_from_position)
        self.set_start_time_button.setEnabled(False)

        self.set_end_time_button = QPushButton("Set End", self)
        self.set_end_time_button.setToolTip("Set end time to current video position")
        self.set_end_time_button.clicked.connect(self.set_end_time_from_position)
        self.set_end_time_button.setEnabled(False)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(12, 8, 12, 8)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.label_current_time)
        control_layout.addWidget(self.position_slider)
        control_layout.addWidget(self.label_duration_time)

        # Create layouts to place inside widget
        choices_first_row_horizontal_layout = QHBoxLayout()
        choices_first_row_horizontal_layout.setSpacing(12)
        choices_first_row_horizontal_layout.setContentsMargins(12, 8, 12, 8)
        choices_first_row_horizontal_layout.addWidget(self.label_trim_start)
        choices_first_row_horizontal_layout.addWidget(self.trim_start_date_time_edit)
        choices_first_row_horizontal_layout.addWidget(self.set_start_time_button)
        choices_first_row_horizontal_layout.addStretch()
        choices_first_row_horizontal_layout.addWidget(self.label_audio_channel)
        choices_first_row_horizontal_layout.addWidget(self.audio_channel_select)

        choices_second_row_horizontal_layout = QHBoxLayout()
        choices_second_row_horizontal_layout.setSpacing(12)
        choices_second_row_horizontal_layout.setContentsMargins(12, 8, 12, 8)
        choices_second_row_horizontal_layout.addWidget(self.label_trim_end)
        choices_second_row_horizontal_layout.addWidget(self.trim_end_date_time_edit)
        choices_second_row_horizontal_layout.addWidget(self.set_end_time_button)
        choices_second_row_horizontal_layout.addStretch()
        choices_second_row_horizontal_layout.addWidget(self.label_subtitle_channel)
        choices_second_row_horizontal_layout.addWidget(self.subtitle_channel_select)

        channel_select_layout = QVBoxLayout()
        channel_select_layout.addLayout(choices_first_row_horizontal_layout)
        channel_select_layout.addLayout(choices_second_row_horizontal_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.label_file_location)
        layout.addWidget(self.label_subtitle_location)
        layout.addWidget(video_widget)
        layout.addLayout(control_layout)
        layout.addLayout(channel_select_layout)
        layout.addWidget(self.error_label)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.video_player.setVideoOutput(video_widget)
        # self.media_player.stateChanged.connect(self.media_state_changed)
        self.video_player.positionChanged.connect(self.position_changed)
        self.video_player.durationChanged.connect(self.duration_changed)
        # self.media_player.error.connect(self.handle_error)

    def set_subtitle(self, subtitle_path):
        self.label_subtitle_location.setText(subtitle_path)
        self.media_info.subtitle_location = subtitle_path

    def check_and_set_subtitle(self):
        file_path = Path(self.media_info.file_location)
        base_name = file_path.with_suffix("")

        subtitle_extensions = [".srt", ".ass"]

        for extension in subtitle_extensions:
            subtitle_path = base_name.with_suffix(extension)
            if subtitle_path.exists():
                self.set_subtitle(str(subtitle_path))
                return

        self.label_subtitle_location.setText("No external subtitle found")

    def set_media(self):
        global PLAY_PAUSE_STATE
        if self.media_info.file_location != "":
            print(self.media_info.file_location)
            self.video_player.setSource(self.media_info.file_location)
            self.play_button.setEnabled(True)
            self.label_file_location.setText(self.media_info.file_location)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            PLAY_PAUSE_STATE = 0

            # Enable set time buttons when media is loaded
            self.set_start_time_button.setEnabled(True)
            self.set_end_time_button.setEnabled(True)

            # Load audio and subtitle tracks
            self.load_audio_tracks()
            self.load_subtitle_tracks()

            # self.video_player.setActiveSubtitleTrack(0)
            """for track in self.video_player.subtitleTracks():
                print(f"{track=}")"""

            self.check_and_set_subtitle()

    def browse_video(self):
        return QFileDialog.getOpenFileName(
            self,
            "Open Video",
            self.media_info.file_location,
            VIDEO_FILTER,
        )[0]

    def select_folder(self):
        return QFileDialog.getExistingDirectory(
            self,
            "Select directory",
            os.path.dirname(self.media_info.file_location),
        )

    def select_subtitle(self):
        return QFileDialog.getOpenFileName(
            self, "Select Subtitle", self.media_info.file_location, SUB_FILTER
        )[0]

    def select_image(self):
        return QFileDialog.getOpenFileName(self, "Select Image", "", IMAGE_FILTER)[0]

    def select_audio(self):
        return QFileDialog.getOpenFileName(self, "Select Audio", "", AUDIO_FILTER)[0]

    def save_video(self, _filters=VIDEO_FILTER):
        if self.media_info.file_location == "":
            print("No media selected")
            self.media_info.file_location = self.browse_video()
        return QFileDialog.getSaveFileName(
            self,
            "Save File",
            f"{self.media_info.file_location[:len(self.media_info.file_location) - 4]}",
            _filters,
        )[0]

    def open_video(self):
        self.media_info.file_location = self.browse_video()
        self.set_media()

    def open_subtitle(self):
        _result = self.select_subtitle()
        if _result:
            self.media_info.subtitle_location
            self.label_subtitle_location.setText(self.media_info.subtitle_location)

    def exit_call(self, app):
        sys.exit(app.exec())

    def play(self):
        global PLAY_PAUSE_STATE
        if PLAY_PAUSE_STATE % 2 == 0:
            self.video_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.video_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        PLAY_PAUSE_STATE += 1

    def set_current_time_slider(self, position):
        self.label_current_time.setText(f"{time_select_format(position)}")

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.set_current_time_slider(position)

    def duration_changed(self, duration):
        self.media_info.duration = duration
        self.position_slider.setRange(0, duration)
        _display_str = time_select_format(duration)

        self.label_duration_time.setText(_display_str)
        self.trim_end_date_time_edit.setTime(time_edit_format(_display_str))

    def set_position(self, position):
        self.video_player.setPosition(position)

    def load_audio_tracks(self):
        """Load audio tracks from the current video file and populate the combobox."""
        if not self.media_info.file_location:
            return

        self.audio_tracks = encoding.get_audio_tracks(self.media_info.file_location)
        self.audio_channel_select.clear()

        if self.audio_tracks:
            for track in self.audio_tracks:
                self.audio_channel_select.addItem(track["display_name"], track["index"])
            # Set default to first track
            self.audio_channel_select.setCurrentIndex(0)
            if self.audio_tracks:
                self.media_info.audio_channel = self.audio_tracks[0]["index"]
        else:
            # Fallback if no tracks found
            self.audio_channel_select.addItem("No audio tracks", 0)
            self.media_info.audio_channel = 0

    def load_subtitle_tracks(self):
        """Load subtitle tracks from the current video file and populate the combobox."""
        if not self.media_info.file_location:
            return

        self.subtitle_tracks = encoding.get_subtitle_tracks(
            self.media_info.file_location
        )
        self.subtitle_channel_select.clear()

        if self.subtitle_tracks:
            for track in self.subtitle_tracks:
                self.subtitle_channel_select.addItem(
                    track["display_name"], track["index"]
                )
            # Set default to first track
            self.subtitle_channel_select.setCurrentIndex(0)
            if self.subtitle_tracks:
                self.media_info.subtitle_channel = self.subtitle_tracks[0]["index"]
        else:
            # Fallback if no tracks found
            self.subtitle_channel_select.addItem("No subtitle tracks", 0)
            self.media_info.subtitle_channel = 0

    def audio_channel_value_change(self, index):
        """Handle audio track selection change."""
        if index >= 0:
            track_index = self.audio_channel_select.itemData(index)
            if track_index is not None:
                self.media_info.audio_channel = int(track_index)
                print(f"Selected audio track index: {track_index}")

    def subtitle_channel_value_change(self, index):
        """Handle subtitle track selection change."""
        if index >= 0:
            track_index = self.subtitle_channel_select.itemData(index)
            if track_index is not None:
                self.media_info.subtitle_channel = int(track_index)
                print(f"Selected subtitle track index: {track_index}")

    def trim_start_value_change(self, value):
        self.media_info.trim_start = trim_time_format(value)
        print(f"{self.media_info.trim_start=}")

    def trim_end_value_change(self, value):
        self.media_info.trim_end = trim_time_format(value)
        print(f"{self.media_info.trim_end=}")

    def set_start_time_from_position(self):
        """Set the start time to the current video position."""
        current_position = self.video_player.position()
        if current_position >= 0:
            # Convert position (milliseconds) to time string, then to QTime
            time_str = time_select_format(current_position)
            qtime = time_edit_format(time_str)
            self.trim_start_date_time_edit.setTime(qtime)
            # The value change will trigger trim_start_value_change automatically

    def set_end_time_from_position(self):
        """Set the end time to the current video position."""
        current_position = self.video_player.position()
        if current_position >= 0:
            # Convert position (milliseconds) to time string, then to QTime
            time_str = time_select_format(current_position)
            qtime = time_edit_format(time_str)
            self.trim_end_date_time_edit.setTime(qtime)
            # The value change will trigger trim_end_value_change automatically

    def handle_error(self):
        self.play_button.setEnabled(False)
        self.error_label.setText("Error: " + self.video_player.errorString())

    def to_gif(self):
        _output = self.save_video(GIF_FILTER)
        if _output:
            _to_gif_thread = threading.Thread(
                target=encoding.to_gif,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            _to_gif_thread.start()

    def extract_subtitle(self):
        if self.media_info.file_location == "":
            print("No media selected")
            self.media_info.file_location = self.browse_video()

        if not self.media_info.file_location:
            return

        # Automatically infer subtitle format
        subtitle_format = encoding.get_subtitle_format(
            self.media_info.file_location, self.media_info.subtitle_channel
        )

        # Create filter based on detected format
        if subtitle_format:
            subtitle_filter = f"Subtitle(*.{subtitle_format})"
            # Create default filename with correct extension
            input_path = Path(self.media_info.file_location)
            default_filename = f"{input_path.stem}.{subtitle_format}"
        else:
            # Fallback to generic filter if format detection fails
            subtitle_filter = SUB_FILTER
            input_path = Path(self.media_info.file_location)
            default_filename = f"{input_path.stem}.srt"

        # Get save location with inferred format
        _output = QFileDialog.getSaveFileName(
            self,
            "Save Subtitle File",
            str(Path(self.media_info.file_location).parent / default_filename),
            subtitle_filter,
        )[0]

        if _output:
            _extract_subs_thread = threading.Thread(
                target=encoding.extract_subtitle,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.subtitle_channel,
                ),
            )
            _extract_subs_thread.start()

    def get_number_of_loops(self):
        _num_of_loops, result = QInputDialog.getInt(
            self, "Number of loops", "How many loop:"
        )
        if result:
            self.number_of_loops = str(_num_of_loops - 1)
            return True
        return False

    def get_duration_wanted(self):
        _duration, result = QInputDialog.getInt(
            self, "Duration after start time", "How many seconds:"
        )
        if result:
            self.trim_duration_in_seconds = str(_duration)
            return True
        return False

    def loop_video(self):
        _output = self.save_video(VIDEO_FILTER)
        _mp4_temp_path = "converting_to_mp4.mp4"
        _gif_flag = False
        if _output:
            _get_time = self.get_number_of_loops()
            if _get_time:
                if "gif" in self.media_info.file_location:
                    _gif_flag = True
                    encoding.gif_to_mp4(self.media_info.file_location, _mp4_temp_path)
                if _gif_flag:
                    self.media_info.file_location = _mp4_temp_path
                _loop_video_thread = threading.Thread(
                    target=encoding.loop_video,
                    args=(
                        self.media_info.file_location,
                        _output,
                        self.number_of_loops,
                        _gif_flag,
                        self.media_info.trim_start,
                        self.media_info.trim_end,
                    ),
                )
                _loop_video_thread.start()

    def export_frames(self):
        _media_folder = f"{self.select_folder()}"
        if _media_folder:
            _export_frames_thread = threading.Thread(
                target=encoding.video_to_frames,
                args=(
                    self.media_info.file_location,
                    _media_folder,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            _export_frames_thread.start()

    def lossless_mp4(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            _lossless_mp4_thread = threading.Thread(
                target=encoding.lossless_mp4,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            _lossless_mp4_thread.start()

    def encode_web_mp4(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            _encode_web_mp4_thread = threading.Thread(
                target=encoding.encode_web_mp4,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            _encode_web_mp4_thread.start()

    def batch_encode(self):
        _media_folder = f"{self.select_folder()}"
        if _media_folder:
            _batch_encode_thread = threading.Thread(
                target=encoding.batch_encode, args=(_media_folder,)
            )
            _batch_encode_thread.start()

    def batch_extract_subs(self):
        _media_folder = self.select_folder()
        if _media_folder:
            _batch_extract_subs_thread = threading.Thread(
                target=encoding.batch_extract_subtitles,
                args=(_media_folder, self.media_info.subtitle_channel),
            )
            _batch_extract_subs_thread.start()

    def trim_internal_preset(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            _subs_status = "internal"
            _trim_presets_thread = threading.Thread(
                target=encoding.trim_preset_new,
                args=(
                    self.media_info.file_location,
                    self.media_info.subtitle_location,
                    _output,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                    _subs_status,
                    self.media_info.audio_channel,
                    self.media_info.subtitle_channel,
                ),
            )
            _trim_presets_thread.start()

    def trim_external_preset(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            self.media_info.subtitle_location = self.select_subtitle()
            _subs_status = "external"
            _trim_presets_thread = threading.Thread(
                target=encoding.trim_preset_new,
                args=(
                    self.media_info.file_location,
                    self.media_info.subtitle_location,
                    _output,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                    _subs_status,
                    self.media_info.audio_channel,
                    self.media_info.subtitle_channel,
                ),
            )
            _trim_presets_thread.start()

    def trim_basic(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            _basic_trim_thread = threading.Thread(
                target=encoding.trim_basic,
                args=(
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                    self.media_info.file_location,
                    _output,
                    self.media_info.video_channel,
                    self.media_info.audio_channel,
                ),
            )
            _basic_trim_thread.start()

    def trim_duration(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            _result = self.get_duration_wanted()
            if _result:
                _trim_duration_thread = threading.Thread(
                    target=encoding.trim_duration,
                    args=(
                        self.media_info.trim_start,
                        self.trim_duration_in_seconds,
                        self.media_info.file_location,
                        _output,
                        self.media_info.video_channel,
                        self.media_info.audio_channel,
                    ),
                )
                _trim_duration_thread.start()

    def trim_with_internal_subs(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            trim_with_internal_subs_thread = threading.Thread(
                target=encoding.trim_with_hard_subs,
                args=(
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                    self.media_info.file_location,
                    _output,
                    self.media_info.video_channel,
                    self.media_info.audio_channel,
                    self.media_info.subtitle_channel,
                ),
            )
            trim_with_internal_subs_thread.start()

    def trim_with_external_subs(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            if not self.media_info.subtitle_location:
                self.media_info.subtitle_location = self.select_subtitle()
            trim_with_internal_subs_thread = threading.Thread(
                target=encoding.trim_with_hard_subs,
                args=(
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                    self.media_info.file_location,
                    _output,
                    self.media_info.video_channel,
                    self.media_info.audio_channel,
                    self.media_info.subtitle_channel,
                    self.media_info.subtitle_location,
                ),
            )
            trim_with_internal_subs_thread.start()

    def burn_internal_subs(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            burn_internal_subs_thread = threading.Thread(
                target=encoding.burn_subtitles,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.subtitle_channel,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            burn_internal_subs_thread.start()

    def burn_external_subs(self):
        _output = self.save_video(VIDEO_FILTER)
        if _output:
            if not self.media_info.subtitle_location:
                self.media_info.subtitle_location = self.select_subtitle()
            burn_external_subs_thread = threading.Thread(
                target=encoding.burn_subtitles,
                args=(
                    self.media_info.file_location,
                    _output,
                    self.media_info.subtitle_location,
                    self.media_info.trim_start,
                    self.media_info.trim_end,
                ),
            )
            burn_external_subs_thread.start()

    def extract_audio(self):
        output_path = self.save_video(_filters="Audio Files (*.mp3 *.wav *.ogg)")
        if output_path:
            encoding.extract_audio(
                self.media_info.file_location,
                output_path,
                self.media_info.trim_start,
                self.media_info.trim_end,
            )

    def image_audio_to_video(self):
        # Select image file
        image_path = self.select_image()
        if not image_path:
            return

        # Select audio file
        audio_path = self.select_audio()
        if not audio_path:
            return

        # Select output video file
        output_path = self.save_video(VIDEO_FILTER)
        if not output_path:
            return

        # Start conversion in a separate thread
        image_audio_thread = threading.Thread(
            target=encoding.image_audio_to_video,
            args=(image_path, audio_path, output_path),
        )
        image_audio_thread.start()
