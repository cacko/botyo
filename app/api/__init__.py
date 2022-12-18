from enum import Enum
from botyo_server.models import Method


class ZMethod(Method, Enum):
    LOGIN = "login"
    KNOWLEDGE_ARTICLE = "kb:article"
    KNOWLEDGE_ASK = "kb:ask"
    KNOWLEDGE_TELL = "kb:tell"
    KNOWLEDGE_WTF = "kb:wtf"
    AVATAR_AVATAR = "avatar:avatar"
    AVATAR_RUSSIA = "avatar:avaru"
    AVATAR_UKRAINE = "avatar:avauk"
    CONSOLE_TRACEROUTE = "console:traceroute"
    CONSOLE_TCPTRACEROUTE = "console:tcptraceroute"
    CONSOLE_DIG = "console:dig"
    CONSOLE_WHOIS = "console:whois"
    CONSOLE_GEO = "console:geo"
    CVE_CVE = "cve:cve"
    # CVE_ALERT = "cve:alert"
    # CVE_UNALERT = "cve:unalert"
    # CVE_LISTALERTS = "cve:listalerts"
    NAME_GENDER = "name:gender"
    NAME_RACE = "name:race"
    LOGO_TEAM = "logo:team"
    MUSIC_SONG = "music:song"
    MUSIC_ALBUMART = "music:albumart"
    MUSIC_LYRICS = "music:lyrics"
    MUSIC_NOWPLAYING_SONG = "music:nowsong"
    MUSIC_NOWPLAYING_ART = "music:nowart"
    ONTV_TV = "ontv:tv"
    PHOTO_FAKE = "photo:fake"
    HELP = "help"
    FOOTY_STANDINGS = "ft:standings"
    FOOTY_LEAGUES = "ft:leagues"
    FOOTY_FACTS = "ft:facts"
    FOOTY_LINEUP = "ft:lineup"
    FOOTY_SCORES = "ft:games"
    FOOTY_PLAYER = "ft:player"
    FOOTY_STATS = "ft:stats"
    FOOTY_SUBSCRIBE = "ft:subscribe"
    FOOTY_UNSUBSCRIBE = "ft:unsubscribe"
    FOOTY_SUBSCRIPTIONS = "ft:listsubscriptions"
    FOOTY_FIXTURES = "ft:fixtures"
    FOOTY_GOALS = "ft:goals"
    FOOTY_LIVE = "ft:live"
    FOOTY_TEAM = "ft:team"
    CHAT_DIALOG = "chat:dialog"
    CHAT_PHRASE = "chat:phrase"
    CHAT_REPLY = "chat:reply"
    TEXT_GENERATE = "text:generate"
    TEXT_DETECT = "text:detect"
    TRANSLATE_EN_ES = "translate:en_es"
    TRANSLATE_ES_EN = "translate:es_en"
    TRANSLATE_EN_BG = "translate:en_bg"
    TRANSLATE_BG_EN = "translate:bg_en"
    TRANSLATE_EN_CS = "translate:en_cs"
    TRANSLATE_CS_EN = "translate:cs_en"
    TRANSLATE_EN_PL = "translate:en_pl"
    TRANSLATE_PL_EN = "translate:pl_en"
    TRANSLATE_SQ_EN = "translate:sq_en"
    TRANSLATE_EN_SQ = "translate:en_sq"
    IMAGE_ANALYZE = "image:analyze"
    IMAGE_TAG = "image:tag"
    IMAGE_HOWCUTE = "image:howcute"
    IMAGE_CLASSIFY = "image:classify"
    IMAGE_PIXEL = "image:pixel"
    IMAGE_POLYGON = "image:polygon"
    IMAGE_WALLPAPER = "image:wallpaper"
    IMAGE_VARIATION = "image:variation"
    IMAGE_POKEMON = "image:pokemon"
    INAGE_TXT2IMG = "image:txt2img"
    EVENT_COUNTDOWN = "event:countdown"
    EVENT_CALENDAR = "event:calendar"
    EVENT_SCHEDULE = "event:schedule"
    EVENT_CANCEL = "event:cancel"
