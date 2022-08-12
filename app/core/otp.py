import pyotp


class OTPMeta(type):

    _instances = {}

    def __call__(self, secret: str, *args, **kwds):
        if secret not in self._instances:
            self._instances[secret] = super().__call__(secret, *args, **kwds)
        return self._instances[secret]


class OTP(object, metaclass=OTPMeta):

    __totp = None

    def __init__(self, secret) -> None:
        self.__totp = pyotp.TOTP(secret)

    def verify(self, code: str) -> bool:
        return self.__totp.verify(code)

    @property
    def now(self) -> str:
        return self.__totp.now()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Cache-Control": "no-cache",
            'X-TOTP': self.now
        }
