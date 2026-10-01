#!/usr/bin/env python3
"""Validate stable prompt-size proxies and report repeated prompt prose."""

from __future__ import annotations

import os
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
    print("Python 3.11 or newer is required to validate prompt budgets.", file=sys.stderr)
    raise SystemExit(2)

import argparse
import hashlib
import json
import re
from collections import defaultdict


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORD_RE = re.compile(r"\S+")
SKILL_DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)
REQUIRED_GROUPS = {
    "repository-guidance": (("../../AGENTS.md",), "full_file"),
    "skill-catalog": (("skills/*/SKILL.md",), "skill_description"),
    "skill-entrypoints": (("skills/*/SKILL.md",), "full_file"),
    "agent-prompts": (("templates/custom-agents/*.toml",), "agent_instructions"),
    "on-demand-references": (("skills/*/references/*.md",), "full_file"),
}
REQUIRED_SCENARIOS = {
    "largest-selected-skill": (
        ("repository-guidance", "total"),
        ("skill-catalog", "total"),
        ("skill-entrypoints", "maximum_file"),
        ("agent-prompts", "maximum_file"),
    ),
    "largest-composite-with-reference": (
        ("repository-guidance", "total"),
        ("skill-catalog", "total"),
        ("skill-entrypoints", "maximum_file"),
        ("agent-prompts", "maximum_file"),
        ("on-demand-references", "maximum_file"),
    ),
}
REQUIRED_GROUP_IDS = set(REQUIRED_GROUPS)
REQUIRED_SCENARIO_IDS = set(REQUIRED_SCENARIOS)
CONTENT_SELECTORS = {"full_file", "skill_description", "agent_instructions"}
AGGREGATES = {"total", "maximum_file"}


class BudgetError(Exception):
    """A prompt budget or source file is invalid."""


def measure(text: str) -> tuple[int, int]:
    return len(WORD_RE.findall(text)), len(text)


def read_content(path: Path, content: str) -> str:
    text = path.read_text(encoding="utf-8")
    if content == "full_file":
        return text
    if content == "skill_description":
        match = SKILL_DESCRIPTION_RE.search(text)
        if match is None:
            raise BudgetError(f"{path}: missing skill description")
        return match.group(1).strip()
    if content == "agent_instructions":
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        value = data.get("developer_instructions")
        if not isinstance(value, str) or not value.strip():
            raise BudgetError(f"{path}: missing developer_instructions")
        return value
    raise BudgetError(f"unsupported content selector: {content!r}")


def allowance(baseline: int, percent: float, minimum: int) -> int:
    return max(minimum, int(baseline * percent / 100))


def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise BudgetError(f"{path}: schema_version must be 1")
    require_config_shape(data, path)
    return data


def require_positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise BudgetError(f"{label} must be a positive integer")
    return value


def require_nonnegative_number(value: object, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value < 0
    ):
        raise BudgetError(f"{label} must be a nonnegative number")
    return float(value)


