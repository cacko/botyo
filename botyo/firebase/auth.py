from typing import Any, Optional
from .service_account import ServiceAccount
import firebase_admin
import firebase_admin.auth
from pydantic import BaseModel, Extra
import logging


class AuthUser(BaseModel, extra=Extra.ignore):
    name: str
    picture: str
    exp: int
    uid: str


# {'name': 'Alexander Spassov',
#  'picture': 'https://lh3.googleusercontent.com/a/AEdFTp4gOoL2MvPKy9dN0dmexlRZsdITMrS2bKRAsSv6FA=s96-c',
#  'iss': 'https://securetoken.google.com/botyo-6d3e4',
#  'aud': 'botyo-6d3e4',
#  'auth_time': 1675280902,
#  'user_id': 'I43ZAjTTqBMh4mdHc9SCZ9IAb533',
#  'sub': 'I43ZAjTTqBMh4mdHc9SCZ9IAb533',
#  'iat': 1675434714,
#  'exp': 1675438314,
#  'email': 'spassov@gmail.com',
#  'email_verified': True,
#  'firebase': {'identities': {'google.com': ['109560500963990770355'], 'email': ['spassov@gmail.com']}, 'sign_in_provider': 'google.com'},
#  'uid': 'I43ZAjTTqBMh4mdHc9SCZ9IAb533'}


class AuthMeta(type):
    _instance: Optional['Auth'] = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance


class Auth(object, metaclass=AuthMeta):

    def verify_token(self, token: str) -> AuthUser:
        res = firebase_admin.auth.verify_id_token(token,
                                                  app=ServiceAccount.app)
        logging.warning(f"verification res={res}")
        return AuthUser(**res)