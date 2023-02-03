from typing import Generator, Any
from .service_account import ServiceAccount
from google.cloud.firestore_v1.document import (DocumentReference)
from google.cloud.firestore import Client, CollectionReference
import firebase_admin
from firebase_admin import firestore


class FirestoreClientMeta(type):
    _instance = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwds)
        return cls._instance


class FirestoreClient(object, metaclass=FirestoreClientMeta):

    BATCH_SIZE = 200
    __batch = None
    __batchIds = []

    def __init__(self):
        app = firebase_admin.initialize_app(ServiceAccount.credentials)
        self.__client = firestore.client()

    def collections(self,
                    path=None) -> Generator[CollectionReference, None, None]:
        if not path:
            yield from self.__client.collections()
        else:
            ref = self.__client.document(path)
            yield from ref.collections()

    # def documents(
    #     self, collection: CollectionReference
    # ) -> Generator[DocumentReference, None, None]:
    #     yield from collection.list_documents()

    # def document(self, path) -> DocumentReference:
    #     return self.__client.document(path)

    # def collection(self, path) -> CollectionReference:
    #     return self.__client.collection(path)

    # def delete(self, path):

    #     self.__batch = self.__client.batch()
    #     parts = path.split("/")

    #     if len(parts) % 2 == 0:
    #         ref = self.__client.document(path)
    #         for cl in self.collections(ref.path):
    #             self.delete_collection(cl)
    #         ref.delete()
    #     else:
    #         print("/".join(parts[:-1]))
    #         res = self.delete_collection(self.__client.collection(path))
    #         self.__batch.commit()
    #         return res

    # def delete_collection(self, coll_ref: CollectionReference):
    #     if not self.__deleteProgress:
    #         self.__deleteProgress = Progress(total=self.BATCH_SIZE,
    #                                          desc="Deleting")
    #     deleted = 0
    #     for doc in self.documents(coll_ref):
    #         for cl in self.collections(doc.path):
    #             self.delete_collection(cl)
    #         self.__batch.delete(doc)
    #         self.__batchIds.append(doc.id)
    #         self.__deleteProgress.desc = f"{doc.id} {doc.parent.id}"
    #         self.__deleteProgress.update()
    #         if len(self.__batchIds) > self.BATCH_SIZE:
    #             self.__batch.commit()
    #             self.__batchIds = []
    #             self.__deleteProgress.reset()
    #         deleted += 1