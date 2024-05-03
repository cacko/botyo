from os import environ
from pathlib import Path
from typing import Any
from botyo.firebase.service_account import db, ServiceAccount

ServiceAccount.register(Path(environ.get("BOTYO_SERVICE_ACCOUNT", "")))
app = ServiceAccount.app

class OptionsDb(object):

    @property
    def root_ref(self):
        return db.reference(f"app/")

    def options(self, **kwds):
        options_ref = self.root_ref.child("options")
        return options_ref.set(kwds)


    def get_listener(self, callback):
        return self.root_ref.child("options").listen(callback)