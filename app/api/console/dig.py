from argparse import ArgumentTypeError
import validators
from .base import Base


class Dig(Base):

    command = "dig"

    def validate(self):
        if not any([any(
            [validators.domain(x), validators.ipv4(x)]
        ) for x in self.args]):
            raise ArgumentTypeError
