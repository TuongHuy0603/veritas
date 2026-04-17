#!/usr/bin/env python3
"""
track-state.py — read/write helpers for the Veritas state directory (.veritas/).

Handles the state.json handshake and scaffolds LESSONS.md, DECISIONS.md, and
HANDOFF.md placeholders. Claim and action logs are managed by track-claims.py
and log-actions.py respectively.

Usage:
    track-state.py init                            scaffold .veritas/
    track-state.py set-role <verifier|risk-guard|session-recorder|none>
    track-state.py set-pillar <plan|design|execute|verify|guardrail|none>
    track-state.py set-phase <phase-name> [--step N]
    track-state.py set-gate <proceed|pause-for-confirmation|abort>
    track-state.py set-claim <verified|unverified|partial>
    track-state.py checksum                        sha256 of state.json (for HANDOFF)
    track-state.py show                            print current state.json
    track-state.py migrate                         upgrade a pre-1.0 state.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VERITAS_DIR = Path(".veritas")
STATE_FILE = VERITAS_DIR / "state.json"
HANDOFF_FILE = VERITAS_DIR / "HANDOFF.md"
LESSONS_FILE = VERITAS_DIR / "LESSONS.md"
DECISIONS_FILE = VERITAS_DIR / "DECISIONS.md"
CLAIMS_FILE = VERITAS_DIR / "claims.jsonl"
ACTIONS_FILE = VERITAS_DIR / "actions.jsonl"
HISTORY_FILE = VERITAS_DIR / "history.jsonl"
PRIVATE_DIR = VERITAS_DIR / "private"

VERSION = "1.0.0"
LEGACY_VERSIONS = {"0.1.0", "0.2.0", "0.3.0"}
ROLES = {"verifier", "risk-guard", "session-recorder", "none"}
PILLARS = {"plan", "design", "execute", "verify", "guardrail", "none"}
GATE_DECISIONS = {"proceed", "pause-for-confirmation", "abort"}
CLAIM_STATUSES = {"verified", "unverified", "partial"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_state() -> dict:
    return {
        "version": VERSION,
        "active_role": None,
        "turn": 0,
        "role_turns": {"verifier": 0, "risk-guard": 0, "session-recorder": 0},
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
    PRIVATE_DIR.mkdir(exist_ok=True)
    if not STATE_FILE.exists():
        save_state(default_state())
    for path, header in [
        (LESSONS_FILE, "# Lessons\n\n"),
        (DECISIONS_FILE, "# Decisions\n\n"),
        (HANDOFF_FILE, "# Session Scroll\n\nNo active scroll.\n"),
    ]:
        if not path.exists():
            path.write_text(header, encoding="utf-8")
    for path in (CLAIMS_FILE, ACTIONS_FILE, HISTORY_FILE):
        if not path.exists():
            path.write_text("", encoding="utf-8")
    gitignore = PRIVATE_DIR / ".gitkeep"
    if not gitignore.exists():
        gitignore.write_text("", encoding="utf-8")
    print(f"Initialized {VERITAS_DIR.resolve()}")
    return 0


def cmd_set_role(value: str) -> int:
    if value not in ROLES:
        print(f"Invalid role. Expected one of: {sorted(ROLES)}")
        return 2
    state = load_state()
    state["active_role"] = None if value == "none" else value
    state["turn"] = state.get("turn", 0) + 1
    if value != "none":
        state.setdefault("role_turns", {"verifier": 0, "risk-guard": 0, "session-recorder": 0})
        state["role_turns"][value] = state["role_turns"].get(value, 0) + 1
    save_state(state)
    print(f"active_role={state['active_role']} turn={state['turn']}")
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


def cmd_set_pillar(value: str) -> int:
    if value not in PILLARS:
        print(f"Invalid pillar. Expected one of: {sorted(PILLARS)}")
        return 2
    state = load_state()
    state["active_pillar"] = None if value == "none" else value
    save_state(state)
    print(f"active_pillar={state['active_pillar']}")
    return 0


def cmd_set_phase(value: str, step: int | None) -> int:
    state = load_state()
    state["phase"] = value
    if step is not None:
        state["step"] = step
    save_state(state)
    print(f"phase={value} step={state.get('step')}")
    return 0


def cmd_checksum() -> int:
    if not STATE_FILE.exists():
        print("no state.json", file=sys.stderr)
        return 1
    digest = hashlib.sha256(STATE_FILE.read_bytes()).hexdigest()
    print(digest)
    return 0


def cmd_show() -> int:
    state = load_state()
    print(json.dumps(state, indent=2))
    return 0


def cmd_migrate() -> int:
    if not STATE_FILE.exists():
        print("no state.json to migrate")
        return 0
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read state.json: {e}", file=sys.stderr)
        return 1
    changed = False
    if state.get("version") in LEGACY_VERSIONS:
        legacy_persona = state.pop("active_persona", None)
        legacy_map = {
            "skeptic": "verifier",
            "sentinel": "risk-guard",
            "archivist": "session-recorder",
        }
        if legacy_persona and "active_role" not in state:
            state["active_role"] = legacy_map.get(legacy_persona)
        state.setdefault("active_role", None)
        state.setdefault(
            "role_turns", {"verifier": 0, "risk-guard": 0, "session-recorder": 0}
        )
        state["version"] = VERSION
        changed = True
    if not changed:
        print(f"state.json already at {state.get('version', 'unknown')} — no migration needed")
        return 0
    save_state(state)
    print(f"migrated to {VERSION}")
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
    if cmd == "migrate":
        return cmd_migrate()
    if cmd == "checksum":
        return cmd_checksum()
    if cmd == "set-role" and rest:
        return cmd_set_role(rest[0])
    if cmd == "set-pillar" and rest:
        return cmd_set_pillar(rest[0])
    if cmd == "set-phase" and rest:
        step = None
        if len(rest) >= 3 and rest[1] == "--step":
            try:
                step = int(rest[2])
            except ValueError:
                print("--step expects an integer", file=sys.stderr)
                return 2
        return cmd_set_phase(rest[0], step)
    if cmd == "set-gate" and rest:
        return cmd_set_gate(rest[0])
    if cmd == "set-claim" and rest:
        return cmd_set_claim(rest[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
