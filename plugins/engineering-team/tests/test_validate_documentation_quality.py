from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_documentation_quality.py"
SPEC = importlib.util.spec_from_file_location("documentation_quality", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def run(*arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(value) for value in arguments)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_readable_utf8_prose_passes(tmp_path: Path) -> None:
    document = tmp_path / "guide.md"
    document.write_text(
        "This guide shows you how to start the tool. First, open the file. "
        "Then, choose a name and save your work. The tool will show a short "
        "message when it is done. You can try again if the task does not work. "
        "Café names and other UTF-8 text are safe.\n",
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 0, result.stderr


def test_hard_prose_fails_with_deterministic_diagnostic(tmp_path: Path) -> None:
    document = tmp_path / "hard.md"
    document.write_text(
        "Interoperability conceptualization necessitates extraordinarily "
        "sophisticated organizational communication methodologies. "
        "Institutionalization consequently facilitates multidimensional "
        "characterization and incomprehensible implementation. "
        "Operationalization simultaneously exacerbates architectural "
        "incompatibilities and administrative responsibilities. "
        "Internationalization additionally requires comprehensive "
        "reconceptualization of heterogeneous computational infrastructure.\n",
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 1
    assert f"{document}:1: readability grade" in result.stderr
    assert "exceeds 12" in result.stderr


def test_code_urls_tables_and_short_samples_are_excluded(tmp_path: Path) -> None:
    document = tmp_path / "excluded.md"
    document.write_text(
        "# Supercalifragilisticexpialidocious\n\n"
        "Tiny complicated terminology.\n\n"
        "```python\n"
        "extraordinarily_incomprehensible_implementation()\n"
        "```\n\n"
        "| Conceptualization | Institutionalization |\n"
        "| --- | --- |\n"
        "| internationalization | operationalization |\n\n"
        "`extraordinarily_incomprehensible_implementation()` "
        "https://example.test/extraordinarily/incomprehensible " * 20,
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 0, result.stderr


def test_table_prose_is_checked_but_literal_cells_are_ignored(tmp_path: Path) -> None:
    document = tmp_path / "table.md"
    document.write_text(
        "| id | Meaning |\n"
        "| --- | --- |\n"
        "| api.check | Institutionalization necessitates extraordinarily sophisticated "
        "organizational communication methodologies and comprehensive reconceptualization. |\n",
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 1
    literal = tmp_path / "literal.md"
    literal.write_text("| `api.check` | `HTTP_200` | `value_name` |\n", encoding="utf-8")
    assert run(literal).returncode == 0


def test_default_checks_difficult_ten_word_sample(tmp_path: Path) -> None:
    document = tmp_path / "short.md"
    document.write_text(
        "Institutionalization necessitates extraordinarily sophisticated organizational "
        "communication methodologies through comprehensive reconceptualization processes.\n",
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 1


def test_each_list_item_is_a_sentence_boundary(tmp_path: Path) -> None:
    document = tmp_path / "steps.md"
    document.write_text(
        "- Open the file and read the short note at top\n"
        "- Pick a clear name that your whole team can know\n"
        "- Save the new file in the same work folder\n"
        "- Run the check and fix each issue it may show\n",
        encoding="utf-8",
    )
    result = run(document)
    assert result.returncode == 0, result.stderr


def test_missing_or_invalid_input_is_configuration_error(tmp_path: Path) -> None:
    assert run(tmp_path / "missing.md").returncode == 2
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff")
    assert run(bad).returncode == 2
    assert run("--max-grade", -1, bad).returncode == 2


def inventory_entry(**changes: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "id": "cli.check",
        "kind": "command",
        "source": "scripts/check.py",
        "docs": "reference.md#check-command",
        "example": "python scripts/check.py",
        "expected_return": "Exit status 0 means that all checks passed.",
        "errors": "Exit status 1 means that a check failed.",
        "compatibility": "Additive",
        "owner": "quality_engineer",
    }
    entry.update(changes)
    return entry


def write_inventory(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"interfaces": entries}), encoding="utf-8")


def test_complete_inventory_and_explicit_na_pass(tmp_path: Path) -> None:
    (tmp_path / "reference.md").write_text("# Check command\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check.py").write_text("", encoding="utf-8")
    inventory = tmp_path / "inventory.json"
    write_inventory(
        inventory,
        [inventory_entry(errors={"not_applicable": "This constant cannot fail."})],
    )
    result = run("--inventory", inventory)
    assert result.returncode == 0, result.stderr


def test_inventory_requires_complete_content_and_existing_docs(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    write_inventory(inventory, [inventory_entry(example="", docs="missing.md#nope")])
    result = run("--inventory", inventory)
    assert result.returncode == 1
    assert "missing or empty: example" in result.stderr
    assert "docs file does not exist" in result.stderr
    assert "source path does not exist" in result.stderr


def test_inventory_checks_anchor_and_baseline_drift(tmp_path: Path) -> None:
    (tmp_path / "reference.md").write_text("# Other section\n", encoding="utf-8")
    inventory = tmp_path / "inventory.json"
    baseline = tmp_path / "baseline.json"
    write_inventory(inventory, [inventory_entry(kind="api", source="new.py")])
    write_inventory(
        baseline,
        [inventory_entry(), inventory_entry(id="removed.api", docs={"not_applicable": "Retired"})],
    )
    result = run("--inventory", inventory, "--baseline-inventory", baseline)
    assert result.returncode == 1
    assert "docs anchor not found" in result.stderr
    assert "kind drifted from baseline" in result.stderr
    assert "source drifted from baseline" in result.stderr
    assert "removed.api: missing baseline interface" in result.stderr


def test_bad_inventory_is_input_error(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{bad json", encoding="utf-8")
    assert run("--inventory", inventory).returncode == 2


def test_changed_from_checks_only_added_docs_and_source_prose(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    guide = tmp_path / "guide.md"
    guide.write_text(
        "Institutionalization necessitates extraordinarily sophisticated organizational "
        "communication methodologies through comprehensive reconceptualization processes.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "guide.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    script = tmp_path / "new.py"
    script.write_text(
        "# Institutionalization necessitates extraordinarily sophisticated organizational "
        "communication methodologies through comprehensive reconceptualization processes.\n"
        "value = 'this difficult code literal is not authored documentation at all'\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--changed-from", "HEAD", "."],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert "new.py" in result.stderr
    assert "guide.md" not in result.stderr


def test_changed_from_checks_added_lines_not_legacy_lines(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    guide = tmp_path / "guide.md"
    hard = (
        "Institutionalization necessitates extraordinarily sophisticated organizational "
        "communication methodologies through comprehensive reconceptualization processes.\n"
    )
    guide.write_text(hard, encoding="utf-8")
    subprocess.run(["git", "add", "guide.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    guide.write_text(hard + "This new note is short and clear for every reader today.\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--changed-from", "HEAD", "."],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_changed_from_ignores_ordinary_python_and_toml_code(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "base.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "base.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    (tmp_path / "ordinary.py").write_text(
        "schema = 'Institutionalization necessitates extraordinarily sophisticated "
        "organizational communication methodologies through comprehensive "
        "reconceptualization processes.'\n"
        "def compute(extraordinarily_long_identifier: str) -> str:\n"
        "    return extraordinarily_long_identifier\n",
        encoding="utf-8",
    )
    (tmp_path / "ordinary.toml").write_text(
        'command = "Institutionalization necessitates extraordinarily sophisticated '
        'organizational communication methodologies through comprehensive '
        'reconceptualization processes."\n'
        'sandbox_mode = "workspace-write"\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--changed-from", "HEAD", "."],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_changed_from_does_not_score_agent_toml_instructions(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    role = tmp_path / "role.toml"
    legacy = 'developer_instructions = """Keep this agent rule exact."""\n'
    role.write_text(legacy, encoding="utf-8")
    subprocess.run(["git", "add", "role.toml"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    role.write_text(
        'developer_instructions = """\n'
        "Institutionalization necessitates extraordinarily sophisticated organizational "
        "communication methodologies through comprehensive reconceptualization processes.\n"
        '"""\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--changed-from", "HEAD", "."],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_changed_from_keeps_existing_markdown_fence_context(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    guide = tmp_path / "guide.md"
    baseline = "Run this command:\n\n```text\nexisting-command --safe\n```\n"
    guide.write_text(baseline, encoding="utf-8")
    subprocess.run(["git", "add", "guide.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    guide.write_text(
        baseline.replace(
            "existing-command --safe\n",
            "existing-command --safe\n"
            "institutionalization necessitates extraordinarily sophisticated "
            "organizational communication methodologies through comprehensive "
            "reconceptualization processes\n",
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--changed-from", "HEAD", "."],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    """Adapt the temporary-path tests to the dependency-free unittest runner."""
    del loader, tests, pattern
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if not name.startswith("test_") or not callable(value):
            continue

        def invoke(function=value) -> None:
            with tempfile.TemporaryDirectory() as directory:
                function(Path(directory))

        suite.addTest(unittest.FunctionTestCase(invoke, description=name))
    return suite
