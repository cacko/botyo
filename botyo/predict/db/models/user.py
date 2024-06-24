from typing import Generator
from psycopg2 import IntegrityError
from botyo.predict.db.database import Database
from .base import DbModel
from peewee import CharField, IntegerField, prefetch


class DbUser(DbModel):
    phone = CharField(null=False, unique=True)
    name = CharField(null=True)
    wins = IntegerField(default=0)
    draws = IntegerField(default=0)
    losses = IntegerField(default=0)
    points = IntegerField(default=0)

    @classmethod
    def by_points(cls) -> Generator["DbUser", None, None]:
        query = cls.select().order_by(cls.points.desc())
        yield from query

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["DbUser", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        phone = kwargs.get("phone")
        query = query.where((cls.phone == phone))

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                if defaults:
                    kwargs.update(defaults)
                return cls.create(**kwargs), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    def add_points(self, points: int):
        self.points += points
        match points:
            case 3:
                self.wins += 1
            case 1:
                self.draws += 1
            case 0:
                self.losses += 1
        self.save(only=["points", "wins", "draws", "losses"])

    @property
    def played(self):
        return sum([self.wins, self.draws, self.losses])

    @property
    def display_name(self) -> str:
        try:
            assert self.name
            return self.name
        except AssertionError:
            pass
        return self.phone

    class Meta:
        database = Database.db
        table_name = "predict_user"
