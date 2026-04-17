"""
Tests for src/veritas/scripts/score-risk.py — deterministic risk scoring.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "src" / "veritas" / "scripts" / "score-risk.py"


def run(args, cwd):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(result.stdout)


def test_safe_git_commit_proceeds(tmp_path: Path) -> None:
    out = run(
        ["git commit", "--branch", "feature/x", "--rev", "abc1234", "--authz", "yes"],
        cwd=tmp_path,
    )
    assert out["recommendation"] == "proceed"
    assert out["score"] < 0.30


def test_terraform_destroy_aborts(tmp_path: Path) -> None:
    out = run(
        ["terraform destroy", "--branch", "main", "--rev", "NONE", "--authz", "no"],
        cwd=tmp_path,
    )
    assert out["recommendation"] == "abort"
    assert out["score"] >= 0.70


def test_ambiguous_drop_table_pauses(tmp_path: Path) -> None:
    out = run(
        ["DROP TABLE sessions", "--branch", "feature/x", "--rev", "NONE", "--authz", "ambiguous"],
        cwd=tmp_path,
    )
    assert out["recommendation"] == "pause-for-confirmation"
