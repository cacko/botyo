from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    LOADING = "loading"
    EXIT = "exit"
    RESUMED = "resumed"
    NEXT = "next"
    PREVIOUS = "previous"
    ERROR = "error"

class Track(BaseModel):
    art: str
    artist: str
    album: str
    track: str