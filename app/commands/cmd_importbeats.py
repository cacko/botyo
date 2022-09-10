from traceback import print_exc
from botyo_server.cli import pass_environment, Environment
import click
from app.commands import coro
from app.music.beats import Beats
from pathlib import Path
from prokopiy import Progress
from requests import post
from app.core.otp import OTP
import filetype
import logging


@click.command("importbeats", short_help="beats info")
@click.argument("path")
@pass_environment
@coro
def cli(ctx: Environment, path):
    queue_path = Path(path)
    processed = queue_path.parent / "processed.dat"
    queue = queue_path.read_text().split("\n")
    with processed.open("ab") as pf:
        with Progress("Importing beats...") as progress:
            for f in progress.track(queue):
                fp = Path(f.strip())
                if filetype.is_image(fp.as_posix()):
                    pf.write(f"{f}\n".encode())
                    continue
                try:
                    beats = Beats(fp.as_posix())
                    tempo = beats.tempo
                    beats_list = beats.beats
                    progress.console.print(
                        f"{beats.path}: beats: {len(beats_list)}, tempo: {tempo}"
                    )
                    try:
                        resp = post(
                            "http://192.168.0.107:7988/beats",
                            headers=OTP("YKXJZI2KGBLF4FPNRDLWETQ4VVNCWTXT").headers,
                            json={
                                "path": beats.path.as_posix(),
                                "tempo": tempo,
                                "beats": beats_list,
                            },
                        )
                        logging.info(f"{resp.status_code}")
                    except Exception as e:
                        logging.error(e)
                    pf.write(f"{f}\n".encode())
                except Exception as e:
                    print_exc(e)
                    logging.error(e)
