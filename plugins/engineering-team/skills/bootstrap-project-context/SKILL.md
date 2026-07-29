---
name: bootstrap-project-context
description: Establish or refresh durable repository guidance, project Codex configuration, and necessary agent overrides for onboarding or changed project context. Reuse global roles; do not use for a one-off code change or user-level agent installation.
---

# Bootstrap Project Context

Create a small, evidence-based operating layer for Codex without inventing
project conventions or replacing useful repository guidance.

## Workflow

1. Locate the repository root and read every applicable `AGENTS.md`, project
   configuration file, contributor guide, build manifest, CI workflow, and
   existing `.codex/` or `.agents/` content.
2. Inspect the worktree before editing. Determine whether this is an initial
   bootstrap or refresh. On refresh, read the recorded context baseline when
   present, compare it with the current `HEAD` and worktree, then perform a full
   current-tree rescan so changes outside the Git diff are not missed. Follow
   [the refresh protocol](references/refresh-protocol.md). Never fetch, pull, or
   switch revisions unless the user separately asks; scan the code currently
   present locally.
3. Preserve unrelated changes and human-maintained guidance. Reconcile verified
   facts instead of overwriting the file wholesale. Do not delete or rewrite an
   existing instruction merely because its origin is unknown; prove it stale or
   contradictory, otherwise retain it and report the uncertainty.
4. Map the project using [references/context-checklist.md](references/context-checklist.md).
   Record only verified commands and paths. Capture pinned and targeted external
   versions plus canonical primary documentation sources. Mark unresolved items
   explicitly. List public docs and record the command that checks
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
5. Build a project-specific agent-routing matrix using
   [references/agent-routing.md](references/agent-routing.md). Base routing on
   verified system boundaries, technologies, paths, public contracts, risks,
   edit authority, and required independent review. Record unavailable,
   unnecessary, and project-overridden roles; do not select agents merely
   because their templates exist.
6. Create or update the root `AGENTS.md` with the minimum durable information
   needed for future work: architecture, repository map, commands, conventions,
   verification, security boundaries, change ownership, and portable
   documentation paths. Include an `Agent routing` section containing the
   project-specific matrix and selection rules so planning, delivery, review,
   security, and orchestration skills can choose roles from repository evidence.
   Require repository-relative paths, `$HOME`,
   `<repo-root>`, or the appropriate Windows home variable instead of
   user-specific absolute home paths. Record public contract ownership,
   compatibility promises, baselines, and the rule that breaking changes require
   necessity evidence, explicit user approval, and migration planning.
7. Record a compact `Project context freshness` section in root `AGENTS.md` with
   the scanned revision, dirty-worktree status, evidence paths, and unresolved
   drift. On every refresh, update it only after reconciliation and validation.
   Use the previous revision to summarize added, removed, renamed, or materially
   changed boundaries, commands, contracts, ownership, CI/CD, security, and
   routing. Never treat a commit hash alone as proof that context is current.
8. Add `.codex/config.toml` only when the repository does not already express
   equivalent agent settings. Use
   `../../templates/project/.codex/config.toml` as a baseline, then preserve any
   project settings already present.
9. Inspect whether the needed roles are already registered in user-level Codex
   configuration. Reuse global roles when available. Select only relevant
   templates from `../../templates/custom-agents/` and copy them into
   `.codex/agents/` only when the user requests project-scoped roles or verified
   repository constraints require an override. Do not install personal agents
   or replace same-named files without explicit approval. Include
   `docs_researcher` when work depends on external versioned or rapidly changing
   systems. Include `devsecops_engineer` when the repository contains material
   CI/CD, policy-as-code, provenance, scanner, or secure-promotion ownership.
10. Tailor agent descriptions and instructions only when repository evidence
   justifies a project-specific constraint. Keep reusable behavior in the
   template.
11. Create `.codex/documentation-evidence.json` from
   `../verify-current-documentation/assets/documentation-evidence.json` when the
   project has material version-sensitive external dependencies. Populate known
   claims through `$verify-current-documentation`; do not leave required claims
   implied or falsely verified. When authorized primary-source access is
   unavailable, create the empty bootstrap ledger, record each unresolved
   required claim and its blocked dependent work explicitly in `AGENTS.md`, and
   validate with `--allow-empty`. Do not fabricate or downgrade a required claim
   merely to satisfy the schema. Populate it and validate without `--allow-empty`
   as soon as evidence access is available.
12. Validate TOML syntax, skill paths, documented commands, agent-routing role
   names and ownership boundaries, and instruction
   precedence. Run the path check and the project docs check on changed docs.
   Block when public docs are not complete or the check fails. Run cheap
   read-only checks first; do not run destructive
   setup, migrations, deployment, or release commands. Document an evidence-
   validator command only when its executable project-relative or installed
   plugin path is known; otherwise record the command location as unresolved
   instead of committing a non-executable placeholder.

## Output

Report the files created or updated, the evidence used, commands validated,
detected task signals, selected and excluded agent roles with reasons, routing
and ownership boundaries, independent-review requirements, unresolved project
questions, and recommended next workflow. On refresh, lead with the baseline and
current revision, changed signals detected, context entries added, updated,
retained as uncertain, or removed with evidence, and stale evidence invalidated.
Include documentation sources and unresolved required claims. Keep project
secrets and proprietary details in the target repository.
