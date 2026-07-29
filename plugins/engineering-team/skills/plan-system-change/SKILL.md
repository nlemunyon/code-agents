---
name: plan-system-change
description: Plan a complex cross-system feature, migration, architecture change, or risky refactor using repository evidence and executable work packages. Use before implementation; do not deliver the change, orchestrate an approved plan, or plan narrow, fully specified local work.
---

# Plan System Change

Turn a broad request into an executable, reviewable work graph grounded in the
target repository.

## Workflow

1. Read applicable repository guidance and establish the requested outcome,
   acceptance criteria, exclusions, compatibility promises, and operational
   constraints. Identify missing decisions without blocking on details that can
   be discovered safely.
2. Trace the current implementation and data flow before proposing a future
   design. Use [references/boundary-checklist.md](references/boundary-checklist.md)
   as the mandatory contract, security, evidence, and verification core; then
   read only its linked domain checklists for boundaries in scope. Inventory
   affected public API, Python, MCP, protocol, configuration, event, command,
   and data contracts and the consumers that rely on them. Inventory the
   documentation for each affected public surface and apply
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
3. Delegate independent read-only analysis when two or more boundaries are
   materially affected. Select roles from the canonical
   [agent-routing reference](../bootstrap-project-context/references/agent-routing.md)
   and the project `AGENTS.md` matrix, confirming that task signals match the
   scope. Keep analysis-only roles read-only; use scoped explorers when a
   required role is unavailable. Require evidence, assumptions, risks, and file
   references, and wait for all relevant results.
4. Invoke `$verify-current-documentation` for every material external claim that
   varies by version, date, Region, partition, edition, or configuration. Do not
   make a stale, inferred, unresolved, secondary-only, or target-mismatched
   required claim an implementation premise.
5. Define the change contract first: observable behavior, schemas, public API,
   errors, authorization, compatibility, data ownership, and nonfunctional
   requirements. Classify every public-surface change as none, additive,
   deprecated-but-compatible, or breaking. Prefer additive compatibility. Treat
   a breaking change as blocked unless no compatible alternative works and the
   user explicitly approves the break plus its versioning, deprecation,
   migration, compatibility-window, consumer-impact, and rollback plan.
6. Produce ordered work packages with explicit inputs, outputs, owner role,
   files or modules, dependencies, verification, and rollback. Separate work
   that can run in parallel from work that must remain sequential. Include
   owned work for grade-12-or-lower prose, verified usage, expected results, and
   caller-facing error meaning and recovery, or explicit `Not applicable`
   reasons.
7. Assign one owner to every shared contract, database migration, generated
   artifact, and file set. Never plan concurrent edits to the same ownership
   boundary.
8. Include rollout and recovery for database, data workflow, container, and
   infrastructure changes. Assign repository-scoped CI/CD, policy, provenance,
   scanning, and promotion-control implementation to `devsecops_engineer` while
   keeping deployment, release, repository-settings, credential, and cloud
   mutations separately authorization-gated. Link required documentation claims to the work
   packages that depend on them.
9. Challenge the plan with failure scenarios, upgrade and downgrade behavior,
   partial deployment states, observability gaps, and testability. Revise until
   each acceptance criterion maps to verification evidence.

## Plan format

Return:

1. Outcome and acceptance criteria.
2. Verified current-state summary with file references.
3. Proposed contracts, compatibility classification, consumer impact, approval
   status, and architecture decisions.
4. Ordered work graph, ownership, and parallelization boundaries.
5. Test and verification matrix.
6. Rollout, migration, rollback, and recovery.
7. Documentation evidence ledger status, claim expiry, and blocked work.
8. Public documentation inventory, quality-gate status, and blocked work.
9. Risks, assumptions, open decisions, and explicit non-goals.

Do not edit implementation files while using this skill unless the user also
asks to proceed with delivery.
