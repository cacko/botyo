from pixelme import Pixelate
from pathlib import Path


def pixelme_b64(
    image_path: Path,
    padding=200,
    grid_lines=True,
    block_size=25,
    resize=None
) -> str:
    pix = Pixelate(
        input=image_path,
        padding=padding,
        grid_lines=grid_lines,
        block_size=block_size
    )
    if resize:
        pix.resize(resize)
    return pix.base64
