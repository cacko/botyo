from app.core import logger
from app.api.footy.footy import Footy
from app.api.footy.item.subscription import Subscription
from app.core.config import Config
from app.core.otp import OTP
from botyo_server.scheduler import Scheduler
from app.threesixfive.item.models import CancelJobEvent
from app.threesixfive.item.team import Team as DataTeam
from app.threesixfive.item.league import LeagueImagePixel
from app.music.beats import Beats
from app.music.nowplay import Track
from app.api.logo.team import TeamLogoPixel
from requests import post
from botyo_server.core import AppServer
from butilka.server import Server, request, abort

class _APIServer(Server):

    def __init__(self, *args, **kwargs):
        api_config = Config.api
        super().__init__(host=api_config.host, port=api_config.port, *args, **kwargs)
        self.setup_routing()

    def setup_routing(self):
        self.app.route("/subscribe", "POST", self.subscribe)
        self.app.route("/nowplaying", "POST", self.nowplaying)
        self.app.route("/team_schedule/<query>", "GET", self.team_schedule)
        self.app.route("/team_logo/<query>", "GET", self.team_logo)
        self.app.route("/league_logo/<query>", "GET", self.league_logo)
        self.app.route("/livescore", "GET", self.livescore)
        self.app.route("/subscriptions", "POST", self.subscriptions)
        self.app.route("/unsubscribe", "POST", self.unsubscribe)
        self.app.route("/beats", "GET", self.beats)
        self.app.route("/subscribe", "POST", self.subscribe)

    def subscribe(self):
        data = request.json
        res = Footy.subscribe(
            client=f"{data.get('webhook')}",
            groupID=f"{data.get('group')}",
            query=f"{data.get('id')}",
        )
        return {"message": res}

    def subscriptions(self):
        data = request.json
        res = Subscription.forGroup(client=data.get("webhook"), group=data.get("group"))
        return [{"id": job.id, "text": job.name} for job in res]

    def unsubscribe(self):
        data = request.json
        subs = Subscription.forGroup(
            client=data.get("webhook"), group=data.get("group")
        )
        id_parts = data.get("id").split(":")
        for sub in subs:
            if sub.id.startswith(id_parts[0]):
                Scheduler.cancel_jobs(sub.id)
                post(
                    data.get("webhook"),
                    headers=OTP(data.get("group")).headers,
                    json=CancelJobEvent(job_id=id_parts[0]).to_dict(),
                )
                return {"message": f"unsubscribed from {sub.name}"}
        return {"message": "nothing unsubscribed"}

    def team_logo(self, query):
        logo = TeamLogoPixel(query)
        b64 = logo.base64
        return {"logo": b64}

    def beats(self):
        path = request.query.path
        try:
            beats = Beats(path=path)
            return beats.model.to_dict()
        except FileNotFoundError:
            abort(404)

    def league_logo(self):
        query = request.match_info.get("query")
        logo = LeagueImagePixel(query)
        b64 = logo.base64
        return {"logo": b64}

    def team_schedule(self, query):
        if not query:
            abort(404)
        try:
            team_id = int(query)
            data_team = DataTeam(team_id)
            data = data_team.team
            res = []
            for game in data.games:
                logo = LeagueImagePixel(game.competitionId)
                n64 = logo.base64
                game.icon = n64
                res.append(game.to_dict())
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
            res.append(game.to_dict())
        return res

    def livescore(self):
        obj = Footy.livescore()
        if not obj:
            abort(404)
        events = obj.items
        return [g.to_dict() for g in events]

    def nowplaying(self):
        data = request.json
        _ = Track(**data)
        Track.persist()
        return {}
    
    def stop(self):
        return self.terminate()


class APIServer(AppServer):
    def __init__(self) -> None:
        worker = _APIServer()
        super().__init__(worker)

    def stop(self):
        try:
            self.worker.terminate()
        except Exception as e:
            logger.exception(e)
        return super().stop()
