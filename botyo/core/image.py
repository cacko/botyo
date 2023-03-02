from pixelme import Pixelate
from pathlib import Path
from corefile import TempPath
from uuid import uuid4
import requests
import shutil


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


def download_image(url: str) -> TempPath:
    tmp_file = TempPath(f"{uuid4()}.jpg")
    response = requests.get(url, stream=True)
    with tmp_file.open("wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return tmp_file
