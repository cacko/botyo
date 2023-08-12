from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.server.scheduler import Scheduler
from apscheduler.schedulers.background import BackgroundScheduler


@click.command("cancel_subs", short_help="test avatar")
@pass_environment
@coro
def cli(ctx: Environment):
    worker = BackgroundScheduler()
    _ = Scheduler(worker, ctx.redis_url)
    Scheduler.start()
    print(Scheduler.get_jobs())
    Scheduler.remove_all_jobs()
