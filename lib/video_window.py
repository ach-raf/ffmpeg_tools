import sys
import os
import time

from PyQt5.QtWidgets import QFileDialog, QMainWindow

from PyQt5.QtCore import QDir, Qt, QUrl, QDateTime, QTime
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
    QSpinBox,
    QDateTimeEdit,
    QTimeEdit,
)
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

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
VIDEO_FILTER = "Videos(*.mp4 *.mkv *.avi *.mov)"
SUB_FILTER = "Subtitle(*.srt *.ass *.sub)"
GIF_FILTER = "GIF(*.gif)"


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


class VideoWindow(QMainWindow):
    def __init__(self, app, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setFixedSize(640, 480)
        self.setWindowTitle(APP_NAME)

        self.media_info = media_info.MediaInfo()

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        video_widget = QVideoWidget()

        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play)

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
        self.label_file_location.move(100, 100)

        self.label_subtitle_location = QLabel("No subtitle has been selected", self)
        self.label_subtitle_location.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.label_subtitle_location.move(100, 100)

        self.label_audio_channel = QLabel("Audio channel: ", self)
        self.label_audio_channel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.audio_channel_select = QSpinBox()
        self.audio_channel_select.setRange(0, 99)
        self.audio_channel_select.valueChanged.connect(self.audio_channel_value_change)

        self.label_subtitle_channel = QLabel("Subtitle channel: ", self)
        self.label_subtitle_channel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self.subtitle_channel_select = QSpinBox()
        self.subtitle_channel_select.setRange(0, 99)
        self.subtitle_channel_select.valueChanged.connect(
            self.subtitle_channel_value_change
        )

        self.label_trim_start = QLabel("Trim start:", self)
        self.label_trim_start.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.label_trim_end = QLabel("Trim end:", self)
        self.label_trim_end.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.error_label = QLabel()
        self.error_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

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

        # Create FILE menu bar and add open and exit action
        file_menu_bar = self.menuBar()
        file_menu = file_menu_bar.addMenu("&File")
        # fileMenu.addAction(newAction)
        file_menu.addAction(open_video_action)
        file_menu.addAction(open_subtitle_action)
        file_menu.addAction(exit_action)

        # Create batch encoding action
        encoding_action = QAction("Encode mp4", self)
        encoding_action.setStatusTip("Encode all videos inside a folder")
        encoding_action.triggered.connect(self.batch_encode)

        # Create batch extract subtitles action
        extract_susbs_action = QAction("Extract subtitles", self)
        extract_susbs_action.setStatusTip("Extract all subtitles inside a folder")
        extract_susbs_action.triggered.connect(self.batch_extract_subs)

        # Create encoding menu bar and add encoding action
        encoding_menu_bar = self.menuBar()
        encoding_menu = encoding_menu_bar.addMenu("&Batch")
        # fileMenu.addAction(newAction)
        encoding_menu.addAction(encoding_action)
        encoding_menu.addAction(extract_susbs_action)

        # Create gif action
        to_gif_action = QAction("Convert to gif", self)
        to_gif_action.setStatusTip("Convert to gif")
        to_gif_action.triggered.connect(self.to_gif)

        # Create extract subs action
        extract_subs_action = QAction("Extract subtitle", self)
        extract_subs_action.setStatusTip("Extract subtitle")
        extract_subs_action.triggered.connect(self.extract_subtitle)

        # Create convert menu bar and add gif and extract_subs action
        encoding_menu_bar = self.menuBar()
        encoding_menu = encoding_menu_bar.addMenu("&Extra")
        encoding_menu.addAction(to_gif_action)
        encoding_menu.addAction(extract_subs_action)

        # Create trim_preset action
        trim_internal_preset_action = QAction("Trim internal preset", self)
        trim_internal_preset_action.setStatusTip("Trim internal preset")
        trim_internal_preset_action.triggered.connect(self.trim_internal_preset)

        trim_external_preset_action = QAction("Trim external preset", self)
        trim_external_preset_action.setStatusTip("Trim external preset")
        trim_external_preset_action.triggered.connect(self.trim_external_preset)

        # Create presets menu bar and add trim_preset action
        presets_menu_bar = self.menuBar()
        presets_menu = presets_menu_bar.addMenu("&Presets")
        presets_menu.addAction(trim_internal_preset_action)
        presets_menu.addAction(trim_external_preset_action)

        # creating trim start widget
        self.trim_start_date_time_edit = QTimeEdit(self)
        self.trim_start_date_time_edit.dateTimeChanged.connect(
            self.trim_start_value_change
        )
        self.trim_start_date_time_edit.setDisplayFormat("hh:mm:ss")
        # setting geometry
        self.trim_start_date_time_edit.setGeometry(100, 100, 150, 35)
        # setting date time to it
        # trim_start_date_time_edit.setDateTime(QDateTime(2020, 10, 10, 11, 30))
        # time
        time = QTime(0, 0, 0)
        # setting only time
        self.trim_start_date_time_edit.setTime(time)

        # creating trim end widget
        self.trim_end_date_time_edit = QTimeEdit(self)
        self.trim_end_date_time_edit.dateTimeChanged.connect(self.trim_end_value_change)
        self.trim_end_date_time_edit.setDisplayFormat("hh:mm:ss")
        self.trim_end_date_time_edit.setGeometry(100, 100, 150, 35)
        time = QTime(0, 0, 0)
        self.trim_end_date_time_edit.setTime(time)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.label_current_time)
        control_layout.addWidget(self.position_slider)
        control_layout.addWidget(self.label_duration_time)

        # Create layouts to place inside widget
        choices_first_row_horizontal_layout = QHBoxLayout()
        # choices_first_row_horizontal_layout.setSpacing(10)
        # choices_first_row_horizontal_layout.addStretch()
        choices_first_row_horizontal_layout.setContentsMargins(10, 1, 10, 1)
        choices_first_row_horizontal_layout.addWidget(self.label_trim_start)
        choices_first_row_horizontal_layout.addWidget(self.trim_start_date_time_edit)
        choices_first_row_horizontal_layout.addWidget(self.label_audio_channel)
        choices_first_row_horizontal_layout.addWidget(self.audio_channel_select)

        choices_second_row_horizontal_layout = QHBoxLayout()
        choices_second_row_horizontal_layout.setContentsMargins(10, 1, 10, 1)
        choices_second_row_horizontal_layout.addWidget(self.label_trim_end)
        choices_second_row_horizontal_layout.addWidget(self.trim_end_date_time_edit)

        choices_second_row_horizontal_layout.addWidget(self.label_subtitle_channel)
        choices_second_row_horizontal_layout.addWidget(self.subtitle_channel_select)

        channel_select_layout = QVBoxLayout()
        channel_select_layout.addLayout(choices_first_row_horizontal_layout)
        channel_select_layout.addLayout(choices_second_row_horizontal_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.label_file_location)
        layout.addWidget(self.label_subtitle_location)
        layout.addWidget(video_widget)
        layout.addLayout(control_layout)
        layout.addLayout(channel_select_layout)
        layout.addWidget(self.trim_start_date_time_edit)
        layout.addWidget(self.error_label)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.media_player.setVideoOutput(video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)

    def set_media(self):
        if self.media_info.file_location != "":
            self.media_player.setMedia(
                QMediaContent(QUrl.fromLocalFile(self.media_info.file_location))
            )
            self.play_button.setEnabled(True)
            self.label_file_location.setText(self.media_info.file_location)
            self.play()
            time.sleep(0.01)
            self.play()

            if os.path.isfile(f"{self.media_info.file_location[:-4]}.srt"):
                self.label_subtitle_location.setText(
                    f"{self.media_info.file_location[:-4]}.srt"
                )
                self.media_info.subtitle_location = (
                    f"{self.media_info.file_location[:-4]}.srt"
                )

    def browse_video(self):
        return QFileDialog.getOpenFileName(
            self, "Open Video", self.media_info.file_location, VIDEO_FILTER
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
        sys.exit(app.exec_())

    def play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def media_state_changed(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

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
        self.media_player.setPosition(position)

    def audio_channel_value_change(self, value):
        self.media_info.audio_channel = value

    def subtitle_channel_value_change(self, value):
        self.media_info.subtitle_channel = value

    def trim_start_value_change(self, value):
        self.media_info.trim_start = trim_time_format(value)
        print(f"{self.media_info.trim_start=}")

    def trim_end_value_change(self, value):
        self.media_info.trim_end = trim_time_format(value)
        print(f"{self.media_info.trim_end=}")

    def handle_error(self):
        self.play_button.setEnabled(False)
        self.error_label.setText("Error: " + self.media_player.errorString())

    def to_gif(self):
        _output = self.save_video(GIF_FILTER)

        _to_gif_thread = threading.Thread(
            target=encoding.to_gif, args=(self.media_info.file_location, _output)
        )
        _to_gif_thread.start()

    def extract_subtitle(self):
        _output = self.save_video(SUB_FILTER)

        _extract_subs_thread = threading.Thread(
            target=encoding.extract_subtitle,
            args=(
                self.media_info.file_location,
                _output,
                self.media_info.subtitle_channel,
            ),
        )
        _extract_subs_thread.start()

    def batch_encode(self):
        _media_folder = f"{self.select_folder()}"
        _batch_encode_thread = threading.Thread(
            target=encoding.batch_encode, args=(_media_folder,)
        )
        _batch_encode_thread.start()

    def batch_extract_subs(self):
        _media_folder = self.select_folder()
        _batch_extract_subs_thread = threading.Thread(
            target=encoding.batch_extract_susbs,
            args=(_media_folder, self.media_info.subtitle_channel),
        )
        _batch_extract_subs_thread.start()

    def trim_internal_preset(self):
        _output = self.save_video(VIDEO_FILTER)
        _subs_status = "internal"
        _trim_presets_thread = threading.Thread(
            target=encoding.trim_preset,
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
        """_output = self.save_video(VIDEO_FILTER)
        self.media_info.subtitle_location = self.select_subtitle()
        _subs_status = "external"
        _trim_presets_thread = threading.Thread(
            target=encoding.trim_preset,
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
        _trim_presets_thread.start()"""

        brows = self.browse_video()
        print(f"{brows=}")

        save = self.save_video()
        print(f"{save=}")
