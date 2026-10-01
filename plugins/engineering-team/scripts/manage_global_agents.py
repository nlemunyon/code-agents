#!/usr/bin/env python3
"""Safely install Engineering Team agent roles in user-level Codex config."""

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
    print("Python 3.11 or newer is required to manage global agents.", file=sys.stderr)
    raise SystemExit(2)

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_AGENT_DIR = PLUGIN_ROOT / "templates" / "custom-agents"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
INSTALL_SUBDIRECTORY = Path("agents") / "engineering-team"
INSTALL_MANIFEST_NAME = ".install-manifest.json"
BEGIN_MARKER = "# BEGIN engineering-team managed global agents"
END_MARKER = "# END engineering-team managed global agents"
INSERTED_SEPARATOR_MARKER = "# engineering-team inserted separator newline"
MANAGED_BLOCK_PATTERN = re.compile(
    rf"(?ms)^{re.escape(BEGIN_MARKER)}\n.*?^{re.escape(END_MARKER)}(?:\n|$)"
)


class ManagerError(RuntimeError):
    """Raised when an operation would be unsafe or produce invalid config."""


@dataclass(frozen=True)
class AgentTemplate:
    name: str
    description: str
    filename: str
    source_path: Path
    sha256: str

    @property
    def config_file(self) -> str:
        return (INSTALL_SUBDIRECTORY / self.filename).as_posix()


@dataclass(frozen=True)
class ManifestAgent:
    name: str
    filename: str
    sha256: str


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    content: bytes | None
    mode: int


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def toml_string(value: str) -> str:
    """Encode a value as a TOML basic string using compatible JSON escaping."""
    return json.dumps(value, ensure_ascii=False)


