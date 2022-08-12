from hashlib import blake2b


def string_hash(s):
    h = blake2b(digest_size=20)
    h.update(s.encode())
    return h.hexdigest()


def split_with_quotes(text: str) -> list[str]:
    return [
        x.strip()
        for x in filter(
            lambda x: len(x.strip()) > 0, text.split('"' if '"' in text else " ")
        )
    ]
