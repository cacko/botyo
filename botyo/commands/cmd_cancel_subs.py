from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.server.scheduler import Scheduler


@click.command("cancel_subs", short_help="test avatar")
@pass_environment
@coro
def cli(ctx: Environment):
    print(Scheduler.get_jobs())
    print(Scheduler.cancel_jobs())
