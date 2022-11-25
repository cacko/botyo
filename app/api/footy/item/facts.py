from botyo_server.output import TextOutput
from app.threesixfive.item.facts import Facts as FactsData


class Facts(FactsData):

    @property
    def message(self) -> str:
        facts = self.facts
        if not facts:
            return None
        TextOutput.utf8mono = True
        TextOutput.addRows([f"* {x.text}\n" for x in facts])
        return TextOutput.render()
