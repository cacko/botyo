from typing import Annotated
from uuid import uuid4
from requests import post
from botyo.api.footy.item.livescore import Livescore
from botyo.api.logo.team import TeamLogoPixel
from botyo.image.koncat import Konkat
from botyo.music.nowplay import Track
from botyo.music.beats import Beats
from botyo.threesixfive.item.league import LeagueImagePixel
from botyo.threesixfive.item.team import Team as DataTeam
from botyo.threesixfive.item.models import CancelJobEvent
from botyo.core.otp import OTP
from botyo.api.footy.item.subscription import RESTClient, Subscription, SubscriptionClient
from botyo.api.footy.footy import Footy
from fastapi import APIRouter, Body, File, Request, HTTPException, Form
import logging
from fastapi.concurrency import run_in_threadpool
from corefile import TempPath
from botyo.lametric import LaMetric
from botyo.lametric.models import Track as LametricTrack
from botyo.core.image import download_image
import requests

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
                res.append(game.model_dump())
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
            res.append(game.model_dump())
        return res
    except AssertionError:
        raise HTTPException(status_code=404)


@router.post("/api/subscribe", tags=["api"])
async def post_subscribe(request: Request):
    data = await request.json()
    assert isinstance(data, dict)
    client = RESTClient(
        client_id=f"{data.get('webhook')}",
        group_id=f"{data.get('group')}"
    )
    res = Footy.subscribe(
        client=client,
        query=f"{data.get('id')}",
    )
    return {"message": res}


@router.post("/api/subscriptions", tags=["api"])
async def post_subscriptions(request: Request):
    data = await request.json()
    assert isinstance(data, dict)
    sc = RESTClient(data.get("webhook", ""), data.get("group"))
    jobs = Subscription.forGroup(sc)
    return [{"id": job.id, "text": job.name} for job in jobs]


@router.post("/api/unsubscribe", tags=["api"])
async def post_unsubscribe(request: Request):
    data = await request.json()
    assert isinstance(data, dict)
    sc = RESTClient(data.get("webhook", ""), data.get("group"))
    jobs = Subscription.forGroup(sc)
    id_parts = data.get("id", "").split(":")
    for job in jobs:
        try:
            if job.id.startswith(id_parts[0]):
                Subscription.clients(id_parts[0]).remove(sc)
                post(
                    data.get("webhook", ""),
                    headers=OTP(data.get("group", "")).headers,
                    json=CancelJobEvent(job_id=id_parts[0]).model_dump(),
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
            res.append(game.model_dump())
    except AssertionError:
        pass
    return res


@router.get("/api/livescore", tags=["api"])
async def get_livescore():
    def scores(obj: Livescore):
        events = obj.items
        return [g.model_dump() for g in events]

    obj = Footy.livescore()
    if not obj:
        raise HTTPException(404)
    return await run_in_threadpool(scores, obj=obj)


@router.get("/api/beats", tags=["api"])
async def get_beats(path: str):
    def extract(path):
        beats = Beats(path=path)
        return beats.model.model_dump()

    try:
        return await run_in_threadpool(extract, path=path)
    except FileNotFoundError:
        raise HTTPException(404)


@router.put("/api/nowplaying", tags=["api"])
async def put_nowplaying(request: Request):
    def persist(data: dict):
        _ = Track(**data)

    try:
        data = await request.json()
        assert isinstance(data, dict)
        await run_in_threadpool(persist, data=data)
    except AssertionError as e:
        logging.error(e)
    return {}


@router.post("/api/nowplaying", tags=["api"])
async def post_nowplaying(
    art: Annotated[str, Form()],
    artist: Annotated[str, Form()],
    album: Annotated[str, Form()],
    track: Annotated[str, Form()],
):
    try:
        text = f"{artist}  / {track}"
        icon = download_image(art)
        return LaMetric.nowplaying(text, icon.as_posix())
    except AssertionError as e:
        logging.error(e)
    except requests.exceptions.InvalidURL:
        logging.error(f"art={art}, artist={artist}, track={track}")
    return {}


@router.post("/api/koncat", tags=["api"])
async def upload_koncat(
    request: Request,
    file: bytes = File(),
    collage_id: str = Form()
):
    uploaded_path = TempPath(uuid4().hex)
    uploaded_path.write_bytes(file)
    return Konkat.upload(uploaded_path, collage_id).model_dump()


@router.delete("/api/koncat/{filename}", tags=["api"])
async def delete_koncat(filename: str):
    return dict(file_id=Konkat.delete(filename))


@router.get("/api/koncat/files/{collage_id}", tags=["api"])
async def get_konkat_files(collage_id: str):
    return [k.model_dump() for k in Konkat.files(collage_id)]


@router.get("/api/koncat/{collage_id}", tags=["api"])
async def get_colage(collage_id: str, shuffle: bool = False) :
    return Konkat.collage(collage_id).model_dump()
