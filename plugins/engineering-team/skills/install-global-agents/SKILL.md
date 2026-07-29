---
name: install-global-agents
description: Install, inspect, update, or safely uninstall reusable Engineering Team agents in user-level Codex configuration. Use for global roles across repositories, not project-specific context, architecture, commands, credentials, policy, or local agent overrides.
---

# Install Global Agents

Manage reusable roles without moving repository facts into user-level config.

## Workflow

1. Resolve `../../scripts/manage_global_agents.py` relative to this `SKILL.md`.
   Do not copy the resolved machine-specific path into documentation.
2. Run `status` first. Treat a nonzero result as state to inspect, not permission
   to overwrite anything.
3. Before installation or update, run `install --dry-run` and report the target
   Codex home, registration file, role count, conflicts, and modified managed
   files. User-level writes require an explicit request from the user.
4. Run `install` only after the dry run is clean. Do not use `--force` unless the
   user explicitly approves replacement after reviewing every modified managed
   file. Never use it to bypass role-name collisions outside the managed block.
5. Run `status` after installation and require a healthy result.
6. Tell the user to start a new Codex chat or CLI session.

The manager defaults to `$CODEX_HOME` and otherwise `$HOME/.codex`. It installs
agent files under the user-level `agents/engineering-team/` directory and adds a
marked block to `config.toml`. It validates the existing and generated TOML,
preserves unrelated text and comments, refuses external role-name collisions,
backs up changed configuration, writes atomically, skips unchanged files, and
records file hashes.

## Uninstall

Run `uninstall --dry-run` before `uninstall`. Remove only the marked
registration and hash-matched managed files. Preserve locally modified or
symlinked files by default. Use `--force` only with explicit approval after
showing the exact managed files it would remove.

## Scope boundary

Keep `AGENTS.md`, verified build and test commands, architecture, security
boundaries, documentation evidence, credentials, and project-specific agent
overrides in the target repository. Global installation supplies reusable role
behavior; it does not bootstrap or understand a repository.
