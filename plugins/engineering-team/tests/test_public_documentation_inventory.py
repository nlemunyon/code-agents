from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INVENTORY = PLUGIN_ROOT / "public-documentation.json"


class PublicDocumentationInventoryTests(unittest.TestCase):
    def test_inventory_covers_each_public_toolkit_surface(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        actual_ids = {entry["id"] for entry in data["interfaces"]}

        expected_ids = {
            f"skill.{path.parent.name}"
            for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md")
        }
        expected_ids.update(
            f"role.{path.stem.replace('-', '_')}"
            for path in (PLUGIN_ROOT / "templates" / "custom-agents").glob("*.toml")
        )
        expected_ids.update(
            f"cli.{path.stem.replace('_', '-')}"
            for path in (PLUGIN_ROOT / "scripts").glob("*.py")
        )
        expected_ids.update(
            {
                "metadata.plugin",
                "metadata.marketplace",
                "config.prompt-budgets-v1",
                "schema.documentation-evidence-v1",
            }
        )

        self.assertEqual(expected_ids, actual_ids)

    def test_documented_command_examples_execute_successfully(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        command_entries = [
            entry for entry in data["interfaces"] if entry["kind"] == "command"
        ]

        for entry in command_entries:
            with self.subTest(interface=entry["id"]):
                arguments = shlex.split(entry["example"])
                if arguments[0] == "python3":
                    arguments[0] = sys.executable
                with tempfile.TemporaryDirectory() as temporary_home:
                    environment = None
                    if entry["id"] == "cli.manage-global-agents":
                        environment = {
                            **os.environ,
                            "CODEX_HOME": temporary_home,
                        }
                    result = subprocess.run(
                        arguments,
                        cwd=PLUGIN_ROOT.parents[1],
                        check=False,
                        capture_output=True,
                        text=True,
                        env=environment,
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{entry['id']} failed:\n{result.stdout}\n{result.stderr}",
                )
                self.assertTrue(
                    result.stdout.strip() or result.stderr.strip(),
                    f"{entry['id']} returned no result to document",
                )


if __name__ == "__main__":
    unittest.main()
