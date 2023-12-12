from botyo.server.output import TextOutput
from botyo.threesixfive.item.facts import Facts as FactsData
from typing import Optional

class Facts(FactsData):

    @property
    def message(self) -> Optional[str]:
        facts = self.facts
        if not facts:
            return None
        TextOutput.addRows([f"* {x.text}\n" for x in facts])
        return TextOutput.render()