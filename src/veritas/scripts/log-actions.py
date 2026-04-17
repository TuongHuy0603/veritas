#!/usr/bin/env python3
"""
log-actions.py — hash-chained action log for RiskGuard gate decisions.

Each line of .veritas/actions.jsonl is a JSON object with:

    {
      "seq": 42,
      "timestamp": "2026-04-17T10:22:11Z",
      "module": "assess-risk",
      "decision": "pause-for-confirmation",
      "action": "DROP TABLE sessions",
      "reversibility": "NONE",
      "authorization": "ambiguous",
      "prev_hash": "<sha256 of line seq-1>",
      "hash": "<sha256 of this line without the hash field>"
    }

Tamper evidence: `hash` = sha256 of the JSON object with `hash` removed.
`prev_hash` chains to the previous entry. Any edit or truncation of a prior
line breaks the chain and `verify` returns non-zero.

Usage:
    log-actions.py append <decision> <action> [--rev REF] [--authz STATUS]
    log-actions.py verify                    walk chain, report first break
    log-actions.py tail [N]                  print last N entries (default 10)
    log-actions.py length                    print entry count
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VERITAS_DIR = Path(".veritas")
ACTIONS_FILE = VERITAS_DIR / "actions.jsonl"
HISTORY_FILE = VERITAS_DIR / "history.jsonl"
GENESIS_PREV = "0" * 64
DECISIONS = {"proceed", "pause-for-confirmation", "abort"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_hash(row: dict) -> str:
    copy = {k: v for k, v in row.items() if k != "hash"}
    payload = json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_rows() -> list[dict]:
    if not ACTIONS_FILE.exists():
        return []
    out: list[dict] = []
    for line in ACTIONS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            out.append({"__corrupt__": line})
    return out


def cmd_append(args: argparse.Namespace) -> int:
    if args.decision not in DECISIONS:
        print(f"decision must be one of: {sorted(DECISIONS)}", file=sys.stderr)
        return 2
    VERITAS_DIR.mkdir(exist_ok=True)
    rows = read_rows()
    seq = (rows[-1].get("seq", 0) if rows else 0) + 1
    prev_hash = rows[-1].get("hash", GENESIS_PREV) if rows else GENESIS_PREV
    row = {
        "seq": seq,
        "timestamp": now(),
        "module": "assess-risk",
        "decision": args.decision,
        "action": args.action,
        "reversibility": args.rev or "NONE",
        "authorization": args.authz or "unspecified",
        "prev_hash": prev_hash,
    }
    row["hash"] = compute_hash(row)
    with ACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    if args.decision == "proceed":
        history_row = {
            "timestamp": row["timestamp"],
            "action": row["action"],
            "decision": row["decision"],
            "authorization": row["authorization"],
        }
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(history_row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_verify(_: argparse.Namespace) -> int:
    rows = read_rows()
    if not rows:
        print("empty chain (no entries)")
        return 0
    prev_hash = GENESIS_PREV
    expected_seq = 1
    for idx, row in enumerate(rows, start=1):
        if "__corrupt__" in row:
            print(f"line {idx}: corrupt JSON", file=sys.stderr)
            return 1
        if row.get("seq") != expected_seq:
            print(
                f"line {idx}: seq mismatch (got {row.get('seq')}, expected {expected_seq})",
                file=sys.stderr,
            )
            return 1
        if row.get("prev_hash") != prev_hash:
            print(f"line {idx}: prev_hash does not chain", file=sys.stderr)
            return 1
        recomputed = compute_hash(row)
        if recomputed != row.get("hash"):
            print(f"line {idx}: hash mismatch (entry has been modified)", file=sys.stderr)
            return 1
        prev_hash = row["hash"]
        expected_seq += 1
    print(f"OK: {len(rows)} entries, chain intact")
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    rows = read_rows()
    n = args.n or 10
    for row in rows[-n:]:
        print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_length(_: argparse.Namespace) -> int:
    rows = read_rows()
    print(len(rows))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="log-actions.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ap = sub.add_parser("append", help="append a gate decision")
    ap.add_argument("decision", choices=sorted(DECISIONS))
    ap.add_argument("action")
    ap.add_argument("--rev")
    ap.add_argument("--authz")
    ap.set_defaults(func=cmd_append)

    vp = sub.add_parser("verify", help="walk chain and report first break")
    vp.set_defaults(func=cmd_verify)

    tp = sub.add_parser("tail", help="print last N entries")
    tp.add_argument("n", nargs="?", type=int, default=10)
    tp.set_defaults(func=cmd_tail)

    lp = sub.add_parser("length", help="print entry count")
    lp.set_defaults(func=cmd_length)

    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
