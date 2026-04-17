"""
Tests for src/veritas/scripts/log-actions.py — hash-chained action log.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "src" / "veritas" / "scripts" / "log-actions.py"


def run(args, cwd, check=True):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def test_append_and_verify_chain(tmp_path: Path) -> None:
    run(["append", "proceed", "git commit", "--rev", "abc1234", "--authz", "yes"], cwd=tmp_path)
    run(
        ["append", "pause-for-confirmation", "DROP TABLE sessions", "--rev", "NONE", "--authz", "ambiguous"],
        cwd=tmp_path,
    )
    result = run(["verify"], cwd=tmp_path)
    assert "chain intact" in result.stdout
    result = run(["length"], cwd=tmp_path)
    assert result.stdout.strip() == "2"


def test_verify_detects_tamper(tmp_path: Path) -> None:
    run(["append", "proceed", "git commit", "--rev", "abc1234", "--authz", "yes"], cwd=tmp_path)
    run(["append", "abort", "terraform destroy", "--rev", "NONE", "--authz", "no"], cwd=tmp_path)
    log_path = tmp_path / ".veritas" / "actions.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["action"] = "innocuous"
    lines[0] = json.dumps(tampered, ensure_ascii=False)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = run(["verify"], cwd=tmp_path, check=False)
    assert result.returncode != 0
    assert "hash mismatch" in result.stderr or "prev_hash" in result.stderr
