from app.api.footy.item.standings import Standings
from fuzzelinho import Match, MatchMethod
from botyo_server.blueprint import Blueprint
from botyo_server.socket.connection import Context
from botyo_server.models import Attachment, RenderResult, EmptyResult
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from app.threesixfive.data import Data365
from app.core.config import Config
from .footy import Footy
from app.threesixfive.exception import CompetitionNotFound, GameNotFound, TeamNotFound
from apscheduler.job import Job
from botyo_server.output import TextOutput
from app.api import ZMethod

bp = Blueprint("footy")


class LeagueMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class LeagueNeedle:
    league_name: str


@bp.command(
    method=ZMethod.FOOTY_SCORES,
    desc="Livescores or live events for game",
)
def scores_command(context: Context):
    message = Footy.livescore().render(context.query, group_by_league=True)

    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)


@bp.command(
    method=ZMethod.FOOTY_LIVE,
    desc="Livescores or live events for game",
)
def live_command(context: Context):
    message = Footy.livescore(live=True).render(context.query, group_by_league=True)

    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)


@bp.command(
    method=ZMethod.FOOTY_SUBSCRIBE,
    desc="subscribes the channels for the live updates during the game",
)
def subscribe_command(context: Context):
    if any([not context.client, not context.group, not context.query]):
        return EmptyResult()
    try:
        response = Footy.subscribe(
            client=context.client, groupID=context.group, query=context.query
        )
        return RenderResult(
            method=ZMethod.FOOTY_SUBSCRIBE, message=response, group=context.group
        )
    except GameNotFound:
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_UNSUBSCRIBE, desc="cancels a subscribtion")
def unsubscribe_command(context: Context):
    if any([not context.client, not context.group, not context.query]):
        return EmptyResult()
    try:
        response = Footy.unsubscribe(
            client=context.client, group=context.group, query=context.query
        )
        return RenderResult(
            method=ZMethod.FOOTY_UNSUBSCRIBE, message=response, group=context.group
        )
    except GameNotFound:
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_SUBSCRIPTIONS, desc="show all subscriptions in the channel"
)
def subscriptions_command(context: Context) -> RenderResult:
    if any([not context.client, not context.group]):
        return EmptyResult()
    jobs: list[Job] = Footy.listjobs(client=context.client, group=context.group)
    if not len(jobs):
        rows = ["Nothing is scheduled"]
    else:
        rows = [j.name for j in jobs]
    TextOutput.addRows(rows)
    return RenderResult(
        method=ZMethod.FOOTY_SUBSCRIPTIONS,
        message=TextOutput.render(),
        group=context.group,
    )


@bp.command(method=ZMethod.FOOTY_LEAGUES, desc="Enabled leagues")
def competitions_command(context: Context) -> RenderResult:
    competitions = Footy.competitions()
    message = competitions.message(context.query)
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_LEAGUES)


@bp.command(method=ZMethod.FOOTY_LINEUP, desc="Game lineup")
def lineups_command(context: Context) -> RenderResult:
    lineups = Footy.lineups(context.query)
    if lineups:
        message = lineups.message
        if not message:
            return EmptyResult()
        return RenderResult(
            message=message,
        )


@bp.command(method=ZMethod.FOOTY_FACTS, desc="Game facts")
def facts_command(context: Context) -> RenderResult:
    facts = Footy.facts(context.query)
    message = facts.message
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_FACTS)


@bp.command(method=ZMethod.FOOTY_STATS, desc="Game stats")
def stats_command(context: Context) -> RenderResult:
    stats = Footy.stats(context.query)
    message = stats.message
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_STATS)


@bp.command(method=ZMethod.FOOTY_PLAYER, desc="Player stats")
def player_command(context: Context) -> RenderResult:
    try:
        player = Footy.player(context.query)
        image = player.image
        image_path = image.path
        message = player.message
        if not image_path:
            return EmptyResult()
        if not image_path.exists():
            return RenderResult(method=ZMethod.FOOTY_PLAYER, message=message)
        return RenderResult(
            method=ZMethod.FOOTY_PLAYER,
            message=message,
            attachment=Attachment(
                path=image_path.as_posix(), contentType=image.contentType
            ),
        )
    except Exception:
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_STANDINGS, desc="standings")
def standings_Command(context: Context):
    query = context.query
    group = None

    if ":" in query:
        query, group = query.split(":", 1)

    if not query:
        return EmptyResult(method=ZMethod.FOOTY_STANDINGS)

    haystack = Data365.leagues

    haystack = list(filter(lambda x: x.league_id in Config.ontv.leagues, haystack))

    matcher = LeagueMatch(haystack=haystack)

    leagues = matcher.fuzzy(LeagueNeedle(league_name=query))

    if not leagues:
        return EmptyResult(method=ZMethod.FOOTY_STANDINGS)

    league = leagues[0]

    standings = Standings(league)

    table = standings.render(group)

    res = RenderResult(method=ZMethod.FOOTY_STANDINGS, message=table)
    return res


@bp.command(method=ZMethod.FOOTY_TEAM, desc="Team info")
def team_command(context: Context) -> RenderResult:
    try:
        team = Footy.team(context.query)
        message = team.render()
        if not message:
            return EmptyResult()
        return RenderResult(message=message, method=ZMethod.FOOTY_TEAM)
    except TeamNotFound:
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_FIXTURES, desc="League fixtures")
def fixtures_command(context: Context) -> RenderResult:
    try:
        competition = Footy.competition(context.query)
        message = competition.render()
        return RenderResult(message=message, method=ZMethod.FOOTY_FIXTURES)
    except CompetitionNotFound:
        return EmptyResult()
