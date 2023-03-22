from dataclasses_json import dataclass_json, Undefined
from botyo.server.output import Align, Column, TextOutput
from botyo.server.models import (
    CoreMethods,
    ZSONMatcher,
    ZSONRequest,
    CommandDef,
    ZMethod,
)
from fuzzelinho import Match, MatchMethod
from typing import Callable, Optional
from itertools import groupby
from pydantic.dataclasses import dataclass
from pydantic import Field


class CommandExecMeta(type):
    registered: list['CommandDef'] = []

    def parse(
        cls,
        message: str,
        **kwds
    ) -> tuple[Optional["CommandDef"], Optional[str]]:
        message = message.lower()
        trigger, args = [*message.split(" ", 1), ""][:2]
        triggers = filter(lambda x: not x.matcher, cls.registered)
        return (
            next(
                filter(
                    lambda x: any([
                        x.method.value.split(":")[-1] == trigger,
                        len(trigger) > 2 and
                        (x.method.value if ":" in trigger else x.method.value.
                         split(":")[-1]).startswith(trigger),
                    ]),
                    triggers,
                ),
                None,
            ),
            args,
        )

    @property
    def definitions(cls) -> list[CommandDef]:
        definitions = []

        def keyfunc(x):
            return x.method.value

        for cmd in sorted(cls.registered, key=keyfunc):
            definitions.append(
                CommandDef(
                    method=cmd.method,
                    desc=cmd.desc,
                    matcher=cmd.matcher,
                    response=cmd.response,
                    icon=cmd.icon,
                    subscription=cmd.subscription,
                    args=cmd.args,
                    upload=cmd.upload,
                    uses_prompt=cmd.uses_prompt
                )
            )

        cols = [
            Column(size=42, align=Align.LEFT),
        ]
        rows = []
        for g, c in groupby(filter(lambda x: x.desc is not None, definitions),
                            key=lambda x: x.namespace):
            rows.append([g.upper()])
            rows = [*rows, *[[f"{d.action} - {d.desc}"] for d in c]]

        TextOutput.addColumns(cols, rows)

        definitions.append(
            CommandDef(method=CoreMethods.HELP, response=TextOutput.render()))
        return definitions


@dataclass
class CommandExec(metaclass=CommandExecMeta):
    method: ZMethod | CoreMethods
    handler: Callable
    desc: Optional[str] = None
    matcher: Optional[ZSONMatcher] = None
    response: Optional[str] = None
    subscription: bool = Field(default=False)
    icon: Optional[str] = None
    args: Optional[str] = None
    upload: bool = Field(default=False)
    uses_prompt: bool = Field(default=False)

    @property
    def trigger(self) -> str:
        return self.method.value

    @classmethod
    def triggered(cls, method: ZMethod | CoreMethods, message: ZSONRequest):
        return next(
            filter(
                lambda x: method == x.method,
                cls.registered,
            ),
            None,
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandMatch(Match):
    minRatio = 85
    extensionMatching = False
    method = MatchMethod.WRATIO


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandMatchNeedle:
    trigger: str
