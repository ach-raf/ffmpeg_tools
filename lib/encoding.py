import os
import json
import subprocess
from shutil import copyfile
from datetime import datetime
from pathlib import Path

# -------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
# -------------------------------------------------------------------------------

# path to ffmpeg bin
FFMPEG_PATH = Path("C:\\", "ffmpeg", "bin", "ffmpeg")

FFPROBE_PATH = Path("C:\\", "ffmpeg", "bin", "ffprobe")

# fonts directory
FONT_DIR = Path("C:\\", "Windows", "Fonts")

SUPPORTED_MEDIA = ["mp4", "mkv", "avi", "mov"]

# Qdialogue filter
VIDEO_FILTER = "Videos(*.mp4 *.mkv *.avi *.mov)"

SUB_FILTER = "Subtitle(*.srt *.ass *.sub)"

# controls the quality of the encode
CRF_VALUE = "23"

# h.264 profile
# baseline, main, high
PROFILE = "baseline"

# encoding speed:compression ratio
# veryslow, slower, slow, medium, fast, faster, veryfast, superfast, ultrafast
COMPRESSION_RATIO = "veryslow"

# current directory
CURRENT_DIR_PATH = Path(__file__).resolve().parent

ROOT_DIRECTORY = CURRENT_DIR_PATH.parent
# ==============================================================================


def check_directory_exists(path):
    path = Path(path)
    if not path.exists():
        path.mkdir()


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


def get_video_duration(video_file: str) -> float:
    """
    Gets the duration of a video file using ffprobe.

    Args:
    video_file (str): Path to the video file.

    Returns:
    float: Duration of the video in seconds.
    """
    try:
        # Construct the command to get the video duration using ffprobe
        command = [
            FFPROBE_PATH,
            "-v",
            "error",  # Hide any warnings
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_file,
        ]

        # Execute the command
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        # Parse the output to get the duration
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while getting video duration: {e}")
        return 0.0
    except ValueError as e:
        print(f"Could not convert duration to float: {e}")
        return 0.0


def get_subtitle_format(input_file: str, subtitle_stream_index=0) -> str:
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-select_streams",
        f"s:{subtitle_stream_index}",
        input_file,
    ]

    try:
        result = subprocess.run(
            ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        stream_info = json.loads(result.stdout)["streams"][0]
        codec_name = stream_info["codec_name"]

        if codec_name == "ass":
            return "ass"
        elif codec_name == "subrip":
            return "srt"
        else:
            return codec_name
    except (subprocess.CalledProcessError, IndexError, json.JSONDecodeError):
        return None


def calculate_duration(_end_time, _start_time):
    _format = "%H:%M:%S"
    _duration = datetime.strptime(_end_time, _format) - datetime.strptime(
        _start_time, _format
    )
    return f"{int(_duration.total_seconds())}"


def lossless_mp4(_input, _output):
    _lossless_mp4_task = [
        FFMPEG_PATH,
        "-i",
        _input,
        "-c:v",
        "libx264",
        # ☻"-qp",
        # "0",
        "-c:a",
        "aac",
        _output,
    ]
    print("Processing lossless_mp4")
    subprocess.run(_lossless_mp4_task)
    print("Process lossless_mp4 finished!")


def encode_web_mp4(input_file: Path, output_file: Path):
    # Ensure the output file has the correct .mp4 extension
    output_file_name = f"{output_file.stem}.mp4"
    output_file = output_file.with_name(output_file_name)

    # ffmpeg command to create an mp4 file that can be shared on the web, mobile...
    encode_task = [
        FFMPEG_PATH,
        "-i",
        str(input_file),
        "-map_metadata",
        "0",
        "-movflags",
        "use_metadata_tags",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-ac",
        "2",  # Ensure stereo audio
        "-ar",
        "48000",  # Set audio sample rate
        "-b:a",
        "192k",  # Set audio bitrate
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        PROFILE,
        "-level",
        "3.0",
        "-crf",
        CRF_VALUE,
        "-preset",
        COMPRESSION_RATIO,
        "-vf",
        "scale=1280:-2",
        "-movflags",
        "+faststart",
        "-threads",
        "0",
        "-f",
        "mp4",
        str(output_file),
    ]

    print("Processing encode_web_mp4")
    try:
        subprocess.run(encode_task, check=True)
        print("Process encode_web_mp4 finished!")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        raise


def extract_subtitle(_input, _output, subtitle_channel=0):
    print(f"Extracting subtitle from {_input} at channel {subtitle_channel}")
    _output = Path(_output)
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
            f"{_output.absolute().as_posix()}",
        ]

        subprocess.run(_extract_subtitle)
        if _output.is_file():
            print("Subtitle extracted!")
            print(f"Subtitle saved at {_output.absolute().as_posix()}")
            return _output.absolute().as_posix()
        else:
            return None


