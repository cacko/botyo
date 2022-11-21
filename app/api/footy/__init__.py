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
from .item.competitions import CompetitionItem
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
)  # type: ignore
def scores_command(context: Context):
    message = Footy.livescore().render(context.query, group_by_league=True)

    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)


@bp.command(
    method=ZMethod.FOOTY_LIVE,
    desc="Livescores or live events for game",
)  # type: ignore
def live_command(context: Context):
    message = Footy.livescore(live=True).render(context.query, group_by_league=True)

    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)


@bp.command(
    method=ZMethod.FOOTY_SUBSCRIBE,
    desc="subscribes the channels for the live updates during the game",
)  # type: ignore
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


@bp.command(method=ZMethod.FOOTY_UNSUBSCRIBE, desc="cancels a subscribtion")  # type: ignore
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
)  # type: ignore
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


@bp.command(method=ZMethod.FOOTY_LEAGUES, desc="Enabled leagues")  # type: ignore
def competitions_command(context: Context) -> RenderResult:
    competitions = Footy.competitions()
    message = competitions.message(context.query)
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_LEAGUES)


@bp.command(method=ZMethod.FOOTY_LINEUP, desc="Game lineup")  # type: ignore
def lineups_command(context: Context) -> RenderResult:
    lineups = Footy.lineups(context.query)
    if lineups:
        message = lineups.message
        if message:
            return RenderResult(
                message=message,
            )
    return EmptyResult()


@bp.command(method=ZMethod.FOOTY_FACTS, desc="Game facts")  # type: ignore
def facts_command(context: Context) -> RenderResult:
    facts = Footy.facts(context.query)
    message = facts.message
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_FACTS)


@bp.command(method=ZMethod.FOOTY_STATS, desc="Game stats")  # type: ignore
def stats_command(context: Context) -> RenderResult:
    stats = Footy.stats(context.query)
    message = stats.message
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.FOOTY_STATS)


@bp.command(method=ZMethod.FOOTY_PLAYER, desc="Player stats")  # type: ignore
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


@bp.command(method=ZMethod.FOOTY_STANDINGS, desc="standings")  # type: ignore
def standings_Command(context: Context):
    query = context.query
    group = None

    if ":" in query:
        query, group = query.split(":", 1)

    if not query:
        return EmptyResult(method=ZMethod.FOOTY_STANDINGS)

    league_id = 0
    try:
        league_id = int(query)
    except ValueError:
        pass

    haystack = Data365.leagues
    if league_id:
        league = next(filter(lambda x: x.league_id == league_id, haystack), None)
    else:
        haystack = list(filter(lambda x: x.league_id in Config.ontv.leagues, haystack))
        matcher = LeagueMatch(haystack=haystack)
        leagues = matcher.fuzzy(LeagueNeedle(league_name=query))
        if not leagues:
            return EmptyResult(method=ZMethod.FOOTY_STANDINGS)
        league = leagues[0]
    if league:
        standings = Standings(league)
        table = standings.render(group)

        res = RenderResult(method=ZMethod.FOOTY_STANDINGS, message=table)
        return res
    return EmptyResult()


@bp.command(method=ZMethod.FOOTY_TEAM, desc="Team info")  # type: ignore
def team_command(context: Context) -> RenderResult:
    try:
        team = Footy.team(context.query)
        message = team.render()
        if not message:
            return EmptyResult()
        return RenderResult(message=message, method=ZMethod.FOOTY_TEAM)
    except TeamNotFound:
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_FIXTURES, desc="League fixtures")  # type: ignore
def fixtures_command(context: Context) -> RenderResult:
    try:
        competition = CompetitionItem(Footy.competition(context.query))
        message = competition.render()
        return RenderResult(message=message, method=ZMethod.FOOTY_FIXTURES)
    except CompetitionNotFound:
        return EmptyResult()
