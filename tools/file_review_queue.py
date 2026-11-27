#!/usr/bin/env python3
"""Read-only, commit-pinned review queue. No checkout, solver, or automatic review receipts."""
import argparse
import collections
import json
import subprocess
import sys

LEDGER = "docs/review/FILE_REVIEW_LEDGER.jsonl"
STATES = {"reviewed", "updated", "partial", "blocked", "reopen"}
LEVELS = {"content", "metadata", "validation"}

def git(*args):
    return subprocess.check_output(["git", *args])

def receipts(raw):
    latest = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if not all(isinstance(r.get(k), str) and r[k].strip() for k in
                   ("date", "ref", "path", "blob", "level", "state", "scope", "evidence")):
            raise ValueError("Incomplete ledger receipt")
        if r["state"] not in STATES or r["level"] not in LEVELS:
            raise ValueError("Unknown ledger state or level")
        if r["level"] == "content":
            latest[(r["path"], r["blob"])] = r
    return latest

def queue(raw, latest, prefix):
    any_path = {path for path, _ in latest}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        path = path.decode("utf-8", "surrogateescape")
        if path == LEDGER or not path.startswith(prefix):
            continue
        r = latest.get((path, blob))
        if r and r["state"] in ("reviewed", "updated"):
            state = "closed_for_recorded_scope"
        elif r:
            state = r["state"]
        else:
            state = "changed_or_new" if path in any_path else "pending"
        yield {"path": path, "blob": blob, "type": kind, "mode": mode,
               "state": state, "scope": r["scope"] if r else None}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ref", required=True)
    p.add_argument("--ledger-ref", help="Explicit ledger ref; defaults to --ref")
    p.add_argument("--prefix", default="")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--include-closed", action="store_true")
    args = p.parse_args()
    if args.limit < 0:
        p.error("--limit must be >= 0")
    commit = git("rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}").decode().strip()
    # Separate explicit ledger ref allows historical branches to reuse current receipts.
    ledger_commit = git("rev-parse", "--verify", "--end-of-options",
                        (args.ledger_ref or args.ref) + "^{commit}").decode().strip()
    latest = receipts(git("show", ledger_commit + ":" + LEDGER).decode("utf-8"))
    counts = collections.Counter()
    emitted = 0
    for row in queue(git("ls-tree", "-r", "-z", "--full-tree", commit), latest, args.prefix):
        counts[row["state"]] += 1
        if row["state"] == "closed_for_recorded_scope" and not args.include_closed:
            continue
        if not args.limit or emitted < args.limit:
            print(json.dumps(row, ensure_ascii=True))
            emitted += 1
    print(json.dumps({"commit": commit, "ledger_commit": ledger_commit, "prefix": args.prefix, "counts": dict(counts),
                      "total": sum(counts.values()), "emitted": emitted}), file=sys.stderr)

if __name__ == "__main__":
    main()
