from fastapi import APIRouter, Request, HTTPException
import logging

router = APIRouter()


from botyo.api.footy.footy import Footy
from botyo.api.footy.item.subscription import Subscription, SubscriptionClient
from botyo.core.config import Config
from botyo.core.otp import OTP
from botyo.threesixfive.item.models import CancelJobEvent
from botyo.threesixfive.item.team import Team as DataTeam
from botyo.threesixfive.item.league import LeagueImagePixel
from botyo.music.beats import Beats
from botyo.music.nowplay import Track
from botyo.api.logo.team import TeamLogoPixel
from requests import post
import logging


@router.get("/api/team_schedule/{query}", tags=["api"])
async def read_lookup(
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
                res.append(game.to_dict())  # type: ignore
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
            res.append(game.to_dict())  # type: ignore
        return res
    except AssertionError:
        raise HTTPException(status_code=404)


# class _APIServer(Server):
#     def __init__(self, *args, **kwargs):
#         api_config = Config.api
#         super().__init__(
#             host=api_config.host,
#             port=api_config.port,
#             *args,
#             **kwargs
#         )
#         self.setup_routing()

#     def setup_routing(self):
#         self.app.route("/subscribe", "POST", self.subscribe)
#         self.app.route("/nowplaying", "POST", self.nowplaying)
#         self.app.route("/team_schedule/<query>", "GET", self.team_schedule)
#         self.app.route("/league_schedule/<query>", "GET", self.league_schedule)
#         self.app.route("/team_logo/<query>", "GET", self.team_logo)
#         self.app.route("/league_logo/<query>", "GET", self.league_logo)
#         self.app.route("/livescore", "GET", self.livescore)
#         self.app.route("/subscriptions", "POST", self.subscriptions)
#         self.app.route("/unsubscribe", "POST", self.unsubscribe)
#         self.app.route("/beats", "GET", self.beats)
#         self.app.route("/subscribe", "POST", self.subscribe)

#     def subscribe(self):
#         data = request.json
#         assert isinstance(data, dict)
#         res = Footy.subscribe(
#             client=f"{data.get('webhook')}",
#             groupID=f"{data.get('group')}",
#             query=f"{data.get('id')}",
#         )
#         return {"message": res}

#     def subscriptions(self):
#         data = request.json
#         assert isinstance(data, dict)
#         sc = SubscriptionClient(
#             client_id=data.get("webhook", ""), group_id=data.get("group")
#         )
#         jobs = Subscription.forGroup(sc)
#         return [{"id": job.id, "text": job.name} for job in jobs]

#     def unsubscribe(self):
#         data = request.json
#         assert isinstance(data, dict)
#         sc = SubscriptionClient(
#             client_id=data.get("webhook", ""), group_id=data.get("group")
#         )
#         jobs = Subscription.forGroup(sc)
#         id_parts = data.get("id", "").split(":")
#         for job in jobs:
#             if job.id.startswith(id_parts[0]):
#                 Subscription.clients(id_parts[0]).remove(sc)
#                 post(
#                     data.get("webhook", ""),
#                     headers=OTP(data.get("group", "")).headers,
#                     json=CancelJobEvent(
#                         job_id=id_parts[0]).to_dict(),  # type: ignore
#                 )
#                 return {"message": f"unsubscribed from {job.name}"}
#         return {"message": "nothing unsubscribed"}

#     def team_logo(self, query):
#         logo = TeamLogoPixel(query)
#         b64 = logo.base64
#         return {"logo": b64}

#     def beats(self):
#         try:
#             path = request.query.path  # type: ignore
#             beats = Beats(path=path)
#             return beats.model.to_dict()  # type: ignore
#         except (FileNotFoundError):
#             abort(404)

#     def league_logo(self, query):
#         logo = LeagueImagePixel(query)
#         b64 = logo.base64
#         return {"logo": b64}

#     def league_schedule(self, query):
#         data_league = Footy.competition(query)
#         res = []
#         for game in data_league.games:
#             logo = LeagueImagePixel(data_league.id)
#             n64 = logo.base64
#             game.icon = n64
#             res.append(game.to_dict())  # type: ignore
#         return res



#     def livescore(self):
#         obj = Footy.livescore()
#         if not obj:
#             abort(404)
#         events = obj.items
#         return [g.to_dict() for g in events]  # type: ignore

#     def nowplaying(self):
#         try:
#             data = request.json
#             assert isinstance(data, dict)
#             _ = Track(**data)
#             Track.persist()
#         except AssertionError as e:
#             logging.error(e)
#         return {}

#     def stop(self):
#         return self.terminate()



# @router.get("/api/lookup", tags=["api"])
# async def read_lookup(
#     request: Request,
#     ip: str = "",
#     x_forwarded_for: str | None = Header(default=None),
# ):
#     try:
#         if not ip:
#             ip = get_remote_ip(request.client.host, x_forwarded_for)
#         assert validators.ip_address.ipv4(ip)
#         return MaxMind.lookup(ip).dict()
#     except AssertionError:
#         raise HTTPException(status_code=502)


# @router.get("/api/background/{ip}", tags=["api"])
# async def route_background(ip: str):
#     try:
#         logging.warning(ip)
#         geo_info = MaxMind.lookup(ip=ip)
#         image = LookupImage(geo=geo_info)
#         image_path = image.path
#         assert image_path
#         assert image_path.exists()
#         return {
#             "name": image_path.name,
#             "url": f"{app_config.web.backgrounds_path}/{image_path.name}",
#         }
#     except AssertionError:
#         raise HTTPException(status_code=502)