def require_config_shape(config: dict, path: Path) -> None:
    """Reject incomplete policies so removing a budget cannot disable its gate."""
    policy = config.get("growth_policy")
    if not isinstance(policy, dict):
        raise BudgetError(f"{path}: growth_policy must be an object")
    require_nonnegative_number(
        policy.get("maximum_percent"),
        f"{path}: growth_policy.maximum_percent",
    )
    require_positive_int(
        policy.get("minimum_word_allowance"),
        f"{path}: growth_policy.minimum_word_allowance",
    )
    require_positive_int(
        policy.get("minimum_character_allowance"),
        f"{path}: growth_policy.minimum_character_allowance",
    )

    groups = config.get("groups")
    if not isinstance(groups, list) or not groups:
        raise BudgetError(f"{path}: groups must be a non-empty list")
    group_ids: list[str] = []
    for index, group in enumerate(groups):
        label = f"{path}: groups[{index}]"
        if not isinstance(group, dict):
            raise BudgetError(f"{label} must be an object")
        group_id = group.get("id")
        if not isinstance(group_id, str) or not group_id:
            raise BudgetError(f"{label}.id must be a non-empty string")
        group_ids.append(group_id)
        patterns = group.get("paths")
        if (
            not isinstance(patterns, list)
            or not patterns
            or any(not isinstance(item, str) or not item for item in patterns)
        ):
            raise BudgetError(f"{label}.paths must contain non-empty strings")
        if group.get("content") not in CONTENT_SELECTORS:
            raise BudgetError(f"{label}.content is not supported")
        expected_paths, expected_content = REQUIRED_GROUPS.get(
            group_id, (None, None)
        )
        if tuple(patterns) != expected_paths or group.get("content") != expected_content:
            raise BudgetError(
                f"{label} must use the canonical paths and content selector"
            )
        for field in ("baseline_words", "baseline_characters", "maximum_file_words"):
            require_positive_int(group.get(field), f"{label}.{field}")
        if "optimization_baseline_words" in group:
            require_positive_int(
                group["optimization_baseline_words"],
                f"{label}.optimization_baseline_words",
            )
    if len(group_ids) != len(set(group_ids)):
        raise BudgetError(f"{path}: group ids must be unique")
    if set(group_ids) != REQUIRED_GROUP_IDS:
        raise BudgetError(
            f"{path}: group ids must be exactly {sorted(REQUIRED_GROUP_IDS)}"
        )

    scenarios = config.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise BudgetError(f"{path}: scenarios must be a non-empty list")
    scenario_ids: list[str] = []
    for index, scenario in enumerate(scenarios):
        label = f"{path}: scenarios[{index}]"
        if not isinstance(scenario, dict):
            raise BudgetError(f"{label} must be an object")
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise BudgetError(f"{label}.id must be a non-empty string")
        scenario_ids.append(scenario_id)
        require_positive_int(scenario.get("baseline_words"), f"{label}.baseline_words")
        if "optimization_baseline_words" in scenario:
            require_positive_int(
                scenario["optimization_baseline_words"],
                f"{label}.optimization_baseline_words",
            )
        members = scenario.get("members")
        if not isinstance(members, list) or not members:
            raise BudgetError(f"{label}.members must be a non-empty list")
        for member in members:
            if (
                not isinstance(member, dict)
                or member.get("group") not in REQUIRED_GROUP_IDS
                or member.get("aggregate") not in AGGREGATES
            ):
                raise BudgetError(f"{label}: invalid member {member!r}")
        actual_members = tuple(
            (member["group"], member["aggregate"]) for member in members
        )
        if actual_members != REQUIRED_SCENARIOS.get(scenario_id):
            raise BudgetError(f"{label} must use the canonical ordered members")
    if len(scenario_ids) != len(set(scenario_ids)):
        raise BudgetError(f"{path}: scenario ids must be unique")
    if set(scenario_ids) != REQUIRED_SCENARIO_IDS:
        raise BudgetError(
            f"{path}: scenario ids must be exactly {sorted(REQUIRED_SCENARIO_IDS)}"
        )

    duplicate_policy = config.get("duplicate_policy")
    if not isinstance(duplicate_policy, dict):
        raise BudgetError(f"{path}: duplicate_policy must be an object")
    require_positive_int(
        duplicate_policy.get("minimum_files"),
        f"{path}: duplicate_policy.minimum_files",
    )
    hashes = duplicate_policy.get("allowed_hashes")
    if (
        not isinstance(hashes, list)
        or any(not isinstance(item, str) or not item for item in hashes)
        or len(hashes) != len(set(hashes))
    ):
        raise BudgetError(
            f"{path}: duplicate_policy.allowed_hashes must contain unique strings"
        )


