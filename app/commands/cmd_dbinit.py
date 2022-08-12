from botyo_server.cli import pass_environment, Environment
import click
from app.commands import coro
from app.music.beats.db import BeatsDb


@click.command("dbinit", short_help="init beats db")
@pass_environment
@coro
def cli(ctx: Environment):
    try:
        from app.music.beats.models.beats import Beats
        with BeatsDb.db as db:
            db.create_tables([Beats])
    except Exception as e:
        print(e)