import os
import subprocess
from shutil import copyfile
from datetime import datetime


# -------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
# -------------------------------------------------------------------------------

# path to ffmpeg bin
FFMPEG_PATH = os.path.join("C:\\", "ffmpeg", "bin", "ffmpeg")

# fonts directory
FONT_DIR = os.path.join("C:\\", "Windows", "Fonts")

SUPPORTED_MEDIA = ["mp4", "mkv", "avi", "mov"]

# Qdialogue filter
VIDEO_FILTER = "Videos(*.mp4 *.mkv *.avi *.mov)"

SUB_FILTER = "Subtitle(*.srt *.ass *.sub)"

# controls the quality of the encode
CRF_VALUE = "23"

# h.264 profile
PROFILE = "high"

# encoding speed:compression ratio
COMPRESSION_RATIO = "veryslow"

# current directory
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# ==============================================================================


def check_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def clean_text(_text):
    cleaned_text = (
        _text.lower()
        .strip()
        .replace(" ", "_")
        .replace("'", "")
        .replace("-", "")
        .replace(",", "_")
        .replace("__", "_")
        .replace("’", "'")
    )
    return cleaned_text


def encode_web_mp4(_input, _output):
    if _output:
        _output_base_path, _output_file_name = os.path.split(_output)
        _output_file_name = f"{_output_file_name[:len(_output_file_name) - 4]}.mp4"
        _output = os.path.join(_output_base_path, _output_file_name)
        # ffmpeg command to create an mp4 file that can be shared on the web, mobile...
        _encode_task = [
            FFMPEG_PATH,
            "-i",
            _input,
            "-map_metadata",
            "0",
            "-movflags",
            "use_metadata_tags",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-c:s",
            "mov_text",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "baseline",
            "-level",
            "3.0",
            "-crf",
            CRF_VALUE,
            "-preset",
            COMPRESSION_RATIO,
            "-vf",
            "scale=1280:-2",
            "-strict",
            "experimental",
            "-movflags",
            "+faststart",
            "-threads",
            "0",
            "-f",
            "mp4",
            _output,
        ]
        print("Processing encode_web_mp4")
        subprocess.run(_encode_task)
        print("Process encode_web_mp4 finished!")


def extract_subtitle(_input, _output, subtitle_channel=0):
    print(f"Extracting subtitle from {_input} at channel {subtitle_channel}")
    if _output:
        _extract_subtitle = [
            FFMPEG_PATH,
            # "-txt_format",
            # "text",
            "-i",
            _input,
            # "-vsync",
            "-map",
            f"0:s:{subtitle_channel}",
            f"{_output}",
        ]

        subprocess.run(_extract_subtitle)
        if os.path.exists(_output):
            print("Subtitle extracted!")
            return _output
        else:
            return ""


def to_gif(_input, _output):
    if _output:
        _task = [FFMPEG_PATH, "-i", _input, "-vf", "fps=30", "-loop", "0", _output]
        print("Starting gif conversion")
        subprocess.run(_task)
        print("Gif conversion done!")


def batch_encode(_media_folder):
    if _media_folder:
        _encoded_path = os.path.join(_media_folder, "encoded")
        if not os.path.exists(_encoded_path):
            os.makedirs(_encoded_path)
        directory = os.listdir(_media_folder)
        for filename in directory:
            if filename[-3:].lower() in SUPPORTED_MEDIA:
                _input = os.path.join(_media_folder, filename)
                _output = os.path.join(
                    _encoded_path, f"{filename[:len(filename) - 4]}.mp4"
                )
                encode_web_mp4(
                    _input,
                    _output,
                )
        print("Encoding done!")


def batch_extract_susbs(_media_folder, subtitle_channel=0):
    if _media_folder:
        directory = os.listdir(_media_folder)
        for filename in directory:
            if filename[-3:].lower() in SUPPORTED_MEDIA:
                _input = os.path.join(_media_folder, filename)
                _output = os.path.join(
                    _media_folder, f"{filename[:len(filename) - 4]}.ass"
                )
                extract_subtitle(_input, _output, subtitle_channel)
        print("Subtitle extraction done!")


def calculate_duration(_end_time, _start_time):
    _format = "%H:%M:%S"
    _duration = datetime.strptime(_end_time, _format) - datetime.strptime(
        _start_time, _format
    )
    return f"{int(_duration.total_seconds())}"


