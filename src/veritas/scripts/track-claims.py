#!/usr/bin/env python3
"""
track-claims.py — provenance DAG for the Veritas claim ledger.

Each claim is a JSON line in .veritas/claims.jsonl:

    {"id": "c_ab12", "text": "...", "status": "verified",
     "depends_on": ["c_98ef"], "evidence": [{"file": "x.py", "line": 47,
     "fingerprint": "a1b2c3d4"}], "commit_sha": "abcdef0",
     "touched_files": ["x.py"], "created_at": "...", "updated_at": "..."}

Cascade invalidation: when a file in `touched_files` changes on disk, the
claim is marked `stale`. Every claim that lists it in `depends_on` is also
marked `stale`, transitively. No network, no database. Just files.

Usage:
    track-claims.py add --text "..." [--depends-on ID,ID] [--file PATH] [--line N]
    track-claims.py verify ID                     mark as verified with current state
    track-claims.py invalidate-changed            scan touched_files for drift
    track-claims.py show [ID]                     print one claim or the whole DAG
    track-claims.py list [--status STATUS]        list by status
    track-claims.py retire ID --reason "..."      move to retired
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VERITAS_DIR = Path(".veritas")
CLAIMS_FILE = VERITAS_DIR / "claims.jsonl"
STATUSES = ("unverified", "verified", "partial", "stale", "retired")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short_id(seed: str) -> str:
    return "c_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def file_fingerprint(path: str) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha1()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_all() -> list[dict]:
    if not CLAIMS_FILE.exists():
        return []
    rows: list[dict] = []
    for line in CLAIMS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def save_all(rows: Iterable[dict]) -> None:
    VERITAS_DIR.mkdir(exist_ok=True)
    with CLAIMS_FILE.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def dependents_of(claim_id: str, rows: list[dict]) -> list[dict]:
    return [r for r in rows if claim_id in r.get("depends_on", [])]


def mark_stale_cascade(root_id: str, rows: list[dict], reason: str) -> int:
    touched = 0
    frontier = [root_id]
    seen: set[str] = set()
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        for claim in rows:
            if claim.get("id") != current:
                continue
            if claim.get("status") in ("stale", "retired"):
                continue
            claim["status"] = "stale"
            claim["stale_reason"] = reason
            claim["updated_at"] = now()
            touched += 1
        for dep in dependents_of(current, rows):
            frontier.append(dep["id"])
    return touched


def cmd_add(args: argparse.Namespace) -> int:
    rows = load_all()
    seed = f"{args.text}|{now()}"
    cid = short_id(seed)
    evidence = []
    touched_files: list[str] = []
    if args.file:
        entry = {"file": args.file}
        if args.line is not None:
            entry["line"] = args.line
        fp = file_fingerprint(args.file)
        if fp:
            entry["fingerprint"] = fp
            touched_files.append(args.file)
        evidence.append(entry)
    depends_on = [d.strip() for d in (args.depends_on or "").split(",") if d.strip()]
    row = {
        "id": cid,
        "text": args.text,
        "status": "unverified",
        "depends_on": depends_on,
        "evidence": evidence,
        "commit_sha": git_head(),
        "touched_files": touched_files,
        "created_at": now(),
        "updated_at": now(),
    }
    rows.append(row)
    save_all(rows)
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    rows = load_all()
    hit = False
    for row in rows:
        if row.get("id") == args.id:
            row["status"] = "verified"
            row["commit_sha"] = git_head() or row.get("commit_sha", "")
            row["updated_at"] = now()
            for ev in row.get("evidence", []):
                if "file" in ev:
                    fp = file_fingerprint(ev["file"])
                    if fp:
                        ev["fingerprint"] = fp
                        if ev["file"] not in row["touched_files"]:
                            row["touched_files"].append(ev["file"])
            hit = True
            break
    if not hit:
        print(f"claim {args.id} not found", file=sys.stderr)
        return 1
    save_all(rows)
    print(f"verified {args.id}")
    return 0


def cmd_invalidate_changed(_: argparse.Namespace) -> int:
    rows = load_all()
    stale_count = 0
    for row in rows:
        if row.get("status") not in ("verified", "partial"):
            continue
        for ev in row.get("evidence", []):
            path = ev.get("file")
            if not path:
                continue
            current = file_fingerprint(path)
            prior = ev.get("fingerprint")
            if prior and current and current != prior:
                stale_count += mark_stale_cascade(
                    row["id"], rows, reason=f"{path} changed"
                )
                break
    save_all(rows)
    print(f"marked {stale_count} claim(s) stale")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    rows = load_all()
    if args.id:
        for row in rows:
            if row.get("id") == args.id:
                print(json.dumps(row, ensure_ascii=False, indent=2))
                return 0
        print(f"claim {args.id} not found", file=sys.stderr)
        return 1
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = load_all()
    for row in rows:
        if args.status and row.get("status") != args.status:
            continue
        deps = ",".join(row.get("depends_on", [])) or "-"
        print(f"{row['id']:<12} {row['status']:<11} deps={deps:<20} {row['text'][:60]}")
    return 0


def cmd_retire(args: argparse.Namespace) -> int:
    rows = load_all()
    hit = False
    for row in rows:
        if row.get("id") == args.id:
            row["status"] = "retired"
            row["retire_reason"] = args.reason
            row["updated_at"] = now()
            hit = True
            break
    if not hit:
        print(f"claim {args.id} not found", file=sys.stderr)
        return 1
    save_all(rows)
    print(f"retired {args.id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="track-claims.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="add a new claim")
    add.add_argument("--text", required=True)
    add.add_argument("--depends-on", default="")
    add.add_argument("--file")
    add.add_argument("--line", type=int)
    add.set_defaults(func=cmd_add)

    verify = sub.add_parser("verify", help="mark a claim as verified")
    verify.add_argument("id")
    verify.set_defaults(func=cmd_verify)

    inv = sub.add_parser("invalidate-changed", help="scan for file drift")
    inv.set_defaults(func=cmd_invalidate_changed)

    show = sub.add_parser("show", help="show one claim or all")
    show.add_argument("id", nargs="?")
    show.set_defaults(func=cmd_show)

    listc = sub.add_parser("list", help="list claims")
    listc.add_argument("--status", choices=STATUSES)
    listc.set_defaults(func=cmd_list)

    retire = sub.add_parser("retire", help="retire a claim")
    retire.add_argument("id")
    retire.add_argument("--reason", required=True)
    retire.set_defaults(func=cmd_retire)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
