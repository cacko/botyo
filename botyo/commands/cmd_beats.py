
from traceback import print_exc
from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.music.beats import Beats
from humanfriendly.tables import format_robust_table
import logging


@click.command("beats", short_help="beats info")
@click.argument("path")
@click.option("-h", "--hoplength", default=512)
@click.option("-m", "--margin", default=1)
@click.option("-f", "--force", is_flag=True, default=False)
@click.option("-v", "--with-vocals", is_flag=True, default=False)
@pass_environment
@coro
def cli(ctx: Environment, path, hoplength: int, margin: int, with_vocals: bool, force: bool):
    beats = Beats(path, hop_length=hoplength, margin=margin, with_vocals=with_vocals, force=force)
    try:
        tempo = beats.tempo
        beats = beats.beats
        num_beats = len(beats)
        column_names = ["Tempo", "Number of Beats", "Beats"]
        print(
            format_robust_table(
                [[f"{tempo}", f"{num_beats}", ", ".join(map(str, beats))]], column_names
            )
        )
    except Exception as e:
        print_exc(e)
        logging.error(e)
