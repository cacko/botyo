from botyo.cli import pass_environment, Environment
import click
from pathlib import Path
import logging
import sys


@click.command("serve", short_help="Initializes a repo.")
@pass_environment
def cli(ctx: Environment):
    app_folder = Path(".").absolute().as_posix()
    sys.path.insert(0, app_folder)
    __import__("botyo")
    mod = __import__(
        f"botyo", None, None, ["app"])
    server = mod.create_app()
    server.register_scheduler(ctx.redis_url)
    logging.info("Init done")
    server.start(ctx.host, ctx.port)
