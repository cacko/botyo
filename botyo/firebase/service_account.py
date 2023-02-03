from pathlib import Path
from firebase_admin import credentials
from typing import Optional


class ServiceAccountMeta(type):
    _instance: Optional['ServiceAccount'] = None

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/firebase.database",
    ]

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def register(cls, service_account_file: Path):
        if not cls._instance:
            cls._instance = cls(service_account_file)
        return cls._instance

    @property
    def admin_json(cls) -> Path:
        return cls().get_admin_json()

    @property
    def credentials(cls) -> credentials.Certificate:
        return cls().get_credentials()


class ServiceAccount(object, metaclass=ServiceAccountMeta):

    __credentials: Optional[credentials.Certificate] = None
    _instance = None
    __token = None
    __admin_json: Path

    def __init__(self, admin_json: Path) -> None:
        self.__admin_json = admin_json

    def get_credentials(self) -> credentials.Certificate:
        if not self.__credentials:
            self.__credentials = credentials.Certificate(
                self.__admin_json.as_posix())
        return self.__credentials

    def get_admin_json(self) -> Path:
        return self.__admin_json

    # @property
    # def token(self):
    #     if not self.__token:
    #         r = GRequest()
    #         self.credentials.refresh(r)
    #         self.__token = self.credentials.token
    #     return self.__token

    # def getRequest(self, url, **kwargs) -> dict:
    #     return Request(url, params={"access_token": self.token}, **kwargs).json

    # def deleteRequest(self, url, **kwargs) -> dict:
    #     print(url, kwargs)
    #     return Request(url,
    #                    params={
    #                        "access_token": self.token
    #                    },
    #                    method=RequestMethod.DELETE,
    #                    **kwargs).json

    # def putRequest(self, url, data={}) -> Request:
    #     return Request(
    #         url,
    #         method=RequestMethod.PUT,
    #         params={
    #             "access_token": self.token
    #         },
    #         data=data,
    #     ).json
