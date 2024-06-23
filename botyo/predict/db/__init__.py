from .database import Database
from .models import User, Prediction, Game


class PredictionNotAllow(Exception):
    pass

def create_tables(drop=True):
    tables = [
        Prediction,
        User,
        Game
    ]
    if drop:
        Database.db.drop_tables(tables)
    Database.db.create_tables(tables)
