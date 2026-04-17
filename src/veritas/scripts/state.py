#!/usr/bin/env python3
"""
state.py — read/write helpers for the Veritas ledger directory (.veritas/).

Usage:
    python state.py init                           create .veritas/ with empty files
    python state.py set-persona <skeptic|sentinel|archivist|none>
    python state.py set-gate <proceed|pause-for-confirmation|abort>
    python state.py set-claim <verified|unverified|partial>
    python state.py audit <decision> <action-summary> [--rev REF] [--authz STATUS]
    python state.py show                           print current state.json

No dependencies. Writes plain JSON and plain text so the files stay readable
without this script.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VERITAS_DIR = Path(".veritas")
STATE_FILE = VERITAS_DIR / "state.json"
AUDIT_LOG = VERITAS_DIR / "audit.log"
LEDGER_FILE = VERITAS_DIR / "LEDGER.md"
HANDOFF_FILE = VERITAS_DIR / "HANDOFF.md"
LESSONS_FILE = VERITAS_DIR / "LESSONS.md"
DECISIONS_FILE = VERITAS_DIR / "DECISIONS.md"

VERSION = "0.2.0"
PERSONAS = {"skeptic", "sentinel", "archivist", "none"}
GATE_DECISIONS = {"proceed", "pause-for-confirmation", "abort"}
CLAIM_STATUSES = {"verified", "unverified", "partial"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_state() -> dict:
    return {
        "version": VERSION,
        "active_persona": None,
        "turn": 0,
        "last_gate_decision": None,
        "last_claim_status": None,
        "open_questions": [],
        "updated_at": now(),
    }


def load_state() -> dict:
    if not STATE_FILE.exists():
        return default_state()
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_state()


def save_state(state: dict) -> None:
    VERITAS_DIR.mkdir(exist_ok=True)
    state["updated_at"] = now()
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def cmd_init() -> int:
    VERITAS_DIR.mkdir(exist_ok=True)
    if not STATE_FILE.exists():
        save_state(default_state())
    for path, header in [
        (LEDGER_FILE, "# Assumption Ledger\n\n## Active\n\n## Stale\n\n## Retired\n"),
        (LESSONS_FILE, "# Lessons\n\n"),
        (DECISIONS_FILE, "# Decisions\n\n"),
    ]:
        if not path.exists():
            path.write_text(header, encoding="utf-8")
    if not AUDIT_LOG.exists():
        AUDIT_LOG.write_text("", encoding="utf-8")
    print(f"Initialized {VERITAS_DIR.resolve()}")
    return 0


def cmd_set_persona(value: str) -> int:
    if value not in PERSONAS:
        print(f"Invalid persona. Expected one of: {sorted(PERSONAS)}")
        return 2
    state = load_state()
    state["active_persona"] = None if value == "none" else value
    state["turn"] = state.get("turn", 0) + 1
    save_state(state)
    print(f"active_persona={state['active_persona']} turn={state['turn']}")
    return 0


def cmd_set_gate(value: str) -> int:
    if value not in GATE_DECISIONS:
        print(f"Invalid gate. Expected one of: {sorted(GATE_DECISIONS)}")
        return 2
    state = load_state()
    state["last_gate_decision"] = value
    save_state(state)
    print(f"last_gate_decision={value}")
    return 0


def cmd_set_claim(value: str) -> int:
    if value not in CLAIM_STATUSES:
        print(f"Invalid claim status. Expected one of: {sorted(CLAIM_STATUSES)}")
        return 2
    state = load_state()
    state["last_claim_status"] = value
    save_state(state)
    print(f"last_claim_status={value}")
    return 0


def cmd_audit(argv: list[str]) -> int:
    if len(argv) < 2:
        print("audit requires <decision> <action-summary> [--rev REF] [--authz STATUS]")
        return 2
    decision, summary = argv[0], argv[1]
    if decision not in GATE_DECISIONS:
        print(f"Invalid decision. Expected one of: {sorted(GATE_DECISIONS)}")
        return 2
    rev = "NONE"
    authz = "unspecified"
    i = 2
    while i < len(argv):
        if argv[i] == "--rev" and i + 1 < len(argv):
            rev = argv[i + 1]
            i += 2
        elif argv[i] == "--authz" and i + 1 < len(argv):
            authz = argv[i + 1]
            i += 2
        else:
            print(f"Unknown option: {argv[i]}")
            return 2
    VERITAS_DIR.mkdir(exist_ok=True)
    line = f"{now()}  blast-radius  {decision:<21}  {summary}  rev={rev}  authz={authz}\n"
    with AUDIT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print(line.rstrip())
    return 0


def cmd_show() -> int:
    state = load_state()
    print(json.dumps(state, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    rest = argv[2:]
    if cmd == "init":
        return cmd_init()
    if cmd == "show":
        return cmd_show()
    if cmd == "set-persona" and rest:
        return cmd_set_persona(rest[0])
    if cmd == "set-gate" and rest:
        return cmd_set_gate(rest[0])
    if cmd == "set-claim" and rest:
        return cmd_set_claim(rest[0])
    if cmd == "audit":
        return cmd_audit(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
