from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "validate_prompt_budgets.py"
SPEC = importlib.util.spec_from_file_location("validate_prompt_budgets", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def validate_mutated(mutate, *, show_duplicates: bool = False) -> tuple[list[str], list[str]]:
    config = json.loads(
        (PLUGIN_ROOT / "prompt-budgets.json").read_text(encoding="utf-8")
    )
    mutate(config)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "budgets.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return VALIDATOR.validate(path, show_duplicates=show_duplicates)


class PromptBudgetTests(unittest.TestCase):
    def assert_invalid_config(self, mutate) -> None:
        with self.assertRaises(VALIDATOR.BudgetError):
            validate_mutated(mutate)

    def test_repository_prompt_budgets_pass(self) -> None:
        errors, reports = VALIDATOR.validate(
            PLUGIN_ROOT / "prompt-budgets.json",
            show_duplicates=True,
        )
        self.assertFalse(errors, errors)
        self.assertTrue(any("skill-catalog" in item for item in reports))
        self.assertTrue(any(item.startswith("duplicate ") for item in reports))

    def test_growth_over_allowance_fails(self) -> None:
        def mutate(config) -> None:
            group = next(item for item in config["groups"] if item["id"] == "skill-catalog")
            group["baseline_words"] = 1
            group["baseline_characters"] = 1

        errors, _ = validate_mutated(mutate)
        self.assertTrue(any("skill-catalog" in error for error in errors))

    def test_unapproved_repeated_prompt_prose_fails(self) -> None:
        def mutate(config) -> None:
            config["duplicate_policy"]["allowed_hashes"] = []

        errors, _ = validate_mutated(mutate, show_duplicates=True)
        self.assertTrue(any(error.startswith("duplicate ") for error in errors))

    def test_missing_canonical_group_fails_closed(self) -> None:
        self.assert_invalid_config(lambda config: config["groups"].pop())

    def test_duplicate_group_id_fails_closed(self) -> None:
        def mutate(config) -> None:
            config["groups"][1]["id"] = config["groups"][0]["id"]

        self.assert_invalid_config(mutate)

    def test_missing_baseline_fails_closed(self) -> None:
        self.assert_invalid_config(
            lambda config: config["groups"][0].pop("baseline_words")
        )

    def test_missing_canonical_scenario_fails_closed(self) -> None:
        self.assert_invalid_config(lambda config: config["scenarios"].pop())

    def test_invalid_scenario_member_fails_closed(self) -> None:
        def mutate(config) -> None:
            config["scenarios"][0]["members"][0]["group"] = "missing-group"

        self.assert_invalid_config(mutate)

    def test_narrowed_group_paths_fail_closed(self) -> None:
        def mutate(config) -> None:
            config["groups"][1]["paths"] = ["skills/plan-system-change/SKILL.md"]

        self.assert_invalid_config(mutate)

    def test_changed_content_selector_fails_closed(self) -> None:
        def mutate(config) -> None:
            config["groups"][1]["content"] = "full_file"

        self.assert_invalid_config(mutate)

    def test_removed_scenario_member_fails_closed(self) -> None:
        def mutate(config) -> None:
            config["scenarios"][0]["members"].pop()

        self.assert_invalid_config(mutate)


if __name__ == "__main__":
    unittest.main()
