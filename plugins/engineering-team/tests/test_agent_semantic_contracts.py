from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PLUGIN_ROOT / "scripts" / "validate_agent_templates.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_templates_contracts", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class AgentSemanticContractTests(unittest.TestCase):
    def test_all_templates_satisfy_shared_contracts(self) -> None:
        paths = sorted(VALIDATOR.AGENT_DIR.glob("*.toml"))
        self.assertEqual(len(paths), 13)
        for path in paths:
            with self.subTest(agent=path.name):
                self.assertEqual(VALIDATOR.validate_agent(path, set()), [])

    def test_authority_matches_sandbox(self) -> None:
        for path in sorted(VALIDATOR.AGENT_DIR.glob("*.toml")):
            data = VALIDATOR.load_toml(path)
            instructions = " ".join(data["developer_instructions"].lower().split())
            with self.subTest(agent=path.name):
                if data["sandbox_mode"] == "read-only":
                    self.assertRegex(instructions, r"\b(do not edit|remain read-only)\b")
                else:
                    self.assertRegex(
                        instructions,
                        r"\b(edit only (the )?(assigned|files assigned)|one writer owns each)\b",
                    )
                    self.assertRegex(
                        instructions,
                        r"\b(never|do not)\b.{0,100}\b(deploy|deployment|publish|release|live database|cloud resources?)\b",
                    )

    def test_prompts_have_bounded_word_count(self) -> None:
        for path in sorted(VALIDATOR.AGENT_DIR.glob("*.toml")):
            instructions = VALIDATOR.load_toml(path)["developer_instructions"]
            with self.subTest(agent=path.name):
                self.assertLessEqual(len(instructions.split()), 450)


if __name__ == "__main__":
    unittest.main()
