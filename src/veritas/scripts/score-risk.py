#!/usr/bin/env python3
"""
risk_score.py — compute a [0.0, 1.0] risk score for a proposed action.

Inputs:
    action string           what Sentinel is about to gate
    --branch BRANCH         current git branch (default: current HEAD)
    --rev REF               proposed reversibility reference (hash / NONE / …)
    --authz STATUS          yes | no | ambiguous | unspecified
    --history PATH          override default .veritas/history.jsonl

Scoring is deterministic and auditable. No ML, no opaque model.

Components (weights sum to 1.0):
    base_score       0.40   from data/risky-ops.csv pattern match
    reversibility    0.25   NONE -> +1.0, commit-ref -> 0.0
    branch           0.15   shared branch names -> +1.0
    authorization    0.10   ambiguous/no -> +1.0, yes -> 0.0
    recency          0.10   similar action approved <1h ago -> -0.5 (familiarity)

Output: JSON with score + components + recommendation.
    recommendation: proceed | pause-for-confirmation | abort
        score < 0.30          -> proceed
        0.30 <= score < 0.70  -> pause-for-confirmation
        score >= 0.70         -> abort
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

VERITAS_DIR = Path(".veritas")
HISTORY = VERITAS_DIR / "history.jsonl"
DEFAULT_RULES = Path(__file__).resolve().parent.parent / "data" / "risky-ops.csv"

SHARED_BRANCH_PATTERNS = [
    r"^main$",
    r"^master$",
    r"^release/.+$",
    r"^prod(uction)?$",
    r"^staging$",
]

WEIGHTS = {
    "base_score": 0.40,
    "reversibility": 0.25,
    "branch": 0.15,
    "authorization": 0.10,
    "recency": 0.10,
}


def git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def load_rules(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rules = []
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rules.append(row)
    return rules


def base_score(action: str, rules: list[dict]) -> tuple[float, str]:
    for row in rules:
        pattern = row.get("pattern", "").strip()
        if not pattern:
            continue
        # word-boundary where possible, fall back to substring for punctuation-heavy patterns
        escaped = re.escape(pattern)
        if re.search(rf"(?<!\w){escaped}(?!\w)", action, flags=re.IGNORECASE):
            raw = row.get("base_score", "")
            try:
                return float(raw), pattern
            except (TypeError, ValueError):
                # fall back by default decision
                decision = row.get("default_decision", "")
                fallback = {
                    "proceed": 0.1,
                    "pause-for-confirmation": 0.6,
                    "abort": 0.9,
                }.get(decision, 0.5)
                return fallback, pattern
    return 0.2, ""


def reversibility_score(rev: str) -> float:
    if not rev:
        return 0.5
    rev = rev.strip()
    if rev.upper() == "NONE":
        return 1.0
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", rev):
        return 0.0
    if rev.lower().startswith(("backup:", "snapshot:", "tag:")):
        return 0.1
    return 0.4


def branch_score(branch: str) -> float:
    for pat in SHARED_BRANCH_PATTERNS:
        if re.match(pat, branch or ""):
            return 1.0
    return 0.0


def authz_score(authz: str) -> float:
    authz = (authz or "unspecified").lower()
    if authz == "yes":
        return 0.0
    if authz == "ambiguous":
        return 0.7
    if authz == "no":
        return 1.0
    return 0.5  # unspecified


def recency_score(action: str, history_path: Path) -> float:
    if not history_path.exists():
        return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    try:
        lines = history_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0.0
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("decision") != "proceed":
            continue
        if _tokens_overlap(entry.get("action", ""), action) < 0.5:
            continue
        try:
            ts = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            return -0.5
    return 0.0


def _tokens_overlap(a: str, b: str) -> float:
    ta = set(re.findall(r"\w+", a.lower()))
    tb = set(re.findall(r"\w+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def recommend(score: float) -> str:
    if score >= 0.70:
        return "abort"
    if score >= 0.30:
        return "pause-for-confirmation"
    return "proceed"


def score_action(
    action: str,
    branch: str,
    rev: str,
    authz: str,
    rules_path: Path,
    history_path: Path,
) -> dict:
    rules = load_rules(rules_path)
    base, matched = base_score(action, rules)
    components = {
        "base_score": base,
        "reversibility": reversibility_score(rev),
        "branch": branch_score(branch),
        "authorization": authz_score(authz),
        "recency": recency_score(action, history_path),
    }
    total = 0.0
    for key, val in components.items():
        total += WEIGHTS[key] * val
    total = max(0.0, min(1.0, total))
    return {
        "action": action,
        "branch": branch,
        "reversibility": rev,
        "authorization": authz,
        "matched_pattern": matched,
        "components": {k: round(v, 3) for k, v in components.items()},
        "weights": WEIGHTS,
        "score": round(total, 3),
        "recommendation": recommend(total),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="risk_score.py", description=__doc__)
    parser.add_argument("action")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--rev", default="NONE")
    parser.add_argument("--authz", default="unspecified")
    parser.add_argument("--rules", default=str(DEFAULT_RULES))
    parser.add_argument("--history", default=str(HISTORY))
    args = parser.parse_args(argv[1:])

    branch = args.branch if args.branch is not None else git_branch()
    result = score_action(
        action=args.action,
        branch=branch,
        rev=args.rev,
        authz=args.authz,
        rules_path=Path(args.rules),
        history_path=Path(args.history),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
