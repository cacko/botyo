__all__ = ["UA"]

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


class UAMeta(type):

    @property
    def random(cls) -> str:
        return cls.instance.getRandomUserAgent()

    @property
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance


class UA(object, metaclass=UAMeta):

    rotator: UserAgent = None
    _instance = None

    def __init__(self):
        software = [SoftwareName.CHROME.value]
        systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
        self.rotator = UserAgent(
            software_names=software, operating_systems=systems, limit=100
        )

    def __new__(cls,  *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def getRandomUserAgent(self) -> str:
        return self.rotator.get_random_user_agent()
