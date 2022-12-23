from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.api.footy.item.livescore import GameMatch, GameNeedle
from botyo.api.footy.footy import Footy


@click.command("match", short_help="test avatar")
@click.argument("filt")
@pass_environment
@coro
def cli(ctx: Environment, filt):
    livescores = Footy.livescore()
    items = livescores.items
    matcher = GameMatch(haystack=items)
    res = matcher.fuzzy(GameNeedle(strAwayTeam=filt, strHomeTeam=filt))
    filtered = [x.id for x in GameMatch(haystack=items).fuzzy(GameNeedle(
                strHomeTeam=filt,
                strAwayTeam=filt,
                strLeague=filt
                ))]
    matches = [x for x in sorted(items, key=lambda itm: itm.sort)
               if any(
        [
            not filt,
            x.id in filtered
        ]
    )]
    res = [f"{x.strHomeTeam} x {x.strAwayTeam} {x.strLeague}" for x in matches]
    print("\n".join(res))
