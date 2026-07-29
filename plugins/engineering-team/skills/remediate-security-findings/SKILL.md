---
name: remediate-security-findings
description: Implement and verify fixes for explicitly selected, validated security findings. Use for bounded remediation, not discovering findings, broad hardening, iterative repository-wide audit-remediation, compliance certification, live exploitation, production deployment, or unapproved breaking public contracts.
---

# Remediate Security Findings

Close each selected attack path with the smallest compatible change and prove
the vulnerable behavior no longer succeeds.

## Entry criteria

1. Resolve the repository root, applicable instructions, comparison base,
   selected stable finding IDs, `audit_scope`, exact
   `remediation_write_scope`, and outcome. Audit coverage never grants write
   authority; required writes outside that scope are blocked follow-ups.
2. Require each finding's canonical root-cause key, location, attack path,
   impact, preconditions, evidence, comparison bases, and predecessors. Validate
   missing or stale material facts read-only; invoke `$audit-system-security`
   only when discovery or broad re-audit is requested.
3. Baseline vulnerable behavior with a safe regression assertion when practical.
   Keep payloads in isolated fixtures, harnesses, or memory; never exercise
   production, live services, external targets, or third parties.
4. Classify affected public contracts as unchanged, additive,
   deprecated-compatible, or breaking. Stop before a breaking change unless the
   user explicitly approves it after alternatives are exhausted and versioning,
   deprecation, migration, compatibility-window, consumer, and rollback plans
   are documented.
5. Do not infer authority to deploy, release, apply migrations, rotate or revoke
   credentials, mutate cloud or databases, contact systems, or disclose details.
6. Read the project `AGENTS.md` agent-routing matrix. Resolve role availability,
   overrides, independence, and actual tool capability before assignment.

## Workflow

1. Load or create
   [the security iteration record](../secure-system-iteratively/references/security-iteration-record.md).
   Persist it at a project-approved path before mutation, or append to the
   parent orchestration ledger. Do not use a response-only record as
   authoritative remediation or resume evidence.
   Reconstruct each path against the current tree and resolved environment.
   Record already-fixed, duplicate, invalid, proposed-risk-acceptance, and
   blocked dispositions without changing code. Risk is accepted only with an
   accountable human decision owner and approval reference.
2. Use [references/remediation-checklist.md](references/remediation-checklist.md)
   for relevant controls. Eliminate dangerous behavior at the narrowest trusted
   boundary instead of filtering payloads or suppressing diagnostics.
3. Invoke `$verify-current-documentation` for material volatile behavior and
   validate `.codex/documentation-evidence.json` when a decision depends on it.
4. Define one bounded work package per root cause: owned files, exclusions,
   dependencies, acceptance criteria, contract impact, evidence, tests, and
   handoff. Assign each file, migration, schema, contract, lockfile, and generated
   artifact to exactly one writer.
5. Use the resolved project routing matrix to choose the narrowest available
   owner: `api_engineer`, `client_engineer`, `ai_ml_engineer`, `data_engineer`,
   `devsecops_engineer`, `govcloud_engineer`, or `technical_writer`. Use
   `$implement-devsecops-controls` for CI/CD, build, policy, provenance, scanner,
   and promotion-control findings. Keep an independent
   `security_engineer` for final validation. Prefer a capability-read-only
   reviewer; if it has workspace-write tools, instructions do not enforce
   read-only operation, so constrain scope, inspect for mutations, and report the
   residual limitation.
6. Implement the smallest root-cause fix. Preserve unrelated changes; avoid
   opportunistic refactors, speculative hardening, broad upgrades, and generated
   edits without their source.
7. Add tests for the original proof, normal behavior, boundaries, authorization
   failure, malformed input, and applicable compatibility paths. Ensure the
   regression test would fail without the fix.
8. Run focused then proportionate broader verification, including contract and
   documentation checks. Inspect the diff for secrets, unsafe examples, disabled
   controls, and accidental contract changes. Inventory affected public
   documentation and apply
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
   Fail closed unless authored prose is grade 12 or lower and every affected
   surface has verified usage, expected results, and caller-facing error meaning
   and recovery, or an explicit `Not applicable` reason.
9. Have the independent security reviewer re-trace the original path, relevant
   bypasses, and alternate in-scope sinks. Address validated gaps and rerun
   affected checks.
10. Enforce active iteration, finding, elapsed-time, explicit token, and
    cumulative-file budgets. Checkpoint after classification, each batch, and
    validation. Stop before exceeding a limit and persist the next action and
    resume condition as blocked rather than expanding scope.

## Handoff

For each finding report stable ID, canonical root-cause key, comparison bases,
predecessors, disposition, changed files, remediation, validation, tests and
results, contract classification, documentation evidence, rollout and rollback,
and residual risk. List blocked follow-ups and resume conditions. Distinguish
implemented controls and tests from compliance, certification, authorization,
or formal assessor conclusions.
