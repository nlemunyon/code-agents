#!/usr/bin/env python3
"""Reject user-specific home-directory paths in portable documentation."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


DOCUMENT_SUFFIXES = {".adoc", ".markdown", ".md", ".mdx", ".rst", ".txt"}
DOCUMENT_NAMES = {
    "AGENTS",
    "CHANGELOG",
    "CONTRIBUTING",
    "DEVELOPING",
    "README",
    "RUNBOOK",
}
SKIP_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "dist",
    "node_modules",
    "vendor",
}
PATH_PATTERNS = (
    (
        "macOS user home",
        re.compile(r"(?<![A-Za-z0-9.])/(?:Users)/[^/\\\s`'\"<>]+(?:[/\\]|$)"),
    ),
    (
        "Linux user home",
        re.compile(r"(?<![A-Za-z0-9.])/(?:home)/[^/\\\s`'\"<>]+(?:[/\\]|$)"),
    ),
    (
        "Windows user home",
        re.compile(r"(?i)(?<![A-Za-z0-9])[A-Z]:[/\\]+Users[/\\]+[^/\\\s`'\"<>]+"),
    ),
    (
        "tilde home shorthand",
        re.compile(r"(?<![A-Za-z0-9_$])~[/\\]"),
    ),
)


def is_document(path: Path) -> bool:
    return path.suffix.lower() in DOCUMENT_SUFFIXES or path.name.upper() in DOCUMENT_NAMES


def walk_files(root: Path) -> list[Path]:
    """List files below root in sorted order and skip tool folders."""
    found: list[Path] = []
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if name not in SKIP_DIRECTORIES]
        found.extend(Path(directory) / name for name in filenames)
    return sorted(found)


def iter_documents(inputs: list[Path]):
    seen: set[Path] = set()
    for candidate in inputs:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield candidate
            continue
        if not candidate.is_dir():
            raise FileNotFoundError(candidate)
        for path in walk_files(candidate):
            if any(part in SKIP_DIRECTORIES for part in path.parts):
                continue
            if path.is_file() and is_document(path):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path


def validate_document(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{path}: cannot read UTF-8 documentation: {exc}"]

    for line_number, line in enumerate(lines, 1):
        for label, pattern in PATH_PATTERNS:
            match = pattern.search(line)
            if match:
                errors.append(
                    f"{path}:{line_number}: {label} path {match.group(0)!r} is not portable; "
                    "use $HOME, a project-relative path, <repo-root>, %USERPROFILE%, "
                    "or $env:USERPROFILE"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="Documentation files or directories to scan (default: current directory)",
    )
    args = parser.parse_args()

    try:
        documents = list(iter_documents(args.paths))
    except FileNotFoundError as exc:
        print(f"ERROR: path does not exist: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for document in documents:
        errors.extend(validate_document(document))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(documents)} documentation file(s) for portable paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
