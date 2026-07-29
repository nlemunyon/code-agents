#!/usr/bin/env python3
"""Validate reusable Codex custom-agent and project TOML templates."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path


try:
    import tomllib
except ModuleNotFoundError:
    for candidate in ("python3.13", "python3.12", "python3.11"):
        executable = shutil.which(candidate)
        if executable and Path(executable).resolve() != Path(sys.executable).resolve():
            os.execv(executable, [executable, __file__, *sys.argv[1:]])
    print("Python 3.11 or newer is required to validate TOML templates.", file=sys.stderr)
    raise SystemExit(2)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = PLUGIN_ROOT / "templates" / "custom-agents"
PROJECT_CONFIG = PLUGIN_ROOT / "templates" / "project" / ".codex" / "config.toml"
REQUIRED_STRING_FIELDS = ("name", "description", "developer_instructions")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
NICKNAME_PATTERN = re.compile(r"^[A-Za-z0-9 _-]+$")
ALLOWED_SANDBOX_MODES = {"read-only", "workspace-write", "danger-full-access"}
POLICY_CONCEPTS = {
    "documentation evidence": (
        (r"\bprimary(?: [a-z]+){0,3} documentation\b", r"\bprimary sources?\b"),
        (r"\btarget[- ]matched\b", r"\b(actual|exact) target\b"),
        (r"\btraining knowledge\b",),
        (r"\b(stale|unresolved|conflicting|mismatched)\b",),
    ),
    "portable documentation": (
        (r"\b(project|repository)[- ]relative paths?\b",),
        (r"\$HOME|<repo-root>|%USERPROFILE%|\$env:USERPROFILE",),
        (r"\buser-specific absolute home path\b",),
    ),
    "grade 12 readability": (
        (r"\b(user|developer) docs?\b",),
        (r"\bgrade 12\b",),
        (r"\bcomments?\b",),
        (r"\bdocstrings?\b",),
    ),
    "public-surface developer documentation": (
        (r"\bpublic surface\b",),
        (r"\bdeveloper documentation\b",),
        (r"\b(verified|tested) (usage )?example\b",),
        (r"\b(return|output|result)\b",),
        (r"\berrors?\b",),
        (r"\b(recovery|fix)\b",),
        (r"\b(if|when) .*does not apply\b",),
    ),
    "public contract stability": (
        (r"\bpublic contracts?\b", r"\bpublic APIs?\b"),
        (r"\b(additive|backward.compatib|compatible alternatives?|preserve)\b",),
        (r"\bbreaking\b", r"\bunapproved changes?\b"),
        (r"\b(explicit user approval|approval requirements?)\b",),
        (r"\bversioning\b", r"\bversioned\b"),
        (r"\bdeprecation\b", r"\bdeprecations\b"),
        (r"\bmigration\b",),
        (r"\brollback\b", r"\bcompatible alternatives\b"),
    ),
}


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_agent(path: Path, seen_names: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        data = load_toml(path)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: invalid TOML: {exc}"]

    for field in REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path}: {field} must be a non-empty string")

    name = data.get("name")
    if isinstance(name, str):
        if not NAME_PATTERN.fullmatch(name):
            errors.append(f"{path}: invalid agent name {name!r}")
        if name in seen_names:
            errors.append(f"{path}: duplicate agent name {name!r}")
        seen_names.add(name)

    sandbox_mode = data.get("sandbox_mode")
    if sandbox_mode is None:
        errors.append(f"{path}: sandbox_mode must be explicitly declared")
    elif sandbox_mode not in ALLOWED_SANDBOX_MODES:
        errors.append(f"{path}: unsupported sandbox_mode {sandbox_mode!r}")

    instructions = data.get("developer_instructions")
    normalized = " ".join(instructions.split()).lower() if isinstance(instructions, str) else ""
    for policy, concept_groups in POLICY_CONCEPTS.items():
        missing = [
            "/".join(group)
            for group in concept_groups
            if not any(re.search(pattern, normalized) for pattern in group)
        ]
        if missing:
            errors.append(
                f"{path}: developer_instructions missing {policy} concepts: "
                + ", ".join(missing)
            )

    nicknames = data.get("nickname_candidates", [])
    if not isinstance(nicknames, list) or any(not isinstance(n, str) for n in nicknames):
        errors.append(f"{path}: nickname_candidates must be an array of strings")
    elif nicknames:
        if len(nicknames) != len(set(nicknames)):
            errors.append(f"{path}: nickname_candidates must be unique")
        for nickname in nicknames:
            if not nickname or not NICKNAME_PATTERN.fullmatch(nickname):
                errors.append(f"{path}: invalid nickname {nickname!r}")

    return errors


def validate_project_config(path: Path) -> list[str]:
    try:
        data = load_toml(path)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: invalid TOML: {exc}"]

    agents = data.get("agents")
    if not isinstance(agents, dict):
        return [f"{path}: missing [agents] table"]

    errors: list[str] = []
    max_threads = agents.get("max_threads")
    max_depth = agents.get("max_depth")
    if not isinstance(max_threads, int) or max_threads < 1:
        errors.append(f"{path}: agents.max_threads must be a positive integer")
    if not isinstance(max_depth, int) or max_depth < 0:
        errors.append(f"{path}: agents.max_depth must be a non-negative integer")
    return errors


def main() -> int:
    agent_paths = sorted(AGENT_DIR.glob("*.toml"))
    if not agent_paths:
        print(f"No agent templates found in {AGENT_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_names: set[str] = set()
    for path in agent_paths:
        errors.extend(validate_agent(path, seen_names))
    errors.extend(validate_project_config(PROJECT_CONFIG))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(agent_paths)} custom agents and project config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
