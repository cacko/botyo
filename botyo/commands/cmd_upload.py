
from traceback import print_exc
from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.core.s3 import S3
from pathlib import Path
import logging


@click.command("upload", short_help="upload file to s3")
@click.argument("path")
@pass_environment
@coro
def cli(ctx: Environment, path):
    try:
        src = Path(path)
        assert src.exists()
        res = S3.upload(src, src.name)
        click.echo(res)
    except Exception as e:
        print_exc(e)
        logging.error(e)
