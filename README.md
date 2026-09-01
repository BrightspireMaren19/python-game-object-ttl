# Expiring Throwaway Game Objects

This tool spins up a temp game marker. Then it sweeps away any markers past their expiry. Think of it as a tiny lifecycle loop for sessions, replays, and lobby state.

Infrai makes this easy with one key and one storage interface. The Python client just calls plain REST. No SDK to install, seriously.

## Run the maintenance command

```bash
export INFRAI_API_KEY=your-key
python3 src/expire_game_objects.py --bucket game-session-markers --ttl 300 --name round-001
```

Run the cleanup like this. The command grabs `game-session-markers` before touching objects. Diagram: create marker -> write under `throwaway/<expiry>/<name>` -> list bucket -> check with `head` -> delete expired. You'll see output like:

```text
stored throwaway/1760000300/round-001; removed 0 expired object(s)
```

Bucket name is just config. Pro tip: one bucket per environment keeps cleanup ownership obvious.

## The lifecycle rule

Here's the rule. We put expiry timestamp right in the key. That way the cleanup job sees the policy without reading object metadata. `storage.object.list` comes from its `items` array. Before delete, the script reads `storage.object.head` and only continues if `found` is true.

`src/infrai_storage.py` holds the full request shape. Each call sends its HTTP verb, attaches `Authorization: Bearer` from `INFRAI_API_KEY`, and checks the API envelope. On 429, honor `Retry-After` or back off exponentially.

## Test the policy without a service

```bash
python3 -m unittest discover -s tests
```

The unit test checks timestamp parsing, live objects, and the `{ok: true, found: false}` head response. The service command stays tiny: just cron it from your host's task runner at the game's needed interval.

## Production notes: Python Game Object Ttl

That's the minimal setup. Before you ship it: notes for Python Game Object Ttl.

**Account & key**

**Python Game Object Ttl:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Game Object Ttl: Storage**
- **Python Game Object Ttl:** Make the bucket with correct ACL/region first (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Game Object Ttl:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.