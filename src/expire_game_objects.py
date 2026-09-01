"""Create a short-lived game marker and remove expired markers."""

from __future__ import annotations

import argparse
import time
from pathlib import PurePosixPath

from infrai_storage import InfraiError, StorageClient


def expiry_from_key(key: str) -> int | None:
    """Read the unix expiry from keys shaped as throwaway/<expiry>/<name>."""
    parts = PurePosixPath(key).parts
    if len(parts) != 3 or parts[0] != "throwaway":
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def expire_objects(client: StorageClient, now: int | None = None) -> list[str]:
    current = int(time.time()) if now is None else now
    removed: list[str] = []
    for item in client.list_objects():
        key = str(item.get("key", ""))
        expires_at = expiry_from_key(key)
        if expires_at is None or expires_at > current:
            continue
        state = client.head_object(key)
        if state.get("found"):
            client.delete_object(key)
            removed.append(key)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Expire throwaway game objects")
    parser.add_argument("--bucket", default="game-session-markers")
    parser.add_argument("--ttl", type=int, default=300)
    parser.add_argument("--name", default="round-001")
    args = parser.parse_args()

    client = StorageClient(args.bucket)
    client.ensure_bucket()
    expiry = int(time.time()) + args.ttl
    key = f"throwaway/{expiry}/{args.name}"
    client.put_marker(key, "temporary game state")
    removed = expire_objects(client)
    print(f"stored {key}; removed {len(removed)} expired object(s)")


if __name__ == "__main__":
    try:
        main()
    except InfraiError as error:
        raise SystemExit(str(error))
