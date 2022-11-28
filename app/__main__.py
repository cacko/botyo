from cachable.storage.redis import RedisStorage
from cachable.storage.file import FileStorage
from app.core.config import Config as app_config
from app.api.footy import Footy
from botyo_server.server import Server
import os
from pathlib import Path
from app.api.server import APIServer
import logging
import signal
import sys


app = Server(Path(__file__).parent.parent)
app.servers.append(APIServer())

RedisStorage.register(os.environ.get("BOTYO_REDIS_URL", ""))
FileStorage.register(Path(app_config.cachable.path))

Footy.register(app)


def create_app():

    from app.api.kb import bp as wiki_bp
    from app.api.avatar import bp as avatar_bp
    from app.api.console import bp as console_Bp
    from app.api.cve import bp as cve_bp
    from app.api.name import bp as name_bp
    from app.api.music import bp as music_bp
    from app.api.ontv import bp as ontv_bp
    from app.api.photo import bp as photo_bp
    from app.api.logo import bp as logo_bp
    from app.api.footy import bp as footy_bp
    from app.api.chat import bp as chat_bp
    from app.api.text import bp as text_bp
    from app.api.translate import bp as translate_bp
    from app.api.image import bp as image_bp

    avatar_bp.register(app)
    console_Bp.register(app)
    cve_bp.register(app)
    name_bp.register(app)
    music_bp.register(app)
    logo_bp.register(app)
    ontv_bp.register(app)
    photo_bp.register(app)
    wiki_bp.register(app)
    footy_bp.register(app)
    chat_bp.register(app)
    text_bp.register(app)
    translate_bp.register(app)
    image_bp.register(app)
    return app


def handler_stop_signals(signum, frame):
    logging.warning("Stopping app")
    app.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
