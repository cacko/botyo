import os
import sys
import click
from pathlib import Path
from importlib import import_module

CONTEXT_SETTINGS = dict(auto_envvar_prefix="BOTYO")


class NotValidCommand(Exception):
    pass


class Environment:
    def __init__(self):
        self.verbose = False

    @property
    def port(self):
        return os.environ.get("BOTYO_PORT")

    @property
    def host(self):
        return os.environ.get("BOTYO_HOST")

    @property
    def redis_url(self):
        return os.environ.get("BOTYO_REDIS_URL")

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)


pass_environment = click.make_pass_decorator(Environment, ensure=True)
app_folder = Path(".") / "botyo"
app_commands_folder = app_folder / "commands"
server_commands_folder = app_folder / "server" / "commands"


class BotyoCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(app_commands_folder.absolute().as_posix()):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        for filename in os.listdir(server_commands_folder.absolute().as_posix()):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            cmd_file = f"cmd_{name}.py"
            mod = None
            if (server_commands_folder / cmd_file).exists():
                # sys.path.insert(
                #     0, app_commands_folder.parent.parent.absolute().as_posix())
                # import_module("botyo.server")
                mod = import_module(
                    f"botyo.server.commands.cmd_{name}")
            elif (app_commands_folder / cmd_file).exists():
                # sys.path.insert(
                #     0, app_commands_folder.parent.parent.absolute().as_posix())
                # import_module("botyo")
                mod = import_module(
                    f"botyo.commands.cmd_{name}")
            else:
                raise NotValidCommand
        except ImportError as e:
            print(e)
            return
        return mod.cli


@click.command(cls=BotyoCLI, context_settings=CONTEXT_SETTINGS)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode.")
@pass_environment
def cli(ctx, verbose):
    """A complex command line interface."""
    ctx.verbose = verbose


if __name__ == "__main__":
    cli()
