from app.core import logger
from traceback import print_exc
from botyo_server.cli import pass_environment, Environment
import click
from app.commands import coro
from app.music.beats import Beats
from pathlib import Path
from prokopiy import Progress
import filetype

@click.command("importbeats", short_help="beats info")
@click.argument("path")
@click.option("-h", "--hoplength", default=512)
@click.option("-t", "--tightness", default=1)
@pass_environment
@coro
def cli(ctx: Environment, path, hoplength: int, tightness: int):
    queue_path = Path(path)
    processed = queue_path.parent / "processed.dat"
    queue = queue_path.read_text().split("\n")
    with processed.open("ab") as pf:
        with Progress("Importing beats...") as progress:
            for f in progress.track(queue):
                fp = Path(f.strip())
                if filetype.is_image(fp.as_posix()):
                    pf.write(f"{f}\n".encode())
                    continue
                try:
                    beats = Beats(fp.as_posix(), hop_length=hoplength, tightness=tightness)
                    tempo = beats.tempo
                    beats = beats.beats
                    num_beats = len(beats)
                    column_names = ["Tempo", "Number of Beats", "Beats"]
                    pf.write(f"{f}\n".encode())
                except Exception as e:
                    print_exc(e)
                    logger.error(e)
