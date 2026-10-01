#!/usr/bin/env python3
"""Check documentation readability and an optional public-interface inventory."""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from collections.abc import Iterable
from pathlib import Path
from typing import Any


DOCUMENT_SUFFIXES = {".adoc", ".markdown", ".md", ".mdx", ".rst", ".txt"}
SKIP_DIRECTORIES = {
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv",
    "dist", "node_modules", "vendor",
}
WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
URL_RE = re.compile(r"(?:https?://|mailto:)\S+")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_RE = re.compile(r"<[^>\n]+>")
SENTENCE_RE = re.compile(r"[.!?]+(?:\s|$)")
VOWELS = frozenset("aeiouy")
REQUIRED_INVENTORY_FIELDS = (
    "id", "kind", "source", "docs", "example", "expected_return",
    "errors", "compatibility", "owner",
)
NA_FIELDS = frozenset({"expected_return", "errors"})


class InputError(Exception):
    """An invalid path, option, or inventory."""


def walk_files(root: Path) -> list[Path]:
    """List files below root in sorted order and skip tool folders."""
    found: list[Path] = []
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if name not in SKIP_DIRECTORIES]
        found.extend(Path(directory) / name for name in filenames)
    return sorted(found)


def iter_documents(inputs: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for candidate in inputs:
        if not candidate.exists():
            raise InputError(f"path does not exist: {candidate}")
        paths = [candidate] if candidate.is_file() else walk_files(candidate)
        for path in paths:
            if any(part in SKIP_DIRECTORIES for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in DOCUMENT_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path


def authored_samples(text: str) -> Iterable[tuple[int, str]]:
    """Yield prose blocks after removing deterministic non-prose Markdown."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 1
    fenced = False
    for number, raw_line in enumerate(text.splitlines(), 1):
        stripped = raw_line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            fenced = not fenced
            continue
        table_line = stripped.startswith("|") and stripped.endswith("|")
        excluded = (
            fenced
            or not stripped
            or stripped.startswith(("#", "=", ".. ", "<!--"))
            or re.match(r"^[|: -]+$", stripped) is not None
            or re.match(r"^\s*\[[^\]]+\]:", raw_line) is not None
        )
        if excluded:
            if current:
                blocks.append((start, current))
                current = []
            continue
        if not current:
            start = number
        if table_line:
            cells = []
            for cell in stripped.strip("|").split("|"):
                cell = INLINE_CODE_RE.sub(" ", cell).strip()
                words = WORD_RE.findall(cell)
                if len(words) >= 2 and not re.fullmatch(r"[\w./:+-]+", cell):
                    cells.append(cell if re.search(r"[.!?]$", cell) else cell + ".")
            if cells:
                if not current:
                    start = number
                current.extend(cells)
            continue
        # Remove list/quote markup but retain the authored prose after it.
        list_item = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", raw_line) is not None
        cleaned = re.sub(r"^\s*(?:[-*+]|\d+[.)]|>)\s+", "", raw_line)
        cleaned = INLINE_CODE_RE.sub(" ", cleaned)
        cleaned = URL_RE.sub(" ", cleaned)
        cleaned = HTML_RE.sub(" ", cleaned)
        cleaned = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", cleaned)
        cleaned = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", cleaned)
        cleaned = re.sub(r"[*_~]+", "", cleaned)
        if cleaned.strip():
            cleaned = cleaned.strip()
            if list_item and not re.search(r"[.!?][\"')\]]?$", cleaned):
                cleaned += "."
            current.append(cleaned)
    if current:
        blocks.append((start, current))
    for line, lines in blocks:
        yield line, " ".join(lines)


def syllable_count(word: str) -> int:
    """Return a deterministic English syllable estimate."""
    value = re.sub("[^a-z]", "", word.lower())
    if not value:
        return 0
    groups = 0
    previous_vowel = False
    for character in value:
        is_vowel = character in VOWELS
        groups += int(is_vowel and not previous_vowel)
        previous_vowel = is_vowel
    if value.endswith("e") and not value.endswith(("le", "ye")) and groups > 1:
        groups -= 1
    if value.endswith("es") and groups > 1 and not value.endswith(("aes", "ees", "oes")):
        groups -= 1
    return max(1, groups)


def flesch_kincaid_grade(text: str) -> tuple[float, int, int]:
    words = WORD_RE.findall(text)
    sentences = len(SENTENCE_RE.findall(text)) or 1
    syllables = sum(syllable_count(word) for word in words)
    grade = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    return grade, len(words), sentences


def readability_violations(
    path: Path, text: str, max_grade: float, min_words: int
) -> list[str]:
    violations = []
    for line, sample in authored_samples(text):
        word_count = len(WORD_RE.findall(sample))
        if word_count < min_words:
            continue
        grade, _, _ = flesch_kincaid_grade(sample)
        if grade > max_grade:
            violations.append(
                f"{path}:{line}: readability grade {grade:.1f} exceeds {max_grade:g} "
                f"({word_count} words)"
            )
    return violations


def validate_readability(path: Path, max_grade: float, min_words: int) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"cannot read UTF-8 documentation {path}: {exc}") from exc
    return readability_violations(path, text, max_grade, min_words)


def added_line_numbers(reference: str, path: Path) -> set[int]:
    """Return current-file line numbers added since a Git reference."""
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        text=True, capture_output=True, check=False,
    ).returncode == 0
    if not tracked:
        return set(range(1, len(path.read_text(encoding="utf-8").splitlines()) + 1))
    result = subprocess.run(
        ["git", "diff", "--unified=0", reference, "--", str(path)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise InputError(result.stderr.strip() or f"git diff failed for {path}")
    numbers: set[int] = set()
    current = 0
    for line in result.stdout.splitlines():
        match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if match:
            current = int(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            numbers.add(current)
            current += 1
        elif line.startswith(" "):
            current += 1
    return numbers


def authored_source_text(path: Path, reference: str) -> str:
    """Extract changed Python comments and true docstrings."""
    try:
        text = path.read_text(encoding="utf-8")
        changed = added_line_numbers(reference, path)
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"cannot read UTF-8 source {path}: {exc}") from exc
    kept: list[str] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        kept.extend(
            token.string.lstrip("# ")
            for token in tokens
            if token.type == tokenize.COMMENT and token.start[0] in changed
        )
        tree = ast.parse(text, filename=str(path))
    except (SyntaxError, tokenize.TokenError) as exc:
        raise InputError(f"cannot parse Python source {path}: {exc}") from exc

    def visit_body(body: list[ast.stmt]) -> None:
        if body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                end = getattr(value, "end_lineno", value.lineno)
                if changed.intersection(range(value.lineno, end + 1)):
                    kept.append(value.value)
        for node in body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                visit_body(node.body)

    visit_body(tree.body)
    return "\n".join(kept)


def changed_files(reference: str, inputs: list[Path]) -> list[Path]:
    """Return tracked changes plus untracked files, limited to requested inputs."""
    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments], text=True, capture_output=True, check=False
        )
        if result.returncode:
            raise InputError(result.stderr.strip() or f"git {' '.join(arguments)} failed")
        return result.stdout

    names = set(git("diff", "--name-only", reference, "--").splitlines())
    names.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    roots = [path.resolve() for path in inputs]
    selected = []
    for name in sorted(names):
        path = Path(name)
        if not path.is_file() or path.suffix.lower() not in DOCUMENT_SUFFIXES | {".py"}:
            continue
        resolved = path.resolve()
        if roots and not any(resolved == root or root.is_dir() and root in resolved.parents for root in roots):
            continue
        selected.append(path)
    return selected


def changed_document_text(reference: str, path: Path) -> str:
    """Keep added document lines and all fence markers from the full file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        changed = added_line_numbers(reference, path)
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"cannot read UTF-8 documentation {path}: {exc}") from exc
    return "\n".join(
        line if number in changed or re.match(r"^\s*(?:```|~~~)", line) else ""
        for number, line in enumerate(lines, 1)
    )


def load_inventory(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"inventory does not exist: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read inventory {path}: {exc}") from exc
    if isinstance(value, dict):
        value = value.get("interfaces", value.get("public_interfaces"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise InputError(f"{path}: inventory must be a JSON list or contain an 'interfaces' list")
    return value


def is_documented(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        reason = value.get("not_applicable") or value.get("n/a")
        return isinstance(reason, str) and bool(reason.strip())
    return False


def validate_inventory(
    inventory_path: Path, entries: list[dict[str, Any]], baseline: list[dict[str, Any]] | None
) -> list[str]:
    violations: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    normalized_docs: dict[Path, str] = {}
    for index, entry in enumerate(entries, 1):
        label = str(entry.get("id") or f"entry {index}")
        missing = [
            field
            for field in REQUIRED_INVENTORY_FIELDS
            if not (
                isinstance(entry.get(field), str)
                and bool(entry[field].strip())
                or field in NA_FIELDS
                and is_documented(entry.get(field))
            )
        ]
        if missing:
            violations.append(f"{inventory_path}: {label}: missing or empty: {', '.join(missing)}")
        identifier = entry.get("id")
        if isinstance(identifier, str) and identifier.strip():
            if identifier in by_id:
                violations.append(f"{inventory_path}: {identifier}: duplicate id")
            by_id[identifier] = entry

        locator = entry.get("docs")
        if isinstance(locator, str) and locator.strip():
            relative, marker, anchor = locator.partition("#")
            doc_path = (inventory_path.parent / relative).resolve()
            if not doc_path.is_file():
                violations.append(f"{inventory_path}: {label}: docs file does not exist: {relative}")
            elif marker and anchor:
                if doc_path not in normalized_docs:
                    try:
                        content = doc_path.read_text(encoding="utf-8").lower()
                    except (OSError, UnicodeDecodeError) as exc:
                        raise InputError(f"cannot read documented content {doc_path}: {exc}") from exc
                    normalized_docs[doc_path] = re.sub(
                        r"\s+", " ", re.sub(r"[^a-z0-9 \n-]", "", content)
                    )
                normalized = re.sub(r"[^a-z0-9 -]", "", anchor.lower()).replace("-", " ")
                if normalized not in normalized_docs[doc_path]:
                    violations.append(f"{inventory_path}: {label}: docs anchor not found: {anchor}")
        source = entry.get("source")
        if isinstance(source, str) and source.strip():
            source_path = (inventory_path.parent / source.partition("#")[0]).resolve()
            if not source_path.exists():
                violations.append(
                    f"{inventory_path}: {label}: source path does not exist: "
                    f"{source.partition('#')[0]}"
                )

    if baseline is not None:
        baseline_by_id = {item["id"]: item for item in baseline if isinstance(item.get("id"), str)}
        for identifier in sorted(set(baseline_by_id) - set(by_id)):
            violations.append(f"{inventory_path}: {identifier}: missing baseline interface")
        for identifier in sorted(set(baseline_by_id) & set(by_id)):
            for field in ("kind", "source"):
                if baseline_by_id[identifier].get(field) != by_id[identifier].get(field):
                    violations.append(
                        f"{inventory_path}: {identifier}: {field} drifted from baseline "
                        f"{baseline_by_id[identifier].get(field)!r} to {by_id[identifier].get(field)!r}"
                    )
    return violations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Documentation files or directories")
    parser.add_argument("--max-grade", type=float, default=12.0)
    parser.add_argument("--min-words", type=int, default=10)
    parser.add_argument(
        "--changed-from",
        metavar="REF",
        help="Check only prose added since this Git reference, plus untracked files",
    )
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--baseline-inventory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_grade < 0 or args.min_words < 1:
        print("ERROR: --max-grade must be nonnegative and --min-words must be positive", file=sys.stderr)
        return 2
    if args.baseline_inventory and not args.inventory:
        print("ERROR: --baseline-inventory requires --inventory", file=sys.stderr)
        return 2
    if not args.paths and not args.inventory:
        print("ERROR: provide a documentation path or --inventory", file=sys.stderr)
        return 2
    try:
        violations: list[str] = []
        if args.changed_from:
            documents = changed_files(args.changed_from, args.paths)
            for document in documents:
                if document.suffix.lower() == ".py":
                    text = authored_source_text(document, args.changed_from)
                else:
                    text = changed_document_text(args.changed_from, document)
                violations.extend(
                    readability_violations(document, text, args.max_grade, args.min_words)
                )
        else:
            documents = list(iter_documents(args.paths))
            for document in documents:
                violations.extend(validate_readability(document, args.max_grade, args.min_words))
        if args.inventory:
            entries = load_inventory(args.inventory)
            baseline = load_inventory(args.baseline_inventory) if args.baseline_inventory else None
            violations.extend(validate_inventory(args.inventory, entries, baseline))
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if violations:
        for violation in sorted(violations):
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1
    inventory_count = len(entries) if args.inventory else 0
    print(f"Validated {len(documents)} documentation file(s) and {inventory_count} interface(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
