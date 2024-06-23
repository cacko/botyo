from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro


@click.command("initpredict", short_help="init predict db")
@pass_environment
@coro
def cli(ctx: Environment):
    try:
        from botyo.predict.db import create_tables
        create_tables()
    except Exception as e:
        print(e)