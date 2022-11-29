
from .shell import Shell
from typing import Optional

class LyricsShell(Shell):
    OUTPUT_IGNORED = ["Tekst piosenki:", "Dodaj", "Historia"]
    OUTPUT_REPLACED = ["lyrics: fetched lyrics:",
                       "lyrics: lyrics already present:"]

    executable = "conda"
    executable_arguments = ["run", "-n", "base", "--live-stream", "beet", "lyrics", "-p"]

    def __post_init__(self):
        if len(self.args) == 1 and not self.args[0].startswith("title:"):
            self.args[0] = f"title:{self.args[0]}"


class Lyrics:

    __query: str
    __message: Optional[str] = None

    def __init__(self, query: str):
        self.__query = query

    @property
    def text(self) -> str:
        if not self.__message:
            self.__message = "\n".join(
                [line for line in LyricsShell.output(self.__query)])
        return self.__message
