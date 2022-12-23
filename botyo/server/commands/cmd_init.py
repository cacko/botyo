from botyo.cli import pass_environment, Environment
import click
from textacy.datasets import CapitolWords
from textacy.resources import DepecheMood
from textacy.lang_id import LangIdentifier


@click.command("init", short_help="Initializes a textacy.")
@pass_environment
def cli(ctx: Environment):
    CapitolWords().download()
    DepecheMood().download()
    LangIdentifier(version=2.0).download()
