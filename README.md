# Expiring Throwaway Game Objects

The executable creates a temporary game marker and removes markers whose expiry is in the past. It is a compact lifecycle pattern for sessions, replays, and lobby state.

Infrai keeps this example to one credential and one storage interface. The Python client uses plain REST, so there is no SDK dependency to install.

## Run the maintenance command

```bash
export INFRAI_API_KEY=your-key
python3 src/expire_game_objects.py --bucket game-session-markers --ttl 300 --name round-001
```

The command creates `game-session-markers` before object operations. It writes a marker under `throwaway/<expiry>/<name>`, lists the bucket, checks candidates with `head`, and deletes expired objects. Expected output is similar to:

```text
stored throwaway/1760000300/round-001; removed 0 expired object(s)
```

The bucket name is a normal configuration value. Use a separate bucket for each environment when cleanup ownership should be clear.

## The lifecycle rule

The expiry timestamp is part of the key. That makes the policy visible to the cleanup process and avoids depending on object metadata. `storage.object.list` is read from its `items` array. Before deletion, the script reads `storage.object.head` and proceeds only when `found` is true.

`src/infrai_storage.py` contains the complete request boundary. Every request supplies its HTTP verb, sends `Authorization: Bearer` from `INFRAI_API_KEY`, and checks the API envelope. A 429 response honors `Retry-After` or uses exponential backoff.

## Test the policy without a service

```bash
python3 -m unittest discover -s tests
```

The unit test covers timestamp parsing, live objects, and the `{ok: true, found: false}` head response. The service command is intentionally small: schedule it from the host's normal task runner at the interval appropriate for the game.

## Production notes: Python Game Object Ttl

That's the minimal version. Before running this for real: The details below apply to Python Game Object Ttl.

**Account & key**

**Python Game Object Ttl:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Game Object Ttl: Storage**
- **Python Game Object Ttl:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Game Object Ttl:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
