from abc import ABC
from dataclasses import dataclass


@dataclass
class MediaInfo:
    file_location: str = ""
    subtitle_location: str = ""
    audio_channel: str = "0"
    subtitle_channel: str = "0"
    trim_start: str = "00:00:00"
    trim_end: str = "00:00:00"
