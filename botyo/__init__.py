import os
import logging
from cachable.storage.redis import RedisStorage
from cachable.storage.file import FileStorage
from botyo.core.config import Config as app_config
from botyo.api.footy import Footy
from botyo.server.server import Server
from botyo.firebase.service_account import ServiceAccount
from botyo.server.rest.server import APIServer
from botyo.firebase.firestore import FirestoreClient
from botyo.firebase.listener import CleaningServer
from pathlib import Path
import signal
import sys
import corelog

corelog.register(os.environ.get("BOTYO_LOG_LEVEL", "INFO"))
ServiceAccount.register(Path(os.environ.get("BOTYO_SERVICE_ACCOUNT", "")))
RedisStorage.register(os.environ.get("BOTYO_REDIS_URL", ""))
FileStorage.register(Path(app_config.cachable.path))

app = Server(Path(__file__).parent.parent)
app.servers.append(APIServer())
app.servers.append(CleaningServer(db=FirestoreClient.db))

Footy.register(app)


def create_app():

    from botyo.api.kb import bp as wiki_bp
    from botyo.api.avatar import bp as avatar_bp
    from botyo.api.console import bp as console_Bp
    from botyo.api.cve import bp as cve_bp
    from botyo.api.name import bp as name_bp
    from botyo.api.music import bp as music_bp
    from botyo.api.ontv import bp as ontv_bp
    from botyo.api.logo import bp as logo_bp
    from botyo.api.footy import bp as footy_bp
    from botyo.api.chat import bp as chat_bp
    from botyo.api.text import bp as text_bp
    from botyo.api.translate import bp as translate_bp
    from botyo.api.image import bp as image_bp
    from botyo.api.meme import bp as meme_bp
    from botyo.api.code import bp as code_bp

    avatar_bp.register(app)
    console_Bp.register(app)
    cve_bp.register(app)
    name_bp.register(app)
    music_bp.register(app)
    logo_bp.register(app)
    ontv_bp.register(app)
    wiki_bp.register(app)
    footy_bp.register(app)
    chat_bp.register(app)
    text_bp.register(app)
    translate_bp.register(app)
    image_bp.register(app)
    meme_bp.register(app)
    code_bp.register(app)
    return app


def handler_stop_signals(signum, frame):
    logging.info("Stopping app")
    app.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
