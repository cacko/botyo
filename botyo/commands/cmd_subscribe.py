from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.api.footy.footy import Footy
from urllib.parse import urlparse
from botyo.server.scheduler import Scheduler
from apscheduler.schedulers.background import BackgroundScheduler


@click.command("subscribe", short_help="subscribe for update")
@click.argument("webhook")
@click.argument("filt")
@pass_environment
@coro
def cli(ctx: Environment, webhook, filt):
    worker = BackgroundScheduler()
    scheduler = Scheduler(worker, ctx.redis_url)

    parsed = urlparse(webhook)

    res = Footy.subscribe(
        client=f"{parsed.scheme}://{parsed.netloc}",
        groupID=f"{parsed.path}",
        query=filt
    )
    scheduler.start()
    print(res)
