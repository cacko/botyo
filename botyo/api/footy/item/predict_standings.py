from botyo.api.footy.item.predict import Predict
from botyo.predict.db.models.user import DbUser
from botyo.server.output import Align, Column, TextOutput


class PredictStandings(Predict):
    
    def columns(self):
        return (
            Column(size=2, align=Align.LEFT, title="#"),
            Column(
                size=12,
                align=Align.LEFT,
                title="Player",
            ),
            Column(size=2, align=Align.RIGHT, title="PT"),
            Column(size=2, align=Align.RIGHT, title="PL"),
            Column(size=2, align=Align.RIGHT, title="W"),
            Column(size=2, align=Align.RIGHT, title="D"),
            Column(size=2, align=Align.RIGHT, title="L"),
        )
    
    
    def standings(self):
        rows = []
        pos = 1
        for user in DbUser.by_points():
            rows.append(
                [
                    f"{pos}",
                    user.display_name,
                    f"{user.points:.0f}",
                    f"{user.played:.0f}",
                    f"{user.wins}",
                    f"{user.draws}",
                    f"{user.losses}"
                ]
            )
            pos += 1
        TextOutput.addTable(self.columns(), rows)
        return TextOutput.render()