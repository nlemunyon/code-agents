from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PLUGIN_ROOT / "scripts" / "validate_agent_templates.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_templates", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class AgentDocumentationPolicyTests(unittest.TestCase):
    def test_every_agent_satisfies_semantic_policies(self) -> None:
        paths = sorted(VALIDATOR.AGENT_DIR.glob("*.toml"))

        self.assertEqual(len(paths), 13)
        for path in paths:
            with self.subTest(agent=path.name):
                self.assertEqual(VALIDATOR.validate_agent(path, set()), [])

    def test_validator_accepts_equivalent_concise_wording(self) -> None:
        source_path = VALIDATOR.AGENT_DIR / "api-engineer.toml"
        source = source_path.read_text(encoding="utf-8")
        source = source.replace(
            "Training knowledge is not evidence.",
            "Never use training knowledge as evidence.",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "agent.toml"
            path.write_text(source, encoding="utf-8")
            self.assertEqual(VALIDATOR.validate_agent(path, set()), [])

    def test_validator_rejects_each_missing_policy_concept(self) -> None:
        source = (
            VALIDATOR.AGENT_DIR / "api-engineer.toml"
        ).read_text(encoding="utf-8")
        cases = (
            ("grade 12", "grade 12 readability"),
            ("developer documentation", "public-surface developer documentation"),
            ("explicit user approval", "public contract stability"),
            ("training knowledge", "documentation evidence"),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            for marker, expected_error in cases:
                with self.subTest(marker=marker):
                    path = Path(temporary_directory) / "agent.toml"
                    path.write_text(source.replace(marker, ""), encoding="utf-8")
                    errors = VALIDATOR.validate_agent(path, set())
                    self.assertTrue(
                        any(expected_error in error for error in errors),
                        errors,
                    )


if __name__ == "__main__":
    unittest.main()
