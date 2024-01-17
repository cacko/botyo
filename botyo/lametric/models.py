from enum import StrEnum


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