def trim_with_hard_subs(
    _start,
    _end,
    _video_input,
    _output,
    subs_input="",
    video_channel=0,
    audio_channel=0,
    subtitle_channel=0,
):
    """
    :param _start: time to start the cutting in this format HH:mm:ss.
    :param _end: time to end the cutting in this format HH:mm:ss.
    :param _video_input: path of the file to trim_with_hard_subs.
    :param subs_input: path of the subtitle file to burn, if external subs are available.
    :param _output: path and name of the new clip c:\clips\clip.mkv (same extension as input).
    :param video_channel: the default video stream is 0.
    :param audio_channel: the default audio stream is 0.
    :param subtitle_channel: the default subtitle stream is 0, if internal subs are available.
    :return: runs the ffmpeg command to trim_with_hard_subs the video and create the new clip.
    """
    _base_dir = os.path.split(_video_input)[0]
    _base_name = os.path.split(_video_input)[1]
    _temp_subtitle = "temp_subtitle.srt"
    if not subs_input:
        # internal subs
        _extract_subtitle = extract_subtitle(
            _video_input, _temp_subtitle, subtitle_channel
        )
    else:
        # external subs
        copyfile(subs_input, _temp_subtitle)

    trim_with_subs_task = [
        FFMPEG_PATH,
        "-ss",
        _start,
        "-to",
        _end,
        "-copyts",
        "-i",
        _video_input,
        #'-vf', f"subtitles={_temp_subtitle}:force_style='Fontsize=6'",
        "-vf",
        f"subtitles={_temp_subtitle}",
        "-map",
        f"0:v:{video_channel}",
        "-map",
        f"0:a:{audio_channel}",
        "-c:s",
        "copy",
        "-c:a",
        "copy",
        "-ss",
        _start,
        _output,
    ]

    print("Processing trim_with_hard_subs")
    subprocess.run(trim_with_subs_task)
    os.remove(_temp_subtitle)


def trim_duration(
    _start,
    _duration,
    _input,
    _output,
    video_channel=0,
    audio_channel=0,
    subtitle_channel=0,
):

    _trim_task = [
        FFMPEG_PATH,
        "-i",
        _input,
        "-ss",
        _start,
        "-t",
        _duration,
        "-map",
        f"0:v:{video_channel}",
        "-map",
        f"0:a:{audio_channel}",
        # '-map', f'0:s:{subtitle_channel}',
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-c:s",
        "mov_text",
        _output,
    ]
    print("Starting trim_duration")
    subprocess.run(_trim_task)


def get_video_duration(_input):
    """
    ffprobe command to get the duration of a video
    :param _input: video input
    :return: video duration as a float
    """
    _task = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        _input,
    ]
    result = subprocess.run(_task, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)


def fade(_input, _output, _video_duration):
    _fade_duration = 1
    _fade_start = _video_duration - _fade_duration

    _task = [
        FFMPEG_PATH,
        "-y",
        "-i",
        _input,
        "-vf",
        f"fade=t=out:st={_fade_start}:d={_fade_duration}",
        "-af",
        f"afade=t=out:st={_fade_start}:d={_fade_duration}",
        _output,
    ]
    print("Starting fade")
    subprocess.run(_task)


def trim_preset(
    _video_location,
    _subs_location,
    _output,
    _trim_start,
    _trim_end,
    _subs_status,
    _audio_channel=0,
    _subs_channel=0,
):
    """
    in order to optimise on time I trim_basic and encode normally
    with the -i flag after -ss and -to flag, but there is a bug that gives the wrong duration of the output clip
    the correct solution for now is to put the -i flag before -ss and -to, but this solution is slow
    (it reads the whole file instead of seeking to a certain timestamp)
    I found it best, if after the first _trim and encode I do a second trim_basic this time with the new trimmed clip
    instead of the original big file, so using -i flag before -ss and -to is minimal.
    to cut and fix the wrong duration
    """
    # the path of the file directory
    input_base_path, input_file_name = os.path.split(_video_location)

    # directory of the output
    output_base_path, output_file_name = os.path.split(_output)
    # filename of the output
    # output_file_name = clean_text(output_file_name)

    # path for the temporary trim_basic
    temp_trim_output = os.path.join(output_base_path, f"basic_{input_file_name}")

    if "external" in _subs_status:
        trim_with_hard_subs(
            _trim_start,
            _trim_end,
            _video_location,
            temp_trim_output,
            subs_input=_subs_location,
            audio_channel=_audio_channel,
        )
    else:
        trim_with_hard_subs(
            _trim_start,
            _trim_end,
            _video_location,
            temp_trim_output,
            audio_channel=_audio_channel,
            subtitle_channel=_subs_channel,
        )

    temp_mp4_output = os.path.join(output_base_path, f"encode_{output_file_name}")
    encode_web_mp4(temp_trim_output, temp_mp4_output)
    # clean temp file
    os.remove(temp_trim_output)

    video_duration = calculate_duration(_trim_end, _trim_start)

    temp_duration_output = os.path.join(
        output_base_path, f"duration_{output_file_name}"
    )
    trim_duration("00:00:00", video_duration, temp_mp4_output, temp_duration_output)
    # clean temp file
    os.remove(temp_mp4_output)

    _video_duration_seconds = int(get_video_duration(temp_duration_output))
    _output = clean_text(_output)
    fade(temp_duration_output, _output, _video_duration_seconds)

    os.remove(temp_duration_output)
    print("All Done!")


if __name__ == "__main__":
    print("This is a module, not a program")