def burn_subtitles(_input, _output, _subtitle_path):
    _subtitle_path = Path(_subtitle_path)
    
    if not _subtitle_path.exists():
        print(f"Error: Subtitle file not found: {_subtitle_path}")
        return
    
    # Convert paths to strings and ensure proper format
    input_path = str(_input)
    output_path = str(_output)
    subtitle_file = str(_subtitle_path.absolute())
    
    # Use filter_complex with proper path escaping for Windows
    # Replace backslashes with forward slashes and escape special characters
    escaped_subtitle_path = subtitle_file.replace('\\', '/').replace(':', '\\:')
    
    _task = [
        str(FFMPEG_PATH),
        "-i",
        input_path,
        "-filter_complex",
        f"[0:v]subtitles='{escaped_subtitle_path}'[v]",
        "-map",
        "[v]",
        "-map",
        "0:a?",
        "-preset",
        str(COMPRESSION_RATIO),
        "-c:a",
        "copy",
        output_path,
    ]
    print(f"Burning subtitles from: {_subtitle_path}")
    print("Starting burn_subtitles")
    try:
        subprocess.run(_task, check=True)
        print("Subtitles burned!")
    except subprocess.CalledProcessError as e:
        print(f"Error burning subtitles: {e}")
        raise


def to_gif(_input, _output):
    if _output:
        _task = [FFMPEG_PATH, "-i", _input, "-vf", "fps=30", "-loop", "0", _output]
        print("Starting gif conversion")
        subprocess.run(_task)
        print("Gif conversion done!")


def gif_to_mp4(_input, _output):
    if _output:
        _task = [
            FFMPEG_PATH,
            "-i",
            _input,
            "-movflags",
            "faststart",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            _output,
        ]
        print("Starting gif_to_mp4")
        subprocess.run(_task)
        print("gif_to_mp4 done!")


def loop_video(_input, _output, _number_of_loops, _gif_flag=False):
    _task = [
        FFMPEG_PATH,
        "-stream_loop",
        _number_of_loops,
        "-i",
        _input,
        "-c",
        "copy",
        _output,
    ]
    print("Starting loop_video")
    subprocess.run(_task)
    print("loop_video done!")
    if _gif_flag:
        os.remove(_input)


def video_to_frames(_input, _output):
    _task = [
        FFMPEG_PATH,
        "-i",
        _input,
        f"{os.path.join(_output, 'out-%03d.png')}",
    ]
    print("Starting video_to_frames")
    subprocess.run(_task)
    print("video_to_frames done!")


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


def batch_extract_subtitles(media_folder: str, subtitle_channel: int = 0) -> None:
    if media_folder:
        media_path = Path(media_folder)
        for file_path in media_path.iterdir():
            if file_path.suffix[1:].lower() in SUPPORTED_MEDIA:
                subtitle_extension = get_subtitle_format(file_path, subtitle_channel)
                output_path = media_path / f"{file_path.stem}.{subtitle_extension}"
                print("Processing batch extract subtitles...")
                extract_subtitle(file_path, output_path, subtitle_channel)
        print("Batch extract subtitles done!")


def trim_basic(_start, _end, _video_input, _output, video_channel=0, audio_channel=0):
    """
    :param _start: time to start the cutting in this format HH:mm:ss
    :param _end: time to end the cutting in this format HH:mm:ss
    :param _video_input: path of the file to _trim
    :param _output: path and name of the new clip c:\clips\clip.mkv
    :param video_channel: the default video stream is 0
    :param audio_channel: the default audio stream is 0
    :return: runs the ffmpeg command to _trim the video and create the new clip
    """
    # simple ffmpeg trim_basic
    trim_task = [
        FFMPEG_PATH,
        "-ss",
        _start,
        "-to",
        _end,
        "-copyts",
        "-i",
        _video_input,
        "-map",
        f"0:v:{video_channel}?",
        "-map",
        f"0:a:{audio_channel}?",
        "-c:a",
        "copy",
        "-ss",
        _start,
        _output,
    ]

    print("Processing trim basic...")
    subprocess.run(trim_task)
    print("Trim basic done!")


def trim_with_hard_subs(
    _start,
    _end,
    _video_input,
    _output,
    video_channel=0,
    audio_channel=0,
    subtitles_channel=0,
    subtitles_path=None,
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

    _temp_subtitle = f"{_output[:len(_output)-4]}.srt"
    _temp_subtitle = Path(_temp_subtitle)

    if not subtitles_path:
        # internal subs
        subtitles_path = extract_subtitle(
            _video_input, _temp_subtitle.absolute().as_posix(), subtitles_channel
        )
    else:
        # external subs
        copyfile(subtitles_path, _temp_subtitle.absolute().as_posix())

    # Convert to forward slashes which FFmpeg handles well on Windows
    _subtitles_filter_path = str(_temp_subtitle.absolute()).replace("\\", "/")
    print(f"{_subtitles_filter_path=}")
    trim_with_subs_task = [
        FFMPEG_PATH,
        "-ss",
        _start,
        "-to",
        _end,
        "-copyts",
        "-i",
        _video_input,
        "-vf",
        f"subtitles='{_subtitles_filter_path}'",
        "-map",
        f"0:v:{video_channel}?",
        "-map",
        f"0:a:{audio_channel}?",
        # Convert 5.1 audio to stereo
        "-ac",
        "2",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-ar",
        "48000",
        "-ss",
        _start,
        _output,
    ]

    print("Processing trim with hard subs")
    subprocess.run(trim_with_subs_task)
    os.remove(_temp_subtitle)
    print("Trim with hard subs done!")


def trim_duration(
    start: str,
    duration: str,
    input_file: str,
    output_file: str,
    video_channel: int = 0,
    audio_channel: int = 0,
    subtitle_channel: int = 0,
):
    """
    Trims a video file to the specified duration from the start time, copies the streams,
    and resets timestamps.

    Args:
    start (str): Start time for trimming.
    duration (str): Duration to keep after the start time.
    input_file (str): Path to the input video file.
    output_file (str): Path to the output video file.
    video_channel (int, optional): Video channel to map. Defaults to 0.
    audio_channel (int, optional): Audio channel to map. Defaults to 0.
    subtitle_channel (int, optional): Subtitle channel to map. Defaults to 0.
    """
    # Construct the ffmpeg command
    trim_command = [
        FFMPEG_PATH,
        "-ss",
        start,
        "-i",
        input_file,
        "-t",
        duration,
        "-map",
        f"0:v:{video_channel}?",
        "-map",
        f"0:a:{audio_channel}?",
        "-map",
        f"0:s:{subtitle_channel}?",
        "-reset_timestamps",
        "1",
        "-c",
        "copy",
        output_file,
    ]

    # Execute the command
    print("Starting trim_duration")
    subprocess.run(trim_command, check=True)
    print("trim_duration done!")


def fade(input_file: str, output_file: str, video_duration: int) -> None:
    """
    Applies a fade-out effect to the video and audio of the input file.

    Args:
        input_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        video_duration (int): Duration of the video in seconds.
    """
    fade_duration = 1  # Duration of the fade effect in seconds
    fade_start = video_duration - fade_duration  # Start time of the fade effect

    task = [
        FFMPEG_PATH,
        "-y",  # Overwrite output file without asking
        "-i",
        input_file,
        "-vf",
        f"fade=t=out:st={fade_start}:d={fade_duration}",  # Video fade
        "-af",
        f"afade=t=out:st={fade_start}:d={fade_duration}",  # Audio fade
        output_file,
    ]

    print("Starting fade effect")
    try:
        subprocess.run(task, check=True)
        print("Fade effect applied successfully to both video and audio.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the fade effect: {e}")
        raise


def convert_3gp_to_mp4(input_file, output_file):
    """
    Convert a .3gp video to mp4 format.

    :param input_file: Path to the input .3gp file.
    :param output_file: Path to the output mp4 file.
    """
    # Use FFmpeg to perform the conversion
    conversion_command = [
        FFMPEG_PATH,
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]

    try:
        subprocess.run(conversion_command, check=True)
        print(f"Conversion successful. {input_file} converted to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")


def extract_audio(_input, _output):
    """
    Extract audio from video file.

    Args:
        _input: Input video file path
        _output: Output audio file path (e.g. output.mp3)
    """
    output_ext = Path(_output).suffix.lower()

    # Base command
    _task = [
        FFMPEG_PATH,
        "-i",
        _input,
        "-vn",  # Disable video
    ]

    # Add format-specific encoding parameters
    if output_ext == ".mp3":
        _task.extend(
            [
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",  # VBR quality (0-9, lower is better)
            ]
        )
    elif output_ext == ".wav":
        _task.extend(
            [
                "-c:a",
                "pcm_s16le",  # Standard 16-bit PCM
            ]
        )
    elif output_ext == ".ogg":
        _task.extend(
            [
                "-c:a",
                "libvorbis",
                "-q:a",
                "4",  # Quality scale (0-10)
            ]
        )
    else:
        _task.extend(["-c:a", "copy"])  # Default to stream copy for other formats

    _task.append(_output)

    print("Starting audio extraction...")
    try:
        subprocess.run(_task, check=True)
        print("Audio extraction complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error during audio extraction: {e}")
        raise


def image_audio_to_video(image_path, audio_path, output_path):
    """
    Create a video from a single image and audio file.
    The video duration will match the audio duration.

    Args:
        image_path (str): Path to the input image file
        audio_path (str): Path to the input audio file
        output_path (str): Path to the output video file
    """
    # Get audio duration to determine video length
    audio_duration = get_video_duration(audio_path)
    
    if audio_duration <= 0:
        print("Error: Could not determine audio duration")
        return

    # FFmpeg command to create video from image and audio
    task = [
        FFMPEG_PATH,
        "-y",  # Overwrite output file without asking
        "-loop", "1",  # Loop the image
        "-i", str(image_path),  # Input image
        "-i", str(audio_path),  # Input audio
        "-c:v", "libx264",  # Video codec
        "-tune", "stillimage",  # Optimize for still images
        "-c:a", "aac",  # Audio codec
        "-b:a", "192k",  # Audio bitrate
        "-pix_fmt", "yuv420p",  # Pixel format for compatibility
        "-shortest",  # End when shortest input ends (audio)
        "-r", "30",  # Frame rate
        str(output_path)
    ]

    print(f"Creating video from image: {image_path}")
    print(f"Audio file: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Duration: {audio_duration:.2f} seconds")
    
    try:
        subprocess.run(task, check=True)
        print("Image + Audio to Video conversion complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error during image+audio to video conversion: {e}")
        raise


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
    temp_trim_output = Path(temp_trim_output)

    if "external" in _subs_status:
        trim_with_hard_subs(
            _trim_start,
            _trim_end,
            _video_location,
            temp_trim_output.absolute().as_posix(),
            subtitles_path=_subs_location,
            audio_channel=_audio_channel,
        )
    else:
        trim_with_hard_subs(
            _trim_start,
            _trim_end,
            _video_location,
            temp_trim_output.absolute().as_posix(),
            audio_channel=_audio_channel,
            subtitles_channel=_subs_channel,
        )

    temp_mp4_output = os.path.join(output_base_path, f"encode_{output_file_name}")
    temp_mp4_output = Path(temp_mp4_output)
    encode_web_mp4(
        temp_trim_output.absolute().as_posix(), temp_mp4_output.absolute().as_posix()
    )
    # clean temp file
    os.remove(temp_trim_output.absolute().as_posix())

    video_duration = calculate_duration(_trim_end, _trim_start)

    temp_duration_output = os.path.join(
        output_base_path, f"duration_{output_file_name}"
    )
    temp_duration_output = Path(temp_duration_output)
    trim_duration(
        "00:00:00",
        video_duration,
        temp_mp4_output,
        temp_duration_output.absolute().as_posix(),
    )
    # clean temp file
    os.remove(temp_mp4_output.absolute().as_posix())

    _video_duration_seconds = int(
        get_video_duration(temp_duration_output.absolute().as_posix())
    )
    _output = clean_text(_output)
    fade(temp_duration_output.absolute().as_posix(), _output, _video_duration_seconds)

    os.remove(temp_duration_output.absolute().as_posix())
    print("All Done!")


def trim_preset_new(
    video_path,
    subtitles_path,
    output_path,
    trim_start,
    trim_end,
    subtitles_status,
    audio_channel=0,
    subtitles_channel=0,
):
    """
    Trims and encodes video with optional hard subtitles, handling temporary files cleanly.
    """
    # Convert string paths to Path objects
    video_path = Path(video_path)
    subtitles_path = Path(subtitles_path)
    output_path = Path(output_path)
    output_base_path = output_path.parent

    output_base_path = output_path.parent

    # Temporary files
    temp_trim_output = output_base_path / f"basic_{video_path.name}"
    temp_duration_output = output_base_path / f"duration_{video_path.name}"
    temp_encoded_output = output_base_path / f"encoded_{output_path.name}"
    print(f"{temp_trim_output=}")
    print(f"{temp_duration_output=}")
    print(f"{temp_encoded_output=}")

    try:
        # Trim with hard subtitles if required
        if "external" in subtitles_status:
            trim_with_hard_subs(
                trim_start,
                trim_end,
                str(video_path),
                str(temp_trim_output),
                subtitles_path=str(subtitles_path),
                audio_channel=audio_channel,
            )
        else:
            trim_with_hard_subs(
                trim_start,
                trim_end,
                str(video_path),
                str(temp_trim_output),
                audio_channel=audio_channel,
                subtitles_channel=subtitles_channel,
            )

        # Calculate video duration
        video_duration = calculate_duration(trim_end, trim_start)

        # Trim duration
        trim_duration(
            "00:00:00",
            video_duration,
            str(temp_trim_output),
            str(temp_duration_output),
        )

        # Encode to web mp4 format
        encode_web_mp4(str(temp_duration_output), str(temp_encoded_output))

        # Get video duration in seconds
        video_duration_seconds = int(get_video_duration(str(temp_encoded_output)))

        # Clean text for output
        output_cleaned = clean_text(str(output_path))

        # Apply fade effect
        fade(str(temp_encoded_output), output_cleaned, video_duration_seconds)

    finally:
        print("Cleaning up temporary files...")
        # Clean up temporary files
        for temp_file in [temp_trim_output, temp_duration_output, temp_encoded_output]:
            if temp_file.exists():
                temp_file.unlink()

    print("All Done!")


if __name__ == "__main__":
    print("This is a module, not a program")
