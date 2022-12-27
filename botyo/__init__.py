import os
import logging
import structlog
from cachable.storage.redis import RedisStorage
from cachable.storage.file import FileStorage
from botyo.core.config import Config as app_config
from botyo.api.footy import Footy
from botyo.server.server import Server
from pathlib import Path
from botyo.api.server import APIServer
import signal
import sys
import colorama


RESET_ALL = colorama.Style.RESET_ALL
BRIGHT = colorama.Style.BRIGHT
DIM = colorama.Style.DIM
RED = colorama.Fore.RED
BLUE = colorama.Fore.BLUE
CYAN = colorama.Fore.CYAN
MAGENTA = colorama.Fore.MAGENTA
YELLOW = colorama.Fore.YELLOW
GREEN = colorama.Fore.GREEN
RED_BACK = colorama.Back.RED


class _ColorfulStyles:
    reset = RESET_ALL
    bright = BRIGHT

    level_critical = RED
    level_exception = RED
    level_error = RED
    level_warn = YELLOW
    level_info = GREEN
    level_debug = GREEN
    level_notset = RED_BACK

    timestamp = DIM
    logger_name = BLUE
    kv_key = CYAN
    kv_value = MAGENTA


structlog.configure(
    processors=[
        # Prepare event dict for `ProcessorFormatter`.
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(
            exception_formatter="better_traceback",
            level_styles=_ColorfulStyles
        )
    ],
)

handler = logging.StreamHandler()
# Use OUR `ProcessorFormatter` to format all `logging` entries.
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(
    getattr(logging, os.environ.get("BOTYO_LOG_LEVEL", "INFO"))
)


app = Server(Path(__file__).parent.parent)
app.servers.append(APIServer())

RedisStorage.register(os.environ.get("BOTYO_REDIS_URL", ""))
FileStorage.register(Path(app_config.cachable.path))

Footy.register(app)


def create_app():

    from botyo.api.kb import bp as wiki_bp
    from botyo.api.avatar import bp as avatar_bp
    from botyo.api.console import bp as console_Bp
    from botyo.api.cve import bp as cve_bp
    from botyo.api.name import bp as name_bp
    from botyo.api.music import bp as music_bp
    from botyo.api.ontv import bp as ontv_bp
    from botyo.api.photo import bp as photo_bp
    from botyo.api.logo import bp as logo_bp
    from botyo.api.footy import bp as footy_bp
    from botyo.api.chat import bp as chat_bp
    from botyo.api.text import bp as text_bp
    from botyo.api.translate import bp as translate_bp
    from botyo.api.image import bp as image_bp

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
