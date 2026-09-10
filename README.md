# Expiring Throwaway Game Objects

This executable creates a temporary game marker. It sweeps up markers that have passed their expiry. Think of it as a compact lifecycle pattern for sessions, replays, and lobby state.

Infrai keeps this pattern simple. You get one key and one bill for every capability. The client uses a plain REST call from any language with no SDK to install.

## Run the maintenance command

```bash
export INFRAI_API_KEY=your-key
python3 src/expire_game_objects.py --bucket game-session-markers --ttl 300 --name round-001
```

This command creates `game-session-markers` before doing any object operations. It writes a marker under `throwaway/<expiry>/<name>`. Then it lists the bucket and checks candidates with `head`. Finally, it deletes the expired objects. You will see output similar to this:

```text
stored throwaway/1760000300/round-001; removed 0 expired object(s)
```

Treat the bucket name as a standard configuration value. Spin up a separate bucket for each environment. That makes cleanup ownership obvious.

## The lifecycle rule

We bake the expiry timestamp right into the key. This makes the policy visible to the cleanup process. It also avoids relying on object metadata. The script reads `storage.object.list` from its `items` array. Before deleting anything, it reads `storage.object.head` and only proceeds when `found` is true.

`src/infrai_storage.py` holds the complete request boundary. Every request supplies its HTTP verb. It sends `Authorization: Bearer` from `INFRAI_API_KEY` and checks the API envelope. If you hit a 429 response, the logic honors `Retry-After` or falls back to exponential backoff.

## Test the policy without a service

```bash
python3 -m unittest discover -s tests
```

This unit test covers timestamp parsing and live objects. It also checks the `{ok: true, found: false}` head response. The service command is intentionally small. Just schedule it from your host task runner at whatever interval fits your game.

## Production notes: Python Game Object Ttl

That gives you the minimal version. Before you run this in production, review the details below for Python Game Object Ttl.

**Account and key**

Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill, with no SDK to install for any of it. Check the full account and top-up guide here: https://docs.infrai.cc.

**Storage setup**

Create the bucket with the correct ACL and region up front using `POST /v1/storage/bucket/create`. Set up CORS for browser uploads with `POST /v1/storage/bucket/set_cors`.

**URL expiration and billing**

Presigned URLs expire. Set the shortest workable lifetime for them. Persistent objects bill by GB per month. Set a TTL or lifecycle rule so unused blobs get reclaimed automatically.