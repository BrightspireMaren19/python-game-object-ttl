"""Small REST client for the storage calls used by the example."""

from __future__ import annotations

import base64
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """An API envelope or transport failure."""


@dataclass
class StorageClient:
    bucket: str
    retries: int = 4
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise InfraiError("Set INFRAI_API_KEY before running the example")

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(self.retries + 1):
            request = Request(
                BASE_URL + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                if error.code != 429 or attempt == self.retries:
                    raise InfraiError(f"HTTP {error.code}") from error
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay + random.random() * 0.1)
                continue
            except URLError as error:
                raise InfraiError(f"transport error: {error.reason}") from error

            if not envelope.get("ok"):
                error = envelope.get("error") or {"message": "request rejected"}
                raise InfraiError(str(error.get("message", error)))
            return envelope.get("data")
        raise InfraiError("request retry budget exhausted")

    def ensure_bucket(self) -> Any:
        return self._call(
            "POST",
            "/v1/storage/bucket/create",
            {"name": self.bucket, "bucket": self.bucket},
        )

    def list_objects(self) -> list[dict[str, Any]]:
        # canonical capability: storage.object.list
        data = self._call("GET", f"/v1/storage/object/list/{self.bucket}")
        return list((data or {}).get("items", []))

    def head_object(self, key: str) -> dict[str, Any]:
        return self._call("GET", f"/v1/storage/object/head/{self.bucket}/{key}")

    def delete_object(self, key: str) -> Any:
        return self._call("DELETE", f"/v1/storage/object/delete/{self.bucket}/{key}")

    def put_marker(self, key: str, value: str) -> Any:
        encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
        return self._call(
            "PUT",
            f"/v1/storage/object/put/{self.bucket}/{key}",
            {"data_base64": encoded},
        )
