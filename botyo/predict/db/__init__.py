from .database import Database
from .models.user import DbUser
from .models.prediction import DbPrediction
from .models.game import DbGame


def create_tables(drop=True):
    tables = [
        DbPrediction,
        DbUser,
        DbGame
    ]
    if drop:
        Database.db.drop_tables(tables)
    Database.db.create_tables(tables)
