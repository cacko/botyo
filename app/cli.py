import click
from app.goals import Goals
import logging

class ZnaykoCommand(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self.commands)


@click.group(cls=ZnaykoCommand)
def cli():
    """This script showcases different terminal UI helpers in Click."""
    pass

@cli.command("goals", short_help="Goals")
@click.argument("query", nargs=-1)
@click.pass_context
def cli_goals(ctx: click.Context, query: list[str]):


if __name__ == "__main__":
    cli()