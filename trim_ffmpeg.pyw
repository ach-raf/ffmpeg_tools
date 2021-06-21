#!/usr/bin/env python

import sys
import os
import subprocess
import threading
import math
from shutil import copyfile
from datetime import datetime
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow
from PyQt5.QtCore import QObject, QThread, pyqtSignal

# -------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
# -------------------------------------------------------------------------------

SUPPORTED_MEDIA = ['mp4', 'mkv', 'avi', 'mov']
# controls the quality of the encode
CRF_VALUE = '23'

# h.264 profile
PROFILE = 'high'

# encoding speed:compression ratio
PRESET = 'veryslow'

# path to ffmpeg bin
FFMPEG_PATH = r'C:\ffmpeg\bin\ffmpeg'

# font dir
FONT_DIR = f'C:\Windows\Fonts'

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
main_gui = f'{BASE_PATH}\\trim.ui'


# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def time_format(_seconds, _minutes, _hours):
    _seconds = str(_seconds).zfill(2)
    _minutes = str(_minutes).zfill(2)
    _hours = str(_hours).zfill(2)

    return f'{_hours}:{_minutes}:{_seconds}'


def duration_format(_time):
    return time_format(_time.second(), _time.minute(), _time.hour())


def seconds_format(_seconds):
    _seconds = int(_seconds)
    minutes, seconds = divmod(_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return time_format(seconds, minutes, hours)


def calculate_duration(_end_time, _start_time):
    _format = '%H:%M:%S'
    _duration = datetime.strptime(_end_time, _format) - datetime.strptime(_start_time, _format)
    return f'{_duration}'


def get_video_duration(_input):
    """
    ffprobe command to get the duration of a video
    :param _input: video input
    :return: video duration as a float
    """
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         _input], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)


def extract_subtitle(_video_input, _output, subtitle_channel):
    _extract_subtitle = [FFMPEG_PATH,
                         '-txt_format', 'text',
                         '-i', _video_input,
                         '-map', f'0:s:{subtitle_channel}',
                         f'{_output}']
    
    print('Starting extract_subtitle')
    subprocess.run(_extract_subtitle)


def trim(_start, _end, _video_input, _output, video_channel=0, audio_channel=0):
    """
    :param _start: time to start the cutting in this format HH:mm:ss
    :param _end: time to end the cutting in this format HH:mm:ss
    :param _video_input: path of the file to _trim
    :param _output: path and name of the new clip c:\clips\clip.mkv
    :param video_channel: the default video stream is 0
    :param audio_channel: the default audio stream is 0
    :return: runs the ffmpeg command to _trim the video and create the new clip
    """
    # simple ffmpeg trim
    trim_task = [FFMPEG_PATH,
                 '-ss', _start,
                 '-to', _end,
                 '-copyts',
                 '-i', _video_input,
                 '-map', f'0:v:{video_channel}',
                 '-map', f'0:a:{audio_channel}',
                 '-c:a', 'copy',
                 '-ss', _start,
                 _output]

    print('Starting _trim')
    subprocess.run(trim_task)


def trim_external_subs(_start, _end, _video_input, _subs_input, _output, video_channel=0, audio_channel=0):
    """
    :param _start: time to start the cutting in this format HH:mm:ss
    :param _end: time to end the cutting in this format HH:mm:ss
    :param _video_input: path of the file to trim
    :param _subs_input: path of the subtitle file to burn
    :param _output: path and name of the new clip c:\clips\clip.mkv (same extension as input)
    :param video_channel: the default video stream is 0
    :param audio_channel: the default audio stream is 0
    :return: runs the ffmpeg command to trim the video and create the new clip
    """
    # ffmpeg command to trim and burn subtitles
    _base_dir = os.path.split(_video_input)[0]
    _base_name = os.path.split(_video_input)[1]
    copyfile(_subs_input, f'temp_{_base_name}')
    trim_task = [FFMPEG_PATH,
                 '-ss', _start,
                 '-to', _end,
                 '-copyts',
                 '-i', _video_input,
                 '-vf', f'subtitles=temp_{_base_name}',
                 '-map', f'0:v:{video_channel}',
                 '-map', f'0:a:{audio_channel}',
                 '-c:s', 'mov_text',
                 '-c:a', 'copy',
                 '-ss', _start,
                 _output]

    print('Starting trim_external_subs')
    subprocess.run(trim_task)
    os.remove(f'temp_{_base_name}')


