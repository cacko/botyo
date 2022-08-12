from dataclasses import dataclass
from tkinter import NONE
from app.core import logger
from pathlib import Path
from typing import Optional
from app.music.beats.db import BeatsDb
from app.music.shell import Shell
from cachable import Cachable
from app.core.string import string_hash
from librosa import (
    stft,
    istft,
    magphase,
    load,
    frames_to_time,
    time_to_frames,
    onset,
    beat,
    decompose,
)
from librosa.util import peak_pick, softmask
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from .models.beats import Beats as BeatsModel
from app.core.time import perftime
import soundfile as sf
import numpy as np
from app.core.bytes import nearest_bytes


@dataclass_json
@dataclass
class BeatsStruct:
    path: Path
    beats: Optional[list[float]] = None
    tempo: Optional[float] = None


class Decoder(Shell):
    executable: str = "ffmpeg"

    def __init__(self, input_path: Path, output_path: Path):
        self.args = [
            "-y",
            "-v",
            "fatal",
            "-i",
            input_path.as_posix(),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "22050",
            "-ac",
            "1",
            "-af",
            "loudnorm=I=-5:LRA=15:TP=0",
            output_path.as_posix(),
        ]


class Beats(Cachable):

    __path: Path = None
    _id: str = None
    __hop_length: int = 512
    __margin: int = 1
    __with_vocals: bool = True
    __force: bool = False
    __tmppath: Path = None
    _struct: BeatsStruct = None

    def __init__(
        self, path: str, hop_length=512, margin=0, with_vocals=False, force=False
    ) -> None:
        self.__path = self._resolve_path(path)
        self.__hop_length = hop_length
        self.__margin = nearest_bytes(margin)
        self.__with_vocals = with_vocals
        self.__force = force
        if not self.__path.exists():
            raise FileNotFoundError

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if self.__force:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    def fromcache(self):
        if model := BeatsModel.fetch(BeatsModel.path_id == self.id):
            return BeatsStruct(
                path=Path(model.path),
                beats=list(map(float, model.beats)),
                tempo=model.tempo,
            )
        return None

    def tocache(self, res: BeatsStruct):
        with BeatsDb.db.atomic():
            BeatsModel.insert(
                path=res.path.as_posix(),
                path_id=self.id,
                beats=res.beats,
                tempo=res.tempo,
            ).on_conflict(
                conflict_target=[BeatsModel.path_id],
                update={BeatsModel.beats: res.beats, BeatsModel.tempo: res.tempo},
            ).execute()
        return res

    def _resolve_path(self, path):
        res = Path(path)
        return res

    @property
    def id(self):
        if not self._id:
            self._id = string_hash(self.__path.as_posix())
        return self._id

    @property
    def tmppath(self) -> Path:
        if not self.__tmppath:
            self.__tmppath = Path("/var/www/znayko/.cache") / f"{self.id}.wav"
        return self.__tmppath

    def _decode(self):
        with perftime(f"decoding {self.__path}"):
            worker = Decoder(input_path=self.__path, output_path=self.tmppath)
            return worker.execute()

    def _load(self):
        self._decode()
        with perftime(f"extracting beats {self.__path}"):
            y, sr = load(self.tmppath.as_posix())
            D = stft(y)
            y_percussive = None
            if self.__with_vocals:
                logger.info(f"Percussive margin: {self.__margin}")
                _, D_percussive = decompose.hpss(D, margin=self.__margin)
                y_percussive = istft(D_percussive, length=len(y))
            else:
                logger.info(f"No vocals mode: {self.__path}")
                S_full, phase = magphase(stft(y))
                S_filter = decompose.nn_filter(
                    S_full,
                    aggregate=np.median,
                    metric="cosine",
                    width=int(time_to_frames(2, sr=sr)),
                )
                S_filter = np.minimum(S_full, S_filter)
                margin_i, margin_v = 2, 10
                power = 2

                mask_i = softmask(S_filter, margin_i * (S_full - S_filter), power=power)

                mask_v = softmask(S_full - S_filter, margin_v * S_filter, power=power)
                S_foreground = mask_v * S_full
                S_background = mask_i * S_full
                # D_foreground = S_foreground * phase
                D_background = S_background * phase
                y_percussive = istft(D_background)

            # sf.write(Path("~/bc.wav").expanduser().as_posix(), y_percussive, sr)

            spectral_novelty = onset.onset_strength(
                y=y_percussive, sr=sr, hop_length=self.__hop_length
            )

            onset_frames = peak_pick(
                spectral_novelty,
                pre_max=3,
                post_max=3,
                pre_avg=3,
                post_avg=5,
                delta=0.5,
                wait=10,
            )

            beat_times = frames_to_time(onset_frames, hop_length=self.__hop_length)
            tempo = beat.tempo(y=y_percussive, sr=sr)

            self._struct = BeatsStruct(
                beats=list(map(float, list(beat_times))),
                tempo=tempo[0],
                path=self.__path,
            )
            self.tmppath.unlink(missing_ok=True)
            return self.tocache(self._struct)

    @property
    def model(self) -> BeatsStruct:
        if not self.load():
            self._load()
        return self._struct

    @property
    def tempo(self) -> float:
        if not self.load():
            self._load()
        return self._struct.tempo

    @property
    def path(self) -> str:
        if not self.load():
            self._load()
        return self._struct.path

    @property
    def beats(self) -> float:
        if not self.load():
            self._load()
        else:
            logger.warning(f"Loading beats for {self.__path} from cache")
        return self._struct.beats
