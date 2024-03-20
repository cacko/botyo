from datetime import datetime
import logging
from typing import Any, Optional
from botyo.firebase.service_account import db, ServiceAccount

app = ServiceAccount.get_app()

class OptionsDb(object):

    @property
    def root_ref(self):
        return db.reference(f"app/image")

    def options(self, **kwds):
        options_ref = self.root_ref.child("options")
        return options_ref.set(kwds)


    def get_listener(self, callback):
        return self.root_ref.child("options").listen(callback)