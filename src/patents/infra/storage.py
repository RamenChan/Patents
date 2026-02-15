from __future__ import annotations

from pathlib import Path
from typing import Dict

from patents.adapters import ports


class InMemoryStorage(ports.Storage):
    def __init__(self) -> None:
        self._objects: Dict[str, bytes] = {}

    def put(self, key: str, data: bytes) -> str:
        self._objects[key] = data
        return key

    def get(self, key: str) -> bytes:
        return self._objects[key]


class FileStorage(ports.Storage):
    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir)

    def put(self, key: str, data: bytes) -> str:
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def get(self, key: str) -> bytes:
        path = self._root / key
        return path.read_bytes()
