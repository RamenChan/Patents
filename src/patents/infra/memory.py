from __future__ import annotations

from datetime import datetime
from typing import Dict, Generic, Optional, Sequence, TypeVar
from uuid import uuid4

from patents.adapters import ports


T = TypeVar("T")


class SystemClock(ports.Clock):
    def now(self) -> datetime:
        return datetime.utcnow()


class UuidGenerator(ports.IdGenerator):
    def new_id(self) -> str:
        return str(uuid4())


class InMemoryRepository(ports.Repository[T], Generic[T]):
    def __init__(self) -> None:
        self._items: Dict[str, T] = {}
        self._index: Dict[str, list[str]] = {}

    def get(self, entity_id: str) -> Optional[T]:
        return self._items.get(entity_id)

    def list_by_invention(self, invention_id: str) -> Sequence[T]:
        ids = self._index.get(invention_id, [])
        return [self._items[item_id] for item_id in ids]

    def save(self, entity: T) -> None:
        entity_id = getattr(entity, "id")
        self._items[entity_id] = entity
        invention_id = getattr(entity, "invention_id", None)
        if invention_id is None:
            return
        if invention_id not in self._index:
            self._index[invention_id] = []
        if entity_id not in self._index[invention_id]:
            self._index[invention_id].append(entity_id)
