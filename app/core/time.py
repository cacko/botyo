from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
import arrow
import time
from contextlib import contextmanager
import logging
from app.core import logger


def seconds_to_duration(s):
    delta = timedelta(seconds=s)
    res = str(delta)
    return res[2:7]


def elapsed_duration(start):
    delta = datetime.now(tz=timezone.utc) - start
    res = str(delta)
    return res[2:7]


def isodate_encoder(d):
    pass


def isodate_decoder(d):
    ar = arrow.get(d)
    return ar.datetime


def time_hhmm(dt: datetime, tz: ZoneInfo):
    return dt.astimezone(tz).strftime("%H:%M")


def time_hhmmz(dt: datetime, tz: ZoneInfo):
    df = dt.astimezone(tz)
    return f"{df.strftime('%H:%M')} {df.tzname()}"


@contextmanager
def perftime(name):
    st = time.perf_counter()
    try:
        yield
    finally:
        total = time.perf_counter() - st
        logger.info(f"{name} -> {total}s")
