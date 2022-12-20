from typing import Optional


def to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except ValueError:
        return None
