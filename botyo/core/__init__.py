from typing import Optional
from contextlib import contextmanager
import logging
import time

def to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except ValueError:
        return None


def to_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except ValueError:
        return None

@contextmanager
def perftime(name, silent=False):
    st = time.perf_counter()
    try:
        yield
    finally:
        if not silent:
            total = time.perf_counter() - st
            logging.info(f"{name} -> {total}s")
