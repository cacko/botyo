from .base import Base
import validators
from argparse import ArgumentTypeError


class WhoIs(Base):

    command = "whois"

    def validate(self):
        if not any([validators.domain(x) for x in self.args]):
            raise ArgumentTypeError
