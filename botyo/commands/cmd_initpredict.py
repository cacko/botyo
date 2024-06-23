import logging
from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.predict.db import create_tables


@click.command("initpredict", short_help="init predict db")
@pass_environment
@coro
def cli(ctx: Environment):
    try:
        create_tables()
    except Exception as e:
        logging.exception(e)