from abc import ABC
from dataclasses import dataclass


@dataclass
class MediaInfo:
    file_location: str = ""
    subtitle_location: str = ""
    video_channel: int = 0
    audio_channel: int = 0
    subtitle_channel: int = 0
    trim_start: str = "00:00:00"
    trim_end: str = "00:00:00"
