import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from expire_game_objects import expire_objects, expiry_from_key


class FakeClient:
    def __init__(self):
        self.deleted = []
        self.items = [
            {"key": "throwaway/100/old-round"},
            {"key": "throwaway/200/live-round"},
            {"key": "permanent/scoreboard"},
        ]

    def list_objects(self):
        return self.items

    def head_object(self, key):
        return {"ok": True, "found": key != "throwaway/100/old-round"}

    def delete_object(self, key):
        self.deleted.append(key)


class ExpiryTests(unittest.TestCase):
    def test_key_parser_and_missing_object_branch(self):
        self.assertEqual(expiry_from_key("throwaway/100/old-round"), 100)
        self.assertIsNone(expiry_from_key("permanent/scoreboard"))
        client = FakeClient()
        self.assertEqual(expire_objects(client, now=150), [])
        self.assertEqual(client.deleted, [])

    def test_expired_object_is_deleted(self):
        client = FakeClient()
        client.items[0]["key"] = "throwaway/100/ready"
        self.assertEqual(expire_objects(client, now=150), ["throwaway/100/ready"])


if __name__ == "__main__":
    unittest.main()
