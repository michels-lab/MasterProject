import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("review_queue", Path(__file__).resolve().parents[1] / "file_review_queue.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def record(path="a", blob="abc", state="reviewed", level="content"):
    return dict(date="2026-11-27", ref="commit", path=path, blob=blob,
                state=state, level=level, scope="test", evidence="fixture")

def rows(entries, events):
    raw = b"".join(f"100644 blob {blob}\t{path}\0".encode() for path, blob in entries)
    latest = mod.receipts("\n".join(json.dumps(r) for r in events))
    return {r["path"]: r["state"] for r in mod.queue(raw, latest, "")}

class ReviewQueueTests(unittest.TestCase):
    def test_unchanged_closed_changed_reopened(self):
        self.assertEqual(rows([("a", "abc")], [record()])["a"], "closed_for_recorded_scope")
        self.assertEqual(rows([("a", "def")], [record()])["a"], "changed_or_new")
        self.assertEqual(rows([("a", "abc")], [record(), record(state="reopen")])["a"], "reopen")
    def test_metadata_never_closes_content(self):
        self.assertEqual(rows([("a", "abc")], [record(level="metadata")])["a"], "pending")
    def test_partial_and_ledger_exclusion(self):
        self.assertEqual(rows([("a", "abc"), (mod.LEDGER, "def")], [record(state="partial")]), {"a": "partial"})
    def test_invalid_receipt_fails_closed(self):
        with self.assertRaises(ValueError):
            mod.receipts('{"state":"reviewed"}')

if __name__ == "__main__":
    unittest.main()