def load_agent_templates() -> list[AgentTemplate]:
    templates: list[AgentTemplate] = []
    seen_names: set[str] = set()
    for path in sorted(SOURCE_AGENT_DIR.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise ManagerError(f"Invalid agent template {path}: {exc}") from exc
        name = data.get("name")
        description = data.get("description")
        if not isinstance(name, str) or not name:
            raise ManagerError(f"Agent template {path} has no valid name")
        if not isinstance(description, str) or not description:
            raise ManagerError(f"Agent template {path} has no valid description")
        if name in seen_names:
            raise ManagerError(f"Duplicate agent name in templates: {name}")
        seen_names.add(name)
        templates.append(
            AgentTemplate(
                name=name,
                description=description,
                filename=path.name,
                source_path=path,
                sha256=sha256_file(path),
            )
        )
    if not templates:
        raise ManagerError(f"No agent templates found in {SOURCE_AGENT_DIR}")
    return templates


def plugin_version() -> str:
    try:
        data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManagerError(f"Cannot read plugin manifest {PLUGIN_MANIFEST}: {exc}") from exc
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise ManagerError(f"Plugin manifest {PLUGIN_MANIFEST} has no valid version")
    return version


def resolve_codex_home(value: Path | None) -> Path:
    if value is None:
        configured = os.environ.get("CODEX_HOME")
        value = Path(configured) if configured else Path.home() / ".codex"
    resolved = value.expanduser().resolve()
    if resolved == Path(resolved.anchor):
        raise ManagerError("Refusing to use a filesystem root as CODEX_HOME")
    return resolved


def reject_symlink_components(codex_home: Path, path: Path) -> None:
    """Reject existing symlinks below CODEX_HOME for managed write targets."""
    try:
        relative = path.relative_to(codex_home)
    except ValueError as exc:
        raise ManagerError(f"Managed path is outside CODEX_HOME: {path}") from exc
    current = codex_home
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ManagerError(f"Refusing to manage a symlinked Codex path: {current}")


def managed_paths(codex_home: Path) -> tuple[Path, Path, Path]:
    """Return the config, install folder, and manifest paths."""
    config_path = codex_home / "config.toml"
    install_dir = codex_home / INSTALL_SUBDIRECTORY
    manifest_path = install_dir / INSTALL_MANIFEST_NAME
    reject_symlink_components(codex_home, config_path)
    reject_symlink_components(codex_home, install_dir)
    return config_path, install_dir, manifest_path


def validate_toml(content: str, path: Path) -> dict:
    try:
        return tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise ManagerError(f"Invalid TOML in {path}: {exc}") from exc


def read_config(path: Path) -> str:
    if path.is_symlink():
        raise ManagerError(f"Refusing to replace symlinked Codex config: {path}")
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManagerError(f"Cannot read Codex config {path}: {exc}") from exc
    validate_toml(content, path)
    return content


def remove_managed_block(content: str) -> tuple[str, bool]:
    begin_count = content.count(BEGIN_MARKER)
    end_count = content.count(END_MARKER)
    if begin_count != end_count or begin_count > 1:
        raise ManagerError("Codex config has malformed or duplicate managed-agent markers")
    if begin_count == 0:
        return content, False
    match = MANAGED_BLOCK_PATTERN.search(content)
    if match is None:
        raise ManagerError("Codex config has a malformed managed-agent block")
    before = content[: match.start()]
    after = content[match.end() :]
    if INSERTED_SEPARATOR_MARKER in match.group(0) and not after:
        if not before.endswith("\n"):
            raise ManagerError("Managed-agent separator metadata is inconsistent")
        before = before[:-1]
    return before + after, True


def build_managed_block(
    templates: list[AgentTemplate], version: str, *, inserted_separator: bool
) -> str:
    lines = [
        BEGIN_MARKER,
        f"# Generated by engineering-team {version}; update through manage_global_agents.py.",
    ]
    if inserted_separator:
        lines.append(INSERTED_SEPARATOR_MARKER)
    for template in sorted(templates, key=lambda item: item.name):
        lines.extend(
            [
                "",
                f"[agents.{template.name}]",
                f"description = {toml_string(template.description)}",
                f"config_file = {toml_string(template.config_file)}",
            ]
        )
    lines.extend(["", END_MARKER, ""])
    return "\n".join(lines)


def build_installed_config(
    current: str, templates: list[AgentTemplate], version: str, config_path: Path
) -> tuple[str, bool]:
    unmanaged, had_block = remove_managed_block(current)
    unmanaged_data = validate_toml(unmanaged, config_path)
    agents = unmanaged_data.get("agents", {})
    if not isinstance(agents, dict):
        raise ManagerError("The user-level agents configuration is not a TOML table")
    conflicts = sorted(template.name for template in templates if template.name in agents)
    if conflicts:
        names = ", ".join(conflicts)
        raise ManagerError(
            "Refusing to replace agent roles defined outside the managed block: " + names
        )
    inserted_separator = bool(unmanaged) and not unmanaged.endswith("\n")
    separator = "\n" if inserted_separator else ""
    desired = unmanaged + separator + build_managed_block(
        templates, version, inserted_separator=inserted_separator
    )
    validate_toml(desired, config_path)
    return desired, had_block


def load_install_manifest(path: Path) -> dict:
    if path.is_symlink():
        raise ManagerError(f"Refusing to use symlinked install manifest: {path}")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManagerError(f"Cannot read install manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManagerError(f"Install manifest {path} must contain a JSON object")
    return data


def manifest_agents(manifest: dict) -> list[ManifestAgent]:
    agents = manifest.get("agents", {})
    if not isinstance(agents, dict):
        raise ManagerError("Install manifest agents must contain a JSON object")
    parsed: list[ManifestAgent] = []
    seen_filenames: set[str] = set()
    for name, entry in agents.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ManagerError(f"Install manifest has an invalid agent name: {name!r}")
        if not isinstance(entry, dict):
            raise ManagerError(f"Install manifest entry for {name} must be an object")
        filename = entry.get("filename")
        digest = entry.get("sha256")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".toml")
        ):
            raise ManagerError(
                f"Install manifest entry for {name} has an invalid filename"
            )
        if filename in seen_filenames:
            raise ManagerError(f"Install manifest repeats managed filename: {filename}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ManagerError(f"Install manifest entry for {name} has an invalid sha256")
        seen_filenames.add(filename)
        parsed.append(ManifestAgent(name, filename, digest))
    return parsed


def retired_manifest_agents(
    manifest: dict, templates: list[AgentTemplate]
) -> list[ManifestAgent]:
    current = {(template.name, template.filename) for template in templates}
    return [
        agent
        for agent in manifest_agents(manifest)
        if (agent.name, agent.filename) not in current
    ]


def classify_retired(
    install_dir: Path, retired: list[ManifestAgent]
) -> tuple[list[ManifestAgent], list[ManifestAgent], list[ManifestAgent]]:
    """Split retired roles into missing, preserved, and removable."""
    missing: list[ManifestAgent] = []
    preserved: list[ManifestAgent] = []
    removable: list[ManifestAgent] = []
    for agent in retired:
        target = install_dir / agent.filename
        if not target.exists() and not target.is_symlink():
            missing.append(agent)
        elif target.is_symlink() or sha256_file(target) != agent.sha256:
            preserved.append(agent)
        else:
            removable.append(agent)
    return missing, preserved, removable


def manifest_hash(manifest: dict, template: AgentTemplate) -> str | None:
    for agent in manifest_agents(manifest):
        if agent.name == template.name and agent.filename == template.filename:
            return agent.sha256
    return None


def find_modified_targets(
    install_dir: Path,
    templates: list[AgentTemplate],
    manifest: dict,
) -> list[Path]:
    modified: list[Path] = []
    for template in templates:
        target = install_dir / template.filename
        if target.is_symlink():
            modified.append(target)
            continue
        if not target.exists():
            continue
        current_hash = sha256_file(target)
        previous_hash = manifest_hash(manifest, template)
        if current_hash not in {template.sha256, previous_hash}:
            modified.append(target)
    return modified


def find_symlink_targets(
    install_dir: Path, templates: list[AgentTemplate]
) -> list[Path]:
    return [
        install_dir / template.filename
        for template in templates
        if (install_dir / template.filename).is_symlink()
    ]


def create_manifest(
    templates: list[AgentTemplate],
    version: str,
    retained: list[ManifestAgent] | None = None,
) -> dict:
    agents = {
        template.name: {
            "filename": template.filename,
            "sha256": template.sha256,
        }
        for template in sorted(templates, key=lambda item: item.name)
    }
    for agent in retained or []:
        if agent.name in agents:
            raise ManagerError(
                f"Cannot retain conflicting ownership entry for agent {agent.name}"
            )
        agents[agent.name] = {"filename": agent.filename, "sha256": agent.sha256}
    return {
        "schema_version": 1,
        "plugin": "engineering-team",
        "plugin_version": version,
        "agents": dict(sorted(agents.items())),
    }


def manifest_bytes(manifest: dict) -> bytes:
    return json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def file_content_matches(path: Path, content: bytes) -> bool:
    return path.exists() and not path.is_symlink() and path.read_bytes() == content


def snapshot_file(path: Path) -> FileSnapshot:
    if not path.exists():
        return FileSnapshot(path, None, 0o600)
    return FileSnapshot(path, path.read_bytes(), path.stat().st_mode & 0o777)


def restore_snapshot(snapshot: FileSnapshot) -> None:
    if snapshot.content is None:
        if snapshot.path.exists() and not snapshot.path.is_symlink():
            snapshot.path.unlink()
        return
    if not file_content_matches(snapshot.path, snapshot.content):
        atomic_write(snapshot.path, snapshot.content, snapshot.mode)


def backup_config(config_path: Path, codex_home: Path) -> Path | None:
    if not config_path.exists():
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = codex_home / "backups" / "engineering-team"
    reject_symlink_components(codex_home, backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    candidate = backup_dir / f"config-{timestamp}.toml"
    counter = 1
    while candidate.exists():
        candidate = backup_dir / f"config-{timestamp}-{counter}.toml"
        counter += 1
    shutil.copy2(config_path, candidate)
    return candidate


def install(codex_home: Path, *, dry_run: bool, force: bool) -> int:
    templates = load_agent_templates()
    version = plugin_version()
    config_path, install_dir, manifest_path = managed_paths(codex_home)
    current_config = read_config(config_path)
    desired_config, was_registered = build_installed_config(
        current_config, templates, version, config_path
    )
    manifest = load_install_manifest(manifest_path)
    retired = retired_manifest_agents(manifest, templates)
    _, retired_preserved, retired_removable = classify_retired(install_dir, retired)
    symlinks = find_symlink_targets(install_dir, templates)
    if symlinks:
        paths = "\n".join(f"  - {path}" for path in symlinks)
        raise ManagerError(
            "Refusing to replace symlinked managed agent files:\n" + paths
        )
    modified = find_modified_targets(install_dir, templates, manifest)
    if modified and not force:
        paths = "\n".join(f"  - {path}" for path in modified)
        raise ManagerError(
            "Refusing to overwrite locally modified or symlinked managed agent files:\n"
            f"{paths}\nRe-run with --force only after reviewing those files."
        )

    role_changes = [
        template
        for template in templates
        if not file_content_matches(
            install_dir / template.filename, template.source_path.read_bytes()
        )
    ]
    manifest_content = manifest_bytes(create_manifest(templates, version, retired_preserved))
    manifest_changed = not file_content_matches(manifest_path, manifest_content)
    config_changed = desired_config != current_config
    has_changes = bool(
        role_changes or retired_removable or manifest_changed or config_changed
    )

    action = "Update" if was_registered else "Install"
    if dry_run:
        if not has_changes:
            print(f"No changes required; {len(templates)} global agents are current")
            return 0
        print(f"Would {action.lower()} global registration for {len(templates)} agents")
        if role_changes:
            print(f"Would write {len(role_changes)} role file(s) in {install_dir}:")
            for template in role_changes:
                print(f"  - {template.filename}")
        if retired:
            print(
                "Retired roles from the prior install manifest: "
                + ", ".join(agent.name for agent in retired)
            )
        if retired_removable:
            print(
                f"Would remove {len(retired_removable)} "
                "unmodified retired role file(s)"
            )
        if retired_preserved:
            print(
                f"Would preserve {len(retired_preserved)} "
                "modified or symlinked retired role file(s)"
            )
        if manifest_changed:
            print(f"Would update install manifest: {manifest_path}")
        if config_changed:
            print(f"Would update user-level registration: {config_path}")
        if modified:
            print(
                f"Would replace {len(modified)} modified managed file(s) "
                "because --force was used"
            )
        return 0

    backup = None
    staged_retired: list[tuple[Path, Path, FileSnapshot]] = []
    snapshots = [
        snapshot_file(install_dir / template.filename) for template in role_changes
    ]
    if config_changed:
        snapshots.append(snapshot_file(config_path))
    if manifest_changed:
        snapshots.append(snapshot_file(manifest_path))
    try:
        for template in role_changes:
            target = install_dir / template.filename
            if target.is_symlink():
                raise ManagerError(f"Refusing to replace symlinked agent file: {target}")
            atomic_write(target, template.source_path.read_bytes(), 0o600)

        if config_changed:
            backup = backup_config(config_path, codex_home)
            atomic_write(config_path, desired_config.encode("utf-8"), 0o600)

        for agent in retired_removable:
            target = install_dir / agent.filename
            retired_snapshot = snapshot_file(target)
            descriptor, staged_name = tempfile.mkstemp(
                prefix=f".{target.name}.retired.", dir=install_dir
            )
            os.close(descriptor)
            staged = Path(staged_name)
            try:
                os.replace(target, staged)
                if staged.is_symlink() or sha256_file(staged) != agent.sha256:
                    os.replace(staged, target)
                    raise ManagerError(
                        "Retired role changed during installation; preserved it: "
                        f"{target}"
                    )
            except BaseException:
                staged.unlink(missing_ok=True)
                raise
            staged_retired.append((target, staged, retired_snapshot))

        if manifest_changed:
            atomic_write(manifest_path, manifest_content, 0o600)

        for _, staged, _ in staged_retired:
            staged.unlink()
    except BaseException as exc:
        rollback_errors: list[str] = []
        for target, staged, retired_snapshot in reversed(staged_retired):
            try:
                if staged.exists() or staged.is_symlink():
                    os.replace(staged, target)
                else:
                    restore_snapshot(retired_snapshot)
            except OSError as rollback_exc:
                rollback_errors.append(f"{target}: {rollback_exc}")
        for snapshot in reversed(snapshots):
            try:
                restore_snapshot(snapshot)
            except OSError as rollback_exc:
                rollback_errors.append(f"{snapshot.path}: {rollback_exc}")
        if rollback_errors:
            raise ManagerError(
                "Install failed and transaction rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise

    if not has_changes:
        completed_action = "Verified"
    else:
        completed_action = "Updated" if was_registered else "Installed"
    print(f"{completed_action} {len(templates)} global agents in {install_dir}")
    if retired:
        print(
            "Retired roles from the prior install manifest: "
            + ", ".join(agent.name for agent in retired)
        )
    if retired_removable:
        print(f"Removed {len(retired_removable)} unmodified retired role file(s).")
    if retired_preserved:
        print(
            f"Preserved {len(retired_preserved)} modified or symlinked "
            "retired role file(s)."
        )
    print(f"User-level registration: {config_path}")
    if backup is not None:
        print(f"Configuration backup: {backup}")
    print("Start a new Codex chat or CLI session to load the agent roles.")
    return 0


def status(codex_home: Path) -> int:
    templates = load_agent_templates()
    version = plugin_version()
    config_path, install_dir, manifest_path = managed_paths(codex_home)
    current_config = read_config(config_path)
    desired_config, registered = build_installed_config(
        current_config, templates, version, config_path
    )
    registration_current = registered and desired_config == current_config
    manifest = load_install_manifest(manifest_path)
    retired = retired_manifest_agents(manifest, templates)

    missing: list[str] = []
    modified: list[str] = []
    outdated: list[str] = []
    for template in templates:
        target = install_dir / template.filename
        if not target.exists() or target.is_symlink():
            missing.append(template.name)
            continue
        current_hash = sha256_file(target)
        if current_hash == template.sha256:
            continue
        if current_hash == manifest_hash(manifest, template):
            outdated.append(template.name)
        else:
            modified.append(template.name)

    manifest_current = manifest.get("plugin_version") == version
    healthy = (
        registration_current
        and not missing
        and not modified
        and not outdated
        and not retired
        and manifest_current
    )
    print(f"Registration: {'installed' if registered else 'not installed'}")
    print(f"Plugin version: {version}")
    if missing:
        print("Missing roles: " + ", ".join(missing))
    if outdated:
        print("Roles with updates available: " + ", ".join(outdated))
    if modified:
        print("Locally modified roles: " + ", ".join(modified))
    if retired:
        missing_agents, preserved_agents, clean_agents = classify_retired(install_dir, retired)
        clean_retired = [agent.name for agent in clean_agents]
        preserved_retired = [agent.name for agent in preserved_agents]
        missing_retired = [agent.name for agent in missing_agents]
        if clean_retired:
            print(
                "Unmodified retired roles pending removal: "
                + ", ".join(clean_retired)
            )
        if preserved_retired:
            print(
                "Modified or symlinked retired roles preserved: "
                + ", ".join(preserved_retired)
            )
        if missing_retired:
            print(
                "Retired roles with stale ownership entries: "
                + ", ".join(missing_retired)
            )
    if registered and not manifest_current:
        print("Install manifest does not match the current plugin version")
    if registered and not registration_current:
        print("Managed registration block does not match the current plugin")
    if healthy:
        print(f"Healthy: {len(templates)} global agents are current")
        return 0
    return 1


def uninstall(codex_home: Path, *, dry_run: bool, force: bool) -> int:
    templates = load_agent_templates()
    config_path, install_dir, manifest_path = managed_paths(codex_home)
    current_config = read_config(config_path)
    desired_config, registered = remove_managed_block(current_config)
    validate_toml(desired_config, config_path)
    manifest = load_install_manifest(manifest_path)

    removable: list[Path] = []
    preserved: list[Path] = []
    preserved_agents: list[ManifestAgent] = []
    known_agents = {
        (agent.name, agent.filename): agent for agent in manifest_agents(manifest)
    }
    current_hashes = {
        (template.name, template.filename): template.sha256 for template in templates
    }
    for template in templates:
        known_agents.setdefault(
            (template.name, template.filename),
            ManifestAgent(template.name, template.filename, template.sha256),
        )
    retired_keys = {
        (agent.name, agent.filename)
        for agent in retired_manifest_agents(manifest, templates)
    }
    for key, agent in sorted(known_agents.items()):
        target = install_dir / agent.filename
        if not target.exists() and not target.is_symlink():
            continue
        if target.is_symlink():
            preserved.append(target)
            preserved_agents.append(agent)
            continue
        current_hash = sha256_file(target)
        # Retired roles are removed only with exact prior-manifest ownership proof.
        known_hashes = {agent.sha256, current_hashes.get(key)}
        if current_hash in known_hashes or (force and key not in retired_keys):
            removable.append(target)
        else:
            preserved.append(target)
            preserved_agents.append(agent)
    retired_names = [
        agent.name
        for agent in known_agents.values()
        if (agent.name, agent.filename) in retired_keys
    ]

    if dry_run:
        if registered:
            print(f"Would remove user-level registration from {config_path}")
        else:
            print("No user-level registration found")
        print(f"Would remove {len(removable)} unmodified managed agent file(s)")
        if preserved:
            print(f"Would preserve {len(preserved)} modified or symlinked file(s)")
        if retired_names:
            print(
                "Retired roles from the prior install manifest: "
                + ", ".join(retired_names)
            )
        return 0

    backup = None
    if desired_config != current_config:
        backup = backup_config(config_path, codex_home)
        atomic_write(config_path, desired_config.encode("utf-8"), 0o600)
    for path in removable:
        path.unlink()
    if preserved_agents:
        retained_manifest = manifest_bytes(
            create_manifest(
                [], str(manifest.get("plugin_version", "unknown")), preserved_agents
            )
        )
        if not file_content_matches(manifest_path, retained_manifest):
            atomic_write(manifest_path, retained_manifest, 0o600)
    elif manifest_path.exists() and not manifest_path.is_symlink():
        manifest_path.unlink()
    if install_dir.exists():
        try:
            install_dir.rmdir()
        except OSError:
            pass

    if registered:
        print("Removed user-level Engineering Team agent registration.")
    else:
        print("No user-level registration was present.")
    print(f"Removed {len(removable)} unmodified managed agent file(s).")
    if retired_names:
        print(
            "Retired roles from the prior install manifest: "
            + ", ".join(retired_names)
        )
    if preserved:
        print("Preserved modified or symlinked files:")
        for path in preserved:
            print(f"  - {path}")
    if backup is not None:
        print(f"Configuration backup: {backup}")
    print("Start a new Codex chat or CLI session to refresh the available roles.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        help="Codex user directory (default: $CODEX_HOME or $HOME/.codex)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install or update global agents")
    install_parser.add_argument(
        "--dry-run", action="store_true", help="Report changes without writing"
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace locally modified managed agent files after explicit review",
    )

    subparsers.add_parser("status", help="Check global-agent registration and file integrity")

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove global-agent registration")
    uninstall_parser.add_argument(
        "--dry-run", action="store_true", help="Report changes without writing"
    )
    uninstall_parser.add_argument(
        "--force",
        action="store_true",
        help="Remove locally modified managed agent files after explicit review",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        codex_home = resolve_codex_home(args.codex_home)
        if args.command == "install":
            return install(codex_home, dry_run=args.dry_run, force=args.force)
        if args.command == "status":
            return status(codex_home)
        if args.command == "uninstall":
            return uninstall(codex_home, dry_run=args.dry_run, force=args.force)
        raise ManagerError(f"Unsupported command: {args.command}")
    except (ManagerError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
