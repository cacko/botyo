

from dataclasses_json import dataclass_json, Undefined
from botyo.server.output import Align, Column, TextOutput
from botyo.server.models import (
    CoreMethods,
    ZSONMatcher,
    ZSONRequest,
    Method,
    CommandDef
)
from fuzzelinho import Match, MatchMethod
from dataclasses import dataclass
from typing import Callable, Optional
from itertools import groupby


class CommandExecMeta(type):
    registered = []

    def parse(
        cls, message: str, **kwds
    ) -> tuple[Optional["CommandDef"], Optional[str]]:
        message = message.lower()
        trigger, args = [*message.split(" ", 1), ""][:2]
        triggers = filter(lambda x: not x.matcher, cls.registered)
        return (
            next(
                filter(
                    lambda x: any(
                        [
                            x.method.value.split(":")[-1] == trigger,
                            len(trigger) > 2
                            and (
                                x.method.value
                                if ":" in trigger
                                else x.method.value.split(":")[-1]
                            ).startswith(trigger),
                        ]
                    ),
                    triggers,
                ),
                None,
            ),
            args,
        )

    @property
    def definitions(cls) -> list[CommandDef]:
        definitions = []
        def keyfunc(x): return x.method.value

        for cmd in sorted(cls.registered, key=keyfunc):

            definitions.append(CommandDef(
                method=cmd.method,
                desc=cmd.desc,
                matcher=cmd.matcher,
                response=cmd.response
            ))

        cols = [
            Column(size=42, align=Align.LEFT),
        ]
        rows = []
        for g, c in groupby(filter(
            lambda x: x.desc is not None, definitions),
            key=lambda x: x.namespace
        ):
            rows.append([g.upper()])
            rows = [*rows, *[[f"{d.action} - {d.desc}"] for d in c]]

        TextOutput.addColumns(cols, rows)

        definitions.append(CommandDef(
            method=CoreMethods.HELP,
            response=TextOutput.render()
        ))
        return definitions


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandExec(metaclass=CommandExecMeta):
    method: Method
    handler: Callable
    desc: Optional[str] = None
    matcher: Optional[ZSONMatcher] = None
    response: Optional[str] = None

    @property
    def trigger(self) -> str:
        return self.method.value

    @classmethod
    def triggered(cls, method: Method, message: ZSONRequest):
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
    method = MatchMethod.PARTIALSET


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandMatchNeedle:
    trigger: str
