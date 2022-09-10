from botyo_server.cli import pass_environment, Environment
import click
from app.commands import coro
from corestring import string_hash
import logging


@click.command("fixbeats", short_help="fixbeats")
@pass_environment
@coro
def cli(ctx: Environment):
    try:
        from app.music.beats.models.beats import Beats
        for beat in Beats.select():
            logging.info(beat)
            pid = string_hash(beat.path)
            if pid != beat.path_id:
                logging.info(f"pid differs {beat.path}")
                beat.path_id = pid
                beat.save()
    except Exception as e:
        print(e)