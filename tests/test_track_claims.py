"""
Tests for src/veritas/scripts/track-claims.py.

Runs the script as a subprocess in a tmp directory so it exercises the real
CLI surface and the real .veritas/ layout.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "src" / "veritas" / "scripts" / "track-claims.py"


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


def test_add_creates_claim(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("hello\n", encoding="utf-8")
    run(["add", "--text", "sample exists", "--file", str(target)], cwd=tmp_path)
    claims = (tmp_path / ".veritas" / "claims.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(claims) == 1
    row = json.loads(claims[0])
    assert row["text"] == "sample exists"
    assert row["status"] == "unverified"
    assert row["evidence"][0]["file"] == str(target)
    assert row["evidence"][0]["fingerprint"]


def test_verify_then_invalidate_cascade(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("one\n", encoding="utf-8")
    run(["add", "--text", "base claim", "--file", str(target)], cwd=tmp_path)
    claims_path = tmp_path / ".veritas" / "claims.jsonl"
    base_id = json.loads(claims_path.read_text(encoding="utf-8").splitlines()[0])["id"]
    run(
        ["add", "--text", "dependent", "--file", str(target), "--depends-on", base_id],
        cwd=tmp_path,
    )
    run(["verify", base_id], cwd=tmp_path)
    target.write_text("two\n", encoding="utf-8")  # drift
    run(["invalidate-changed"], cwd=tmp_path)
    rows = [
        json.loads(line)
        for line in claims_path.read_text(encoding="utf-8").splitlines()
    ]
    stale = [r for r in rows if r["status"] == "stale"]
    assert len(stale) >= 1, rows
    stale_ids = {r["id"] for r in stale}
    assert base_id in stale_ids
