from botyo.cli import pass_environment, Environment
import click
import logging
import importlib


@click.command("serve", short_help="Initializes a repo.")
@pass_environment
def cli(ctx: Environment):
    mod = importlib.import_module("botyo.app")
    server = mod.create_app()
    server.register_scheduler(ctx.redis_url)
    logging.info("Init done")
    server.start(ctx.host, ctx.port)
