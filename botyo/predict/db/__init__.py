from .database import Database
from .models import User, Prediction, Game


def create_tables(drop=False):
    tables = [User, Game, Prediction]
    if drop:
        Database.db.drop_tables(tables)
    Database.db.create_tables(tables)
