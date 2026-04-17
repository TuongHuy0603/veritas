#!/usr/bin/env python3
"""
verify-claim.py — grounding helpers for the verify-claim module.

Three small checks, no dependencies, no network. The assistant calls these
to confirm a claim before stating it.

Usage:
    python verify-claim.py path <file_path>
    python verify-claim.py symbol <file_path> <symbol>
    python verify-claim.py version <manifest_path> <package>

The `version` check finds the package as either a dependency key or the
manifest's own `"name"` field — useful for "is this project version X?".

Exit codes:
    0  verified
    1  not verified (claim is false or undecidable from this check alone)
    2  bad arguments
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def check_path(p: str) -> int:
    exists = Path(p).exists()
    print(f"PATH {p}: {'FOUND' if exists else 'NOT FOUND'}")
    return 0 if exists else 1


def check_symbol(file_path: str, symbol: str) -> int:
    path = Path(file_path)
    if not path.exists():
        print(f"FILE {file_path}: NOT FOUND")
        return 1
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"FILE {file_path}: READ ERROR {e}")
        return 1
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    hits = [i + 1 for i, line in enumerate(text.splitlines()) if pattern.search(line)]
    if hits:
        print(f"SYMBOL {symbol} in {file_path}: FOUND on lines {hits[:10]}")
        return 0
    print(f"SYMBOL {symbol} in {file_path}: NOT FOUND")
    return 1


_MANIFEST_PATTERNS = {
    "package.json": r'"{pkg}"\s*:\s*"([^"]+)"',
    "pyproject.toml": r'{pkg}\s*=\s*"([^"]+)"',
    "Cargo.toml": r'{pkg}\s*=\s*"([^"]+)"',
    "go.mod": r"{pkg}\s+v?([\w\.\-]+)",
    "requirements.txt": r"^{pkg}[=~<>!]+([\w\.\-]+)",
    "Gemfile.lock": r"{pkg}\s+\(([\w\.\-]+)\)",
}


def check_version(manifest: str, pkg: str) -> int:
    path = Path(manifest)
    if not path.exists():
        print(f"MANIFEST {manifest}: NOT FOUND")
        return 1
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"MANIFEST {manifest}: READ ERROR {e}")
        return 1
    name = path.name
    # Special-case: manifest's OWN name (not a dependency). For package.json
    # and similar, the version lives next to the name — match both fields.
    if name == "package.json":
        own = re.search(
            rf'"name"\s*:\s*"{re.escape(pkg)}"[\s\S]*?"version"\s*:\s*"([^"]+)"',
            text,
        )
        if own:
            print(f"VERSION {pkg} (own) in {manifest}: {own.group(1)}")
            return 0
    template = _MANIFEST_PATTERNS.get(name)
    if template is None:
        print(f"MANIFEST {manifest}: UNSUPPORTED FORMAT ({name})")
        return 1
    pattern = re.compile(template.format(pkg=re.escape(pkg)), re.MULTILINE)
    match = pattern.search(text)
    if match:
        print(f"VERSION {pkg} in {manifest}: {match.group(1)}")
        return 0
    print(f"VERSION {pkg} in {manifest}: NOT FOUND")
    return 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    args = argv[2:]
    if cmd == "path" and len(args) == 1:
        return check_path(args[0])
    if cmd == "symbol" and len(args) == 2:
        return check_symbol(args[0], args[1])
    if cmd == "version" and len(args) == 2:
        return check_version(args[0], args[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
