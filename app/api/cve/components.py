from botyo_server.output import Align, Column, TextOutput
from collections import namedtuple
from textwrap import wrap

CVEBasics = namedtuple(
    "CVEBasics", "id,description,severity,attackVector", defaults=[""]
)


class CVEHeader:

    row: CVEBasics = None

    def __init__(self, id, description, severity, attackVector):
        self.row = CVEBasics(
            id=id, description=description,
            severity=severity,
            attackVector=attackVector
        )

    def __str__(self) -> str:
        cols = (
            Column(size=42, align=Align.CENTER),
        )
        row = "-".join(filter(None, [
            self.row.id,
            self.row.severity.upper(),
            self.row.attackVector.upper(),
        ]))
        TextOutput.addColumns(cols, [[row]])
        TextOutput.addRows(wrap(self.row.description, width=42))
        TextOutput.addRows(["\n"])
        return TextOutput.render()
