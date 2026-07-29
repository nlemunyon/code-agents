---
name: deliver-system-change
description: Implement an approved complex cross-system plan with explicit ownership, staged integration, tests, and independent review. Use for bounded delivery, not initial planning, full audit-remediation orchestration, deployment, release, migration application, or production mutation without separate authorization.
---

# Deliver System Change

Deliver a vertical slice without losing contract consistency or allowing
parallel agents to collide.

## Entry criteria

Confirm an outcome, acceptance criteria, and an evidence-based plan. If those
are missing or material architecture decisions remain open, invoke
`$plan-system-change` before implementation. Validate required external claims
through `$verify-current-documentation`; do not start dependent implementation
while the ledger contains stale, inferred, unresolved, secondary-only, or
target-mismatched required claims. Require a compatibility classification for
every affected public surface. Do not implement a breaking change without proof
that no compatible alternative works, explicit user approval, and an approved
versioning, deprecation, migration, compatibility-window, consumer-impact, and
rollback plan.

## Orchestration

1. Read applicable repository instructions, inspect worktree state, and preserve
   unrelated changes. Use the project `AGENTS.md` agent-routing matrix when
   present, but treat it as selection evidence rather than edit or deployment
   authority.
2. Convert the plan into bounded assignments using
   [references/work-package-contract.md](references/work-package-contract.md).
   Assign each file, contract, migration, and generated artifact to exactly one
   writer. Apply
   [the documentation quality contract](references/documentation-quality-contract.md)
   to every affected public surface.
3. Select the narrowest roles from the canonical
   [agent-routing reference](../bootstrap-project-context/references/agent-routing.md)
   and the verified project matrix. Preserve its AI/ML-versus-data ownership
   split and read-only analysis roles. Role selection never grants edit or
   deployment authority.
4. Spawn subagents only for work packages that are independent at the current
   phase. Give each agent exact scope, edit authority, dependencies, acceptance
   criteria, and required handoff. Keep contract-first and integration work
   sequential. Wait for all agents in a phase before integration.
5. If custom roles are unavailable, use worker or explorer agents with the same
   bounded instructions. Never broaden permissions to compensate.

## Delivery phases

1. Baseline public contracts and lock shared signatures, schemas, errors, and
   semantics with focused contract, import, schema, or snapshot tests before
   parallel implementation. Verify version-sensitive external premises and
   validate `.codex/documentation-evidence.json`.
2. Implement data prerequisites safely. Keep migrations backward compatible
   across mixed-version deployments and include rollback or forward-recovery.
3. Implement API behavior, then client and MCP adapters against the agreed
   contract. Prefer additive fields, operations, methods, and tools while
   preserving existing behavior. Avoid duplicating transport or domain logic.
4. Implement container and infrastructure-as-code changes only when in scope.
   Verify current service availability and partition-specific behavior for
   GovCloud. Route delivery-security automation through
   `$implement-devsecops-controls`. Do not mutate cloud resources, repository
   settings, credentials, environments, releases, or deployments without
   separate authorization.
5. Integrate agent handoffs centrally. Inspect every diff, resolve overlap, and
   run narrow tests before broader suites.
6. Exercise normal, invalid, unauthorized, partial-failure, retry, concurrency,
   and rollback paths as applicable. Validate the user-facing Python and MCP
   experiences, not only server internals.
7. List public docs in scope. Update guides, examples, release notes, docstrings,
   and key comments. Use grade 12 prose. Add a tested use case, its result, and
   error help. State `Not applicable` with a cause when needed.
   Use project-relative paths, `$HOME`, `<repo-root>`, or the appropriate Windows
   home variable; never embed a user-specific absolute home path. Run the
   bundled portable-documentation validator on changed docs. Respect file
   ownership when documentation lives inside source files. Block when the docs
   list or check is missing or fails.
8. Re-run documentation evidence validation when dependency versions, target
   environments, configuration, or authoritative documentation changed during
   delivery.
9. Delegate a final read-only review to `quality_engineer`, plus
   `data_engineer`, `devsecops_engineer`, `govcloud_engineer`, or
   `security_engineer` when their
   boundaries or risks changed. Address actionable findings and rerun affected
   verification.

## Handoff

Report behavior delivered, contracts changed, migrations or infrastructure
included, documentation updated, files changed by owner, tests and commands run,
public-surface compatibility classification and approval status, documentation
evidence status and expiry, rollout and rollback, residual risks, and any action
still requiring user authorization. Do not deploy, publish, release, apply
migrations, or message external systems unless explicitly requested.