def trim_internal_subs(_start, _end, _video_input, _output, video_channel=0, audio_channel=0,
                       subtitle_channel=0):
    """
    :param _start: time to start the cutting in this format HH:mm:ss
    :param _end: time to end the cutting in this format HH:mm:ss
    :param _video_input: path of the file to trim
    :param _output: path and name of the new clip c:\clips\clip.mkv (same extension as input)
    :param video_channel: the default video stream is 0
    :param audio_channel: the default audio stream is 0
    :param subtitle_channel: internal subtitle to burn, the default channel is 0
    :return: runs the ffmpeg command to trim the video and create the new clip
    """
    _base_dir = os.path.split(_video_input)[0]
    _base_name = os.path.split(_video_input)[1]

    _extract_subtitle = [FFMPEG_PATH,
                         '-txt_format', 'text',
                         '-i', _video_input,
                         '-map', f'0:s:{subtitle_channel}',
                         f'temp_subtitle.srt']

    trim_task = [FFMPEG_PATH,
                 '-ss', _start,
                 '-to', _end,
                 '-copyts',
                 '-i', _video_input,
                 '-vf', f'subtitles=temp_subtitle.srt',
                 '-map', f'0:v:{video_channel}',
                 '-map', f'0:a:{audio_channel}',
                 '-c:s', 'srt',
                 '-c:a', 'copy',
                 '-ss', _start,
                 _output]

    print('Starting trim_internal_subs')
    subprocess.run(_extract_subtitle)
    subprocess.run(trim_task)
    os.remove('temp_subtitle.srt')


def encode_web_mp4(_input, _output):
    # ffmpeg command to create an mp4 file that can be shared on the web, mobile...
    _encode_task = [FFMPEG_PATH,
                    '-i', _input,
                    '-map_metadata', '0',
                    '-movflags', 'use_metadata_tags',
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-c:s', 'mov_text',
                    '-pix_fmt', 'yuv420p',
                    '-profile:v', 'baseline',
                    '-level', '3.0',
                    '-crf', CRF_VALUE,
                    '-preset', PRESET,
                    '-vf', 'scale=1280:-2',
                    '-strict', 'experimental', '-movflags', '+faststart', '-threads', '0',
                    '-f', 'mp4', _output]
    print('Starting encode_web_mp4')
    subprocess.run(_encode_task)


def trim_duration(_start, _duration, _input, _output, video_channel=0, audio_channel=0, subtitle_channel=0):
    _trim_task = [FFMPEG_PATH,
                  '-i', _input,
                  '-ss', _start,
                  '-t', _duration,
                  '-map', f'0:v:{video_channel}',
                  '-map', f'0:a:{audio_channel}',
                  # '-map', f'0:s:{subtitle_channel}',
                  '-c:v', 'copy',
                  '-c:a', 'aac',
                  '-c:s', 'mov_text',
                  _output]
    print('Starting trim_duration')
    subprocess.run(_trim_task)


def fade(_input, _output, _video_duration):
    _fade_start = _video_duration - 2
    _fade_duration = 2

    _task = [FFMPEG_PATH, '-y',
             '-i', _input,
             '-vf', f'fade=t=out:st={_fade_start}:d={_fade_duration}',
             '-af', f'afade=t=out:st={_fade_start}:d={_fade_duration}',
             _output]
    print('Starting fade')
    subprocess.run(_task)


def to_gif(_input, _output):
    _task = [FFMPEG_PATH,
             '-i', _input,
             '-vf', 'fps=30',
             '-loop', '0',
             _output]
    print('Starting gif conversion')
    subprocess.run(_task)
    print('Gif conversion done!')


def folder_encode(_media_folder, _encoded_folder):
    if not os.path.exists(_encoded_folder):
        os.makedirs(_encoded_folder)
    directory = os.listdir(_media_folder)
    for filename in directory:
        if filename[-3:].lower() in SUPPORTED_MEDIA:
            encode_web_mp4(f'{_media_folder}\\{filename}', f'{_encoded_folder}\\{filename[:len(filename) - 4]}.mp4')


