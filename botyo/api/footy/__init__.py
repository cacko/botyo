from botyo.api.footy.item.standings import Standings
from fuzzelinho import Match, MatchMethod, Needle
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, RenderResult, EmptyResult
from botyo.threesixfive.data import Data365
from botyo.core.config import Config
from .footy import Footy
from .item.competitions import CompetitionItem
from botyo.server.output import TextOutput
from botyo.server.models import ZMethod
import logging

bp = Blueprint("footy")


class LeagueMatch(Match):
    minRatio = 10
    method = MatchMethod.SIMILARITY


class LeagueNeedle(Needle):
    league_name: str


@bp.command(
    method=ZMethod.FOOTY_SCORES,
    desc="Livescores or live events for game",
    icon="scoreboard",
)  # type: ignore
def scores_command(context: Context):
    try:
        message = Footy.livescore().render(
            context.query if context.query else "", group_by_league=True
        )
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)
    except Exception as e:
        logging.debug(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_LIVE, desc="Livescores or live events for game", icon="live_tv"
)  # type: ignore
def live_command(context: Context):
    try:
        message = Footy.livescore(live=True).render(
            context.query if context.query else "", group_by_league=True
        )
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_SCORES)
    except Exception as e:
        logging.debug(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_SUBSCRIBE,
    desc="subscribes the channels for the live updates during the game",
    subscription=True,
    icon="mark_email_read",
)  # type: ignore
def subscribe_command(context: Context):
    if any([not context.client, not context.group, not context.query]):
        return EmptyResult()
    try:
        assert context.query
        result = Footy.subscribe(
            client=context.client, groupID=context.group, query=context.query
        )
        return RenderResult(
            method=ZMethod.FOOTY_SUBSCRIBE,
            message=result.message,
            group=context.group,
            new_id=result.sub_id,
        )
    except Exception as e:
        logging.exception(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_UNSUBSCRIBE,
    desc="cancels a subscribtion",
    subscription=True,
    icon="unsubscribe",
)  # type: ignore
def unsubscribe_command(context: Context):
    if any([not context.client, not context.group, not context.query]):
        return EmptyResult()
    try:
        assert context.query
        result = Footy.unsubscribe(
            client=context.client, group=context.group, query=context.query
        )
        return RenderResult(
            method=ZMethod.FOOTY_UNSUBSCRIBE,
            message=result.message,
            new_id=result.sub_id,
            group=context.group,
        )
    except Exception:
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_SUBSCRIPTIONS,
    desc="show all subscriptions in the channel",
    subscription=True,
    icon="subscriptions",
)  # type: ignore
def subscriptions_command(context: Context) -> RenderResult:
    if any([not context.client, not context.group]):
        return EmptyResult()
    jobs = Footy.listjobs(client=context.client, group=context.group)
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


@bp.command(
    method=ZMethod.FOOTY_LEAGUES, desc="Enabled leagues", icon="emoji_events"
)  # type: ignore
def competitions_command(context: Context) -> RenderResult:
    try:
        competitions = Footy.competitions()
        message = competitions.message(context.query if context.query else "")
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_LEAGUES)
    except Exception:
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_FACTS, desc="Gxzame facts", icon="fact_check")  # type: ignore
def facts_command(context: Context) -> RenderResult:
    try:
        assert context.query
        facts = Footy.facts(context.query)
        message = facts.message
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_FACTS)
    except Exception:
        return EmptyResult()


@bp.command(
    method=ZMethod.FOOTY_LINEUP, desc="Game lineup", icon="sports_soccer"
)  # type: ignore
def lineups_command(context: Context) -> RenderResult:
    try:
        assert context.query
        lineups = Footy.lineups(context.query)
        assert lineups
        message = lineups.message
        assert message
        return RenderResult(
            message=message,
        )
    except Exception:
        return EmptyResult()


# type: ignore
@bp.command(
    method=ZMethod.FOOTY_STATS, desc="Game stats", icon="equalizer"
)  # type: ignore
def stats_command(context: Context) -> RenderResult:
    try:
        assert context.query
        stats = Footy.stats(context.query)
        message = stats.message
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_STATS)
    except Exception:
        return EmptyResult()


# type: ignore
@bp.command(
    method=ZMethod.FOOTY_PLAYER, desc="Player stats", icon="snowboarding"
)  # type: ignore
def player_command(context: Context) -> RenderResult:
    try:
        assert context.query
        player = Footy.player(context.query)
        image = player.image
        image_path = image.path
        message = player.message
        assert image_path
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


# type: ignore
@bp.command(
    method=ZMethod.FOOTY_STANDINGS, desc="standings", icon="signal_cellular_alt"
)  # type: ignore
def standings_Command(context: Context):
    try:
        query = context.query
        group = None
        assert query
        if ":" in query:
            query, group = query.split(":", 1)
        league_id = 0
        try:
            league_id = int(query)
        except ValueError:
            pass
        haystack = Data365.leagues
        if league_id:
            league = next(filter(lambda x: x.league_id == league_id, haystack), None)
        else:
            haystack = list(
                filter(lambda x: x.league_id in Config.ontv.leagues, haystack)
            )
            matcher = LeagueMatch(haystack=haystack)
            leagues = matcher.fuzzy(LeagueNeedle(league_name=query))
            assert leagues
            league = leagues[0]
        assert league
        standings = Standings(league)
        table = standings.render(group)
        res = RenderResult(method=ZMethod.FOOTY_STANDINGS, message=table)
        return res
    except Exception as e:
        logging.exception(e)
        return EmptyResult()


@bp.command(method=ZMethod.FOOTY_TEAM, desc="Team info", icon="groups")  # type: ignore
def team_command(context: Context) -> RenderResult:
    try:
        assert context.query
        team = Footy.team(context.query)
        message = team.render()
        if not message:
            return EmptyResult()
        return RenderResult(message=message, method=ZMethod.FOOTY_TEAM)
    except Exception:
        return EmptyResult()


# type: ignore
@bp.command(
    method=ZMethod.FOOTY_FIXTURES, desc="League fixtures", icon="calendar_month"
)  # type: ignore
def fixtures_command(context: Context) -> RenderResult:
    try:
        assert context.query
        competition = CompetitionItem(Footy.competition(context.query))
        message = competition.render()
        return RenderResult(message=message, method=ZMethod.FOOTY_FIXTURES)
    except Exception:
        return EmptyResult()

@bp.command(
    method=ZMethod.FOOTY_H2H,
    desc="Head to head stats for active games",
    icon="scoreboard",
)  # type: ignore
def h2h_command(context: Context):
    try:
        assert context.query
        stats = Footy.h2h(context.query)
        message = stats.message
        assert message
        return RenderResult(message=message, method=ZMethod.FOOTY_STATS)
    except Exception:
        return EmptyResult()