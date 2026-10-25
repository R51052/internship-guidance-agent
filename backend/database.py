"""Small repository contract shared by PyMongo and explicit offline demo mode."""
from copy import deepcopy
from datetime import date, datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure, ServerSelectionTimeoutError


class ConflictError(Exception):
    pass


def serialize(value: Any):
    """Return JSON-compatible values without mutating database documents."""
    if isinstance(value, dict):
        return {("id" if key == "_id" else key): serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


class MemoryRepository:
    """Thread-safe process-local data; never used as an implicit Mongo fallback."""
    mode = "demo"

    def __init__(self):
        self._collections: dict[str, dict[str, dict]] = {}
        self._lock = RLock()

    def find(self, collection, filters=None):
        with self._lock:
            return deepcopy([doc for doc in self._collections.get(collection, {}).values()
                             if all(doc.get(key) == value for key, value in (filters or {}).items())])

    def get(self, collection, identifier):
        with self._lock:
            return deepcopy(self._collections.get(collection, {}).get(str(identifier)))

    def one(self, collection, filters):
        return next(iter(self.find(collection, filters)), None)

    def insert(self, collection, document):
        with self._lock:
            docs = self._collections.setdefault(collection, {})
            if document["id"] in docs or (collection == "users" and any(
                    doc["email"] == document["email"] for doc in docs.values())):
                raise ConflictError("Document already exists")
            docs[document["id"]] = deepcopy(document)
            return deepcopy(document)

    def upsert(self, collection, identifier, document):
        with self._lock:
            value = {**deepcopy(document), "id": str(identifier)}
            self._collections.setdefault(collection, {})[str(identifier)] = value
            return deepcopy(value)

    def delete(self, collection, identifier):
        with self._lock:
            return self._collections.get(collection, {}).pop(str(identifier), None) is not None

    def ping(self):
        return True

    def close(self):
        pass


class MongoRepository:
    mode = "mongodb"

    def __init__(self, uri, database):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000, tz_aware=True)
        self.db = self.client[database]
        try:
            self.ping()
        except OperationFailure as exc:
            self.client.close()
            raise RuntimeError(
                "MongoDB authentication failed. Check the Atlas database username, password, and cluster URI in backend/.env."
            ) from exc
        except ServerSelectionTimeoutError as exc:
            self.client.close()
            raise RuntimeError(
                "MongoDB is unreachable. Check Atlas Network Access, the cluster URI, and your internet connection."
            ) from exc
        self.db.users.create_index("email", unique=True)
        for collection in ("users", "profiles", "internships", "favorites", "applications", "interview_history", "progress", "sessions"):
            self.db[collection].create_index("id", unique=True)
        self.db.favorites.create_index([("user_id", ASCENDING), ("internship_id", ASCENDING)], unique=True)
        self.db.sessions.create_index("expires_at", expireAfterSeconds=0)
        self.db.applications.create_index([("user_id", ASCENDING), ("internship_id", ASCENDING)], unique=True)
        self.db.interview_history.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        self.db.progress.create_index([("user_id", ASCENDING), ("skill", ASCENDING)], unique=True)

    @staticmethod
    def _clean(document):
        if document is None:
            return None
        document.pop("_id", None)
        return document

    def find(self, collection, filters=None):
        return [self._clean(doc) for doc in self.db[collection].find(filters or {})]

    def get(self, collection, identifier):
        return self.one(collection, {"id": str(identifier)})

    def one(self, collection, filters):
        return self._clean(self.db[collection].find_one(filters))

    def insert(self, collection, document):
        try:
            self.db[collection].insert_one(deepcopy(document))
        except DuplicateKeyError as exc:
            raise ConflictError("Document already exists") from exc
        return deepcopy(document)

    def upsert(self, collection, identifier, document):
        value = {**deepcopy(document), "id": str(identifier)}
        try:
            self.db[collection].replace_one({"id": str(identifier)}, value, upsert=True)
        except DuplicateKeyError as exc:
            raise ConflictError("Document already exists") from exc
        return deepcopy(value)

    def delete(self, collection, identifier):
        return bool(self.db[collection].delete_one({"id": str(identifier)}).deleted_count)

    def ping(self):
        return bool(self.client.admin.command("ping")["ok"])

    def close(self):
        self.client.close()


def create_repository(settings):
    if settings.demo_mode:
        return MemoryRepository()
    return MongoRepository(settings.mongodb_uri, settings.mongodb_database)


def utcnow():
    return datetime.now(timezone.utc)
