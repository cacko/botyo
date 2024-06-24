from .database import Database
from .models import DbUser, DbPrediction, DbGame


def create_tables(drop=True):
    tables = [
        DbPrediction,
        DbUser,
        DbGame
    ]
    if drop:
        Database.db.drop_tables(tables)
    Database.db.create_tables(tables)