# Step 1: Create a worker class
class PresetWorker(QThread):
    def __init__(self, _video_location, _subs_location, _output, _start_time, _end_time, _subs_status, _audio_channel=0,
                 _subs_channel=0):
        super().__init__()
        self._video_location = _video_location
        self._subs_location = _subs_location
        self._output = _output
        self._start_time = _start_time
        self._end_time = _end_time
        self._subs_status = _subs_status
        self._audio_channel = _audio_channel
        self._subs_channel = _subs_channel

    def run(self):
        """Long-running task."""
        _my_presets(self._video_location, self._subs_location, self._output, self._start_time, self._end_time,
                    self._subs_status,
                    self._audio_channel, self._subs_channel)


def _my_presets(_video_location, _subs_location, _output, _start_time, _end_time, _subs_status,
                _audio_channel=0, _subs_channel=0
                ):
    """
    in order to optimise on time I trim and encode normally
    with the -i flag after -ss and -to flag, but there is a bug that gives the wrong duration of the output clip
    the correct solution for now is to put the -i flag before -ss and -to, but this solution is slow
    (it reads the whole file instead of seeking to a certain timestamp)
    I found it best, if after the first _trim and encode I do a second trim this time with the new trimmed clip
    instead of the original big file, so using -i flag before -ss and -to is minimal.
    to cut and fix the wrong duration
    """
    # the path of the file directory
    input_base_path = os.path.split(_video_location)[0]
    # the name of the file, because i'll be using the name i clean it
    input_file_name = os.path.split(_video_location)[1].lower().strip().replace(' ', '_') \
        .replace("'", '').replace('-', '')

    # the path that will be open when the save dialog shows
    _save_path = f'{input_base_path}\\{input_file_name[:-4]}'
    # shown extensions by the save dialog
    _filter = "Videos(*.mp4 *.mkv *.avi)"
    # this will open up a save dialog and the save path will be stored in _output
    # directory of the output
    output_base_path = os.path.split(_output)[0]
    # filename of the output
    output_file_name = os.path.split(_output)[1]
    # getting the time to start the trim from the gui interface
    start_time = duration_format(_start_time)
    # getting the time to end the trim from the gui interface
    end_time = duration_format(_end_time)
    # path for the temporary trim
    temp_trim_output = f'{output_base_path}/temp_{input_file_name}'
    if 'external' in _subs_status:
        trim_external_subs(start_time, end_time, _video_location, _subs_location, temp_trim_output,
                           audio_channel=_audio_channel)
    else:
        trim_internal_subs(start_time, end_time, _video_location, temp_trim_output,
                           audio_channel=_audio_channel,
                           subtitle_channel=_subs_channel)

    temp_mp4_output = f'{output_base_path}/temp_{output_file_name}'
    encode_web_mp4(temp_trim_output, temp_mp4_output)

    video_duration = calculate_duration(end_time, start_time)
    temp_duration_output = f'{output_base_path}/temp_duration_{output_file_name}'
    trim_duration('00:00:00', video_duration, temp_mp4_output, temp_duration_output)

    _video_duration_seconds = int(get_video_duration(temp_duration_output))
    fade(temp_duration_output, _output, _video_duration_seconds)

    os.remove(temp_trim_output)
    os.remove(temp_mp4_output)
    os.remove(temp_duration_output)
    print('All Done!')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()  # Call the inherited classes __init__ method
        _main_window = resource_path(main_gui)
        uic.loadUi(_main_window, self)  # Load the .ui file

        self.btn_subs_select.setEnabled(False)

        self.btn_video_select.clicked.connect(self.browse_video)
        self.btn_subs_select.clicked.connect(self.browse_subs)

        self.action_trim.triggered.connect(self._trim)
        self.action_to_gif.triggered.connect(self._to_gif)
        self.action_encode_web_mp4.triggered.connect(self._encode_web_mp4)
        self.action_encode_folder.triggered.connect(self._encode_folder)
        self.action_presets_external_subs.triggered.connect(self._external_trim)
        self.action_presets_internal_subs.triggered.connect(self._internal_trim)
        self.action_extract_subs.triggered.connect(self._extract_subs)

        self.video_location = ''
        self.subs_location = ''
        self.preset_thread = None
        self.show()  # Show the GUI

    def test(self):
        _output = QFileDialog.getSaveFileName(self, 'Save File', self.video_location)[0]
        _video_duration = int(get_video_duration(self.video_location))
        fade(self.video_location, _output, _video_duration)

    def browse_video(self):
        _filter = "Videos(*.mkv *.mp4 *.avi *.mov)"
        if sys.argv[1] is not None:
            self.video_location = sys.argv[1]
        else:
            self.video_location = QFileDialog.getOpenFileName(self, 'Open Video', '.',
                                                              _filter)[0]

        self.txt_video_location.setText(self.video_location)
        self.btn_subs_select.setEnabled(True)

    def browse_subs(self):
        _filter = "Subtitle(*.srt *.ass *.sub)"
        self.subs_location = QFileDialog.getOpenFileName(self, 'Open Video', self.video_location,
                                                         _filter)[0]

        self.txt_subs_location.setText(self.subs_location)

    def _to_gif(self):
        _output = QFileDialog.getSaveFileName(self, 'Save File', self.video_location)[0]
        to_gif(self.video_location, _output)

    def _extract_subs(self):
        _filter = "Subtitle(*.srt *.ass *.sub)"
        _output = QFileDialog.getSaveFileName(self, 'Save File', self.video_location[-4], _filter)[0]
        extract_subtitle(self.video_location, _output, 0)

    def _trim(self):
        _output = QFileDialog.getSaveFileName(self, 'Save File', self.video_location)[0]
        start_time = duration_format(self.start_time.time())
        end_time = duration_format(self.end_time.time())
        trim(start_time, end_time, self.video_location, _output)

    def _encode_web_mp4(self):
        _output = QFileDialog.getSaveFileName(self, 'Save File', self.video_location)[0]
        encode_web_mp4(self.video_location, _output)

    def _encode_folder(self):
        _output = QFileDialog.getExistingDirectory(self, 'Select directory', self.video_location)
        input_base_path = os.path.split(self.video_location)[0]
        _folder_thread = threading.Thread(target=folder_encode(input_base_path, _output),
                                          args=(input_base_path, _output))
        _folder_thread.start()

    def _external_trim(self):
        self.my_presets('external')

    def _internal_trim(self):
        self.my_presets('internal')

    def my_presets(self, _subs_status):
        # the path of the file directory
        input_base_path = os.path.split(self.video_location)[0]
        # the name of the file, because i'll be using the name i clean it
        input_file_name = os.path.split(self.video_location)[1].lower().strip().replace(' ', '_') \
            .replace("'", '').replace('-', '')

        # the path that will be open when the save dialog shows
        _save_path = f'{input_base_path}\\{input_file_name[:-4]}'
        # shown extensions by the save dialog
        _filter = "Videos(*.mp4 *.mkv *.avi)"
        # this will open up a save dialog and the save path will be stored in _output
        _output = QFileDialog.getSaveFileName(self, 'Save File', _save_path, _filter)[0]
        # empty the argv so that the user can select another file
        sys.argv[1] = None
        # getting the time to start the trim from the gui interface
        start_time = self.start_time.time()
        # getting the time to end the trim from the gui interface
        end_time = self.end_time.time()
        # getting the audio channel from the gui interface
        _audio_channel = int(self.txt_audio_channel.text())
        _subs_channel = int(self.txt_subs_channel.text())
        self.preset_thread = PresetWorker(self.video_location, self.subs_location, _output, start_time, end_time,
                                          _subs_status,
                                          _audio_channel=_audio_channel, _subs_channel=_subs_channel)
        self.preset_thread.start()


def main_app():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(main_window)
    widget.setWindowTitle('ffmpeg encoder')
    widget.setFixedWidth(340)
    widget.setFixedHeight(192)
    widget.show()
    sys.exit(app.exec_())


main_app()
