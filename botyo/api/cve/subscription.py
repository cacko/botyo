# from botyo.api.cve.components import CVEHeader
# from hashlib import blake2b
# from botyo.server.scheduler import Scheduler
# from apscheduler.job import Job
# from botyo.server.models import ZMethod
# from botyo.server.socket.connection import Connection, UnknownClientException
# from botyo.server.models import RenderResult
# from .models import CVEResponse, CVEItem
# from .cve import CVE
# from stringcase import alphanumcase
# from botyo.core.store import RedisCachable


# class Cache(RedisCachable):

#     _struct: CVEResponse = None
#     __id = None
#     __jobId: str = None

#     def __init__(self, query: str = "", jobId: str = ""):
#         self.__query = query
#         self.__jobId = jobId

#     @property
#     def id(self):
#         if not self.__id:
#             h = blake2b(digest_size=20)
#             h.update(f"{self.__jobId}{self.__query}".encode())
#             self.__id = h.hexdigest()
#         return self.__id

#     def fetch(self, ignoreCache=False) -> CVEResponse:
#         cve = CVE(self.__query, ignoreCache=ignoreCache)
#         try:
#             response = cve.response
#             return response
#         except Exception:
#             return None

#     @property
#     def content(self) -> CVEResponse:
#         if not  self.load():
#             response =  self.fetch()
#             self._struct = self.tocache(response)
#         return self._struct

#     @property
#     def fresh(self) -> CVEResponse:
#         self._struct = self.tocache( self.fetch(ignoreCache=True))
#         return self._struct

#     @property
#     def update(self) -> list[CVEListItem]:
#         cached =  self.fromcache()
#         if not cached:
#             self.content
#             return None
#         fresh =  self.fresh
#         cacheIds = cached.ids
#         return list(
#             filter(
#                 lambda x: x.cve.CVE_data_meta.ID not in cacheIds,
#                 fresh.result.CVE_Items
#             )
#         )


# class SubscriptionMeta(type):

#     def forGroup(cls, clientId: str, groupID) -> list[Job]:
#         prefix = cls.jobPrefix(clientId, groupID)
#         return list(
#             filter(
#                 lambda g: g.id.startswith(prefix),
#                 Scheduler.get_jobs()
#             )
#         )

#     def jobPrefix(cls, clientId: str, groupId) -> str:
#         prefix = ":".join([
#             cls.__module__,
#             clientId,
#             groupId
#         ])
#         h = blake2b(digest_size=20)
#         h.update(prefix.encode())
#         return h.hexdigest()


# class Subscription(metaclass=SubscriptionMeta):

#     __groupId: list = None
#     __query: str = ""
#     __clientId: str = None
#     __client: Connection = None

#     def __init__(
#         self,
#         client: str,
#         groupID: list,
#         query: str = None
#     ) -> None:
#         self.__clientId = client
#         self.__groupId = groupID
#         self.__query = query

#     @property
#     def id(self):
#         return ":".join(
#             [
#                 __class__.jobPrefix(self.__clientId, self.__groupId),
#                 alphanumcase(self.__query),
#             ]
#         )

#     @property
#     def subscription_name(self):
#         return " - ".join(filter(None, ["CVE", self.__query]))

#     def cancel(self):
#         Scheduler.cancel_jobs(self.id)

#     @property
#     def client(self) -> Connection:
#         if not self.__client:
#             self.__client = Connection.client(self.__clientId)
#         return self.__client

#     def trigger(self):
#         client = self.client
#         if not client:
#             raise UnknownClientException
#         cache = Cache(
#             query=self.__query,
#             jobId=self.id
#         )
#         if update := self.updates( cache.update):
#             client.respond(RenderResult(
#                 method=ZMethod.CVE_ALERT,
#                 message=update,
#                 group=self.__groupId
#             ))

#     def updates(self, updated: list[CVEListItem]) -> str:
#         if not updated:
#             return None
#         rows = [
#             CVEHeader(x.id, x.description, x.severity, x.attackVector)
#             for x in updated
#         ]
#         return "\n".join(map(str, rows))

#     def schedule(self):
#         Scheduler.add_job(
#             id=self.id,
#             name=f"{self.subscription_name}",
#             func=self.trigger,
#             trigger="interval",
#             minutes=20,
#             replace_existing=True,
#             misfire_grace_time=180
#         )
