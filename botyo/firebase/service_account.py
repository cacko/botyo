from pathlib import Path
from firebase_admin import credentials
from typing import Optional


class ServiceAccountMeta(type):
    _instance: Optional['ServiceAccount'] = None
    __admin_json: Optional[Path] = None

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/firebase.database",
    ]

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def register(cls, service_account_file: Path):
        cls.__admin_json = service_account_file

    @property
    def admin_json(cls) -> Path:
        assert cls.__admin_json
        return cls.__admin_json

    @property
    def credentials(cls) -> credentials.Certificate:
        return cls().get_credentials()


class ServiceAccount(object, metaclass=ServiceAccountMeta):

    __credentials: Optional[credentials.Certificate] = None

    def get_credentials(self) -> credentials.Certificate:
        if not self.__credentials:
            self.__credentials = credentials.Certificate(
                __class__.admin_json.as_posix())
        return self.__credentials
