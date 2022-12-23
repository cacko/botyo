from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.music.beats.db import BeatsDb


@click.command("dbinit", short_help="init beats db")
@pass_environment
@coro
def cli(ctx: Environment):
    try:
        from botyo.music.beats.models.beats import Beats
        with BeatsDb.db as db:
            db.create_tables([Beats])
    except Exception as e:
        print(e)