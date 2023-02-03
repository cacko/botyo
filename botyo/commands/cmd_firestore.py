
from botyo.cli import pass_environment, Environment
import click
from botyo.commands import coro
from botyo.firebase.service_account import ServiceAccount
import os
from botyo.firebase.firestore import FirestoreClient
from botyo.firebase.auth import Auth
from pathlib import Path
import logging

ServiceAccount.register(Path(os.environ.get("BOTYO_SERVICE_ACCOUNT", "")))


@click.command("firestore", short_help="firestore tests")
@click.argument("token")
@pass_environment
@coro
def cli(ctx: Environment, token: str):
    print(Auth.verify(token))