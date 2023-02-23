import beets
from beets.ui import config as beets_config
from botyo.core.config import Config as app_config

beets_config.set_file(app_config.music.beets_config)
beets_library = beets.ui._open_library(beets.config)
