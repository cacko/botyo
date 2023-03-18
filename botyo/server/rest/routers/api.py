from requests import post
from botyo.api.footy.item.livescore import Livescore
from botyo.api.logo.team import TeamLogoPixel
from botyo.music.nowplay import Track
from botyo.music.beats import Beats
from botyo.threesixfive.item.league import LeagueImagePixel
from botyo.threesixfive.item.team import Team as DataTeam
from botyo.threesixfive.item.models import CancelJobEvent
from botyo.core.otp import OTP
from botyo.api.footy.item.subscription import Subscription, SubscriptionClient
from botyo.api.footy.footy import Footy
from fastapi import (
    APIRouter,
    Request,
    HTTPException
)
import logging
from fastapi.concurrency import run_in_threadpool

router = APIRouter()


@router.get("/api/team_schedule/{query}", tags=["api"])
async def get_team_schedule(
    query: str = "",
):
    try:
        assert query
        try:
            team_id = int(query)
            data_team = DataTeam(team_id)
            data = data_team.team
            res = []
            for game in data.games:
                logo = LeagueImagePixel(game.competitionId)
                n64 = logo.base64
                game.icon = n64
                res.append(game.dict())
            return res
        except ValueError:
            pass
        team = Footy.team(query)
        res = []
        struct = team.data
        for game in struct.games:
            logo = LeagueImagePixel(game.competitionId)
            n64 = logo.base64
            game.icon = n64
            res.append(game.dict())
        return res
    except AssertionError:
        raise HTTPException(status_code=404)


@router.post("/api/subscribe", tags=["api"])
async def post_subscribe(
    request: Request
):
    data = await request.json()
    assert isinstance(data, dict)
    res = Footy.subscribe(
        client=f"{data.get('webhook')}",
        groupID=f"{data.get('group')}",
        query=f"{data.get('id')}",
    )
    return {"message": res}


@router.post("/api/subscriptions", tags=["api"])
async def post_subscriptions(request: Request):
    data = await request.json()
    assert isinstance(data, dict)
    sc = SubscriptionClient(
        data.get("webhook", ""),
        data.get("group")
    )
    jobs = Subscription.forGroup(sc)
    return [{"id": job.id, "text": job.name} for job in jobs]


@router.post("/api/unsubscribe", tags=["api"])
async def post_unsubscribe(request: Request):
    data = await request.json()
    assert isinstance(data, dict)
    sc = SubscriptionClient(
        data.get("webhook", ""),
        data.get("group")
    )
    jobs = Subscription.forGroup(sc)
    id_parts = data.get("id", "").split(":")
    for job in jobs:
        try:
            if job.id.startswith(id_parts[0]):
                Subscription.clients(id_parts[0]).remove(sc)
                post(
                    data.get("webhook", ""),
                    headers=OTP(data.get("group", "")).headers,
                    json=CancelJobEvent(
                        job_id=id_parts[0]).dict(),
                )
                return {"message": f"unsubscribed from {job.name}"}
        except ValueError:
            pass
    return {"message": "nothing unsubscribed"}


@router.get("/api/team_logo/{query}", tags=["api"])
def get_team_logo(query: str):
    logo = TeamLogoPixel(query)
    b64 = logo.base64
    return {"logo": b64}


@router.get("/api/league_logo/{query}", tags=["api"])
def get_league_logo(query: str):
    logo = LeagueImagePixel(query)
    b64 = logo.base64
    return {"logo": b64}


@router.get("/api/league_schedule/{query}", tags=["api"])
def get_league_schedule(query: str):
    data_league = Footy.competition(query)
    res = []
    try:
        assert data_league.games
        for game in data_league.games:
            logo = LeagueImagePixel(data_league.id)
            n64 = logo.base64
            game.icon = n64
            res.append(game.dict())
    except AssertionError:
        pass
    return res


@router.get("/api/livescore", tags=["api"])
async def get_livescore():
    def scores(obj: Livescore):
        events = obj.items
        return [g.dict() for g in events]

    obj = Footy.livescore()
    if not obj:
        raise HTTPException(404)
    return await run_in_threadpool(scores, obj=obj)


@router.get("/api/beats", tags=["api"])
async def get_beats(path: str):
    def extract(path):
        beats = Beats(path=path)
        return beats.model.dict()
    try:
        return await run_in_threadpool(extract, path=path)
    except (FileNotFoundError):
        raise HTTPException(404)


@router.post("/api/nowplaying", tags=["api"])
async def post_nowplaying(request: Request):
    def persist(data: dict):
        _ = Track(**data)
        Track.persist()
    try:
        data = await request.json()
        assert isinstance(data, dict)
        await run_in_threadpool(persist, data=data)
    except AssertionError as e:
        logging.error(e)
    return {}
