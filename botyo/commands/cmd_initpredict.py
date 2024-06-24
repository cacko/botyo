import logging
from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.predict.db.models import Prediction, User, Game


@click.command("initpredict", short_help="init predict db")
@pass_environment
@coro
def cli(ctx: Environment):
    for pred in Prediction.calculate_missing():
        try:
            model = pred.on_ended()
            assert model
            print(model)
            print(model.User)
        except AssertionError:
            print(f"{pred} not calculated")
        