def duplicate_paragraphs(texts: dict[Path, str]) -> list[tuple[int, int, str, str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    original: dict[str, str] = {}
    for path, text in texts.items():
        for paragraph in re.split(r"\n\s*\n", text):
            normalized = " ".join(paragraph.split())
            if len(normalized.split()) < 12:
                continue
            digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
            owners[digest].add(str(path))
            original[digest] = normalized
    return sorted(
        (
            len(path_set),
            len(original[digest].split()),
            digest,
            original[digest],
        )
        for digest, path_set in owners.items()
        if len(path_set) >= 3
    )


def validate(config_path: Path, *, show_duplicates: bool) -> tuple[list[str], list[str]]:
    config = load_config(config_path)
    policy = config["growth_policy"]
    percent = float(policy["maximum_percent"])
    minimum_words = int(policy["minimum_word_allowance"])
    minimum_chars = int(policy["minimum_character_allowance"])
    errors: list[str] = []
    reports: list[str] = []
    results: dict[str, dict[str, int]] = {}
    prompt_texts: dict[Path, str] = {}

    groups = config["groups"]

    for group in groups:
        group_id = group.get("id")
        patterns = group.get("paths")
        content = group.get("content")
        if not isinstance(group_id, str) or not isinstance(patterns, list):
            raise BudgetError(f"{config_path}: invalid group")
        paths = sorted(
            {
                path
                for pattern in patterns
                if isinstance(pattern, str)
                for path in PLUGIN_ROOT.glob(pattern)
                if path.is_file()
            }
        )
        if not paths:
            errors.append(f"{group_id}: no files matched")
            continue
        texts = [read_content(path, content) for path in paths]
        values = [measure(text) for text in texts]
        total_words = sum(words for words, _ in values)
        total_chars = sum(chars for _, chars in values)
        max_words = max(words for words, _ in values)
        results[group_id] = {
            "total": total_words,
            "maximum_file": max_words,
        }
        reports.append(
            f"{group_id}: {len(paths)} files, {total_words} words, "
            f"{total_chars} characters, maximum {max_words} words"
        )
        optimization_baseline = group.get("optimization_baseline_words")
        if isinstance(optimization_baseline, int) and optimization_baseline > 0:
            reduction = optimization_baseline - total_words
            reports.append(
                f"{group_id}: optimization change {reduction:+d} words "
                f"({reduction / optimization_baseline:.1%})"
            )
        baseline_words = group["baseline_words"]
        baseline_chars = group["baseline_characters"]
        word_limit = baseline_words + allowance(baseline_words, percent, minimum_words)
        char_limit = baseline_chars + allowance(baseline_chars, percent, minimum_chars)
        if total_words > word_limit:
            errors.append(f"{group_id}: {total_words} words exceeds {word_limit}")
        if total_chars > char_limit:
            errors.append(f"{group_id}: {total_chars} characters exceeds {char_limit}")
        file_limit = group["maximum_file_words"]
        if max_words > file_limit:
            errors.append(f"{group_id}: largest file has {max_words} words; limit is {file_limit}")
        if content in {"full_file", "agent_instructions"} and not group.get("growth_only"):
            prompt_texts.update(zip(paths, texts))

    for scenario in config["scenarios"]:
        scenario_id = scenario.get("id")
        total = 0
        for member in scenario.get("members", []):
            group_id = member.get("group")
            aggregate = member.get("aggregate")
            if group_id not in results or aggregate not in AGGREGATES:
                raise BudgetError(f"{scenario_id}: invalid member {member!r}")
            total += results[group_id][aggregate]
        baseline = scenario["baseline_words"]
        limit = baseline + allowance(baseline, percent, minimum_words)
        reports.append(f"{scenario_id}: {total} proxy words; limit {limit}")
        optimization_baseline = scenario.get("optimization_baseline_words")
        if isinstance(optimization_baseline, int) and optimization_baseline > 0:
            reduction = optimization_baseline - total
            reports.append(
                f"{scenario_id}: optimization change {reduction:+d} proxy words "
                f"({reduction / optimization_baseline:.1%})"
            )
        if total > limit:
            errors.append(f"{scenario_id}: {total} proxy words exceeds {limit}")

    duplicate_policy = config["duplicate_policy"]
    minimum_files = duplicate_policy["minimum_files"]
    allowed_hashes = set(duplicate_policy["allowed_hashes"])
    for copies, words, digest, paragraph in duplicate_paragraphs(prompt_texts):
        if copies < minimum_files:
            continue
        if show_duplicates:
            reports.append(
                f"duplicate {digest}: {copies} files x {words} words: {paragraph[:100]}"
            )
        if digest not in allowed_hashes:
            errors.append(
                f"duplicate {digest}: unapproved {words}-word paragraph in {copies} files"
            )
    return errors, reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PLUGIN_ROOT / "prompt-budgets.json",
    )
    parser.add_argument("--show-duplicates", action="store_true")
    args = parser.parse_args()
    try:
        errors, reports = validate(args.config, show_duplicates=args.show_duplicates)
    except (BudgetError, OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for report in reports:
        print(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Prompt budgets passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
