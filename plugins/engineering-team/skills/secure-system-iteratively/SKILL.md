---
name: secure-system-iteratively
description: Run a bounded, independent audit-remediate-re-audit loop over a stable scope. Use for iterative security convergence; not for audit-only work, preselected fixes, penetration testing, production mutation, compliance certification, or open-ended hardening.
---

# Secure System Iteratively

Compose `$audit-system-security` and `$remediate-security-findings` while
preserving scope, write authority, evidence, and audit independence.

## Establish the contract

1. Resolve repository instructions, comparison base, exact `audit_scope`,
   exclusions, target, routing evidence, and worktree. Separately resolve exact
   `remediation_write_scope`; audit coverage never grants write authority.
2. Invocation authorizes safe local verification and remediation of validated
   findings only inside that write scope. Preserve unrelated changes.
3. It does not authorize breaking contracts, production access, exploitation or
   scanning of live/external targets, secret access, deployment, release,
   migration application, cloud/database mutation, credential rotation,
   disclosure, or scope expansion.
4. Preserve public API, client, MCP, protocol, configuration, command, event,
   model-interface, and data contracts. A finding requiring a break is blocked
   pending explicit approval and versioning, deprecation, migration,
   compatibility-window, consumer, and rollback plans.
5. Convergence means a final independent full-scope audit finds no validated,
   authorized remediable issue under its stated methods. It does not prove
   security, compliance, or certification. Unready required documentation
   evidence blocks convergence.
6. Resolve roles, overrides, independence, and actual capabilities. Record
   unavailable roles and substitutions; writers cannot perform the final audit.

Initialize and persist
[the security iteration record](references/security-iteration-record.md) before
remediation, either standalone or within the parent orchestration ledger.
Conversation state is not authoritative. Record stable finding/root-cause IDs,
predecessors, both scopes, bases, owners, contracts, files, evidence, tests,
risks, budgets, checkpoints, and resume conditions. Validate its digest chain
and compact state before resume, then reconcile the recorded revision and
evidence with the worktree.

## Iteration state machine

1. **Audit:** Invoke `$audit-system-security` read-only on the current full
   `audit_scope`. Require concrete attack paths, canonical root causes, and an
   auditor independent of implementation.
2. **Classify:** Mark findings authorized and remediable; closed, duplicate,
   invalid, or human-approved risk; or blocked by evidence, ownership,
   compatibility, authority, or scope. Risk remains proposed until a named
   accountable owner and approval reference exist. Outside-scope writes are
   blocked follow-ups.
3. **Batch:** Select the smallest coherent dependency-ordered batch, baseline its
   attack paths safely, and assign every file, contract, schema, migration,
   lockfile, and generated artifact to one writer.
4. **Remediate:** Invoke `$remediate-security-findings`. Require root-cause fixes,
   regression tests that fail without them, compatibility classification,
   broader verification, and per-finding handoff. Exclude unrelated hardening.
   Route repository delivery-security controls through
   `$implement-devsecops-controls`; hosted or external actions stay gated.
5. **Validate:** An independent `security_engineer` retraces original paths,
   attempts safe relevant bypasses, checks adjacent sinks, and reviews the diff
   for introduced defects. Inspect for mutations if tool capability is not
   enforceably read-only. Rerun behavior, regression, contract, and
   [documentation quality](../deliver-system-change/references/documentation-quality-contract.md)
   checks; missing inventory or a failed gate blocks convergence.
6. **Re-audit:** Invoke `$audit-system-security` on the updated full scope,
   prioritizing changed boundaries and unresolved paths. Compare by stable ID,
   root cause, predecessor, and base. Reusable intermediate evidence never
   narrows or replaces this independent audit.
7. **Decide:** Finish on convergence; continue after measurable risk reduction
   when authorized findings remain; otherwise checkpoint as blocked or
   non-convergent with the exact next action and resume condition.

Checkpoint after every phase. Never discard history, reset counters, silently
reclassify blocked work as fixed, or rerun reusable evidence unless its base,
scope, boundary, independence, or freshness changed.

## Evidence, budgets, and stop rules

Invoke `$verify-current-documentation` for material version-, provider-,
protocol-, Region-, partition-, model-, or configuration-sensitive claims and
validate `.codex/documentation-evidence.json`. Use proof payloads only in scoped
fixtures, harnesses, or memory. Never weaken assertions or controls, suppress
diagnostics, or redefine convergence around changed files.

Use stricter user/project limits when supplied; otherwise permit at most three
iterations, ten newly handled findings per iteration, 60 elapsed minutes, and
25 cumulative changed files. Count generated sources and outputs separately.
Use a token budget only when explicitly supplied. Checkpoint before any limit;
budget changes require an explicit contract decision. When nested, the stricter
remaining applicable parent or security-loop limit wins; entering or resuming
this loop never resets parent consumption.

Stop blocked when only blocked findings remain, authority or compatible
remediation is missing, or an independent reviewer is unavailable after a
bounded attempt. Stop non-convergent when one root cause survives two consecutive
attempts, a cycle yields no net risk reduction, or fixes repeatedly introduce
equivalent findings. Never substitute implementer self-review or claim
convergence.

## Handoff

Lead with converged, blocked, or non-convergent. Report iterations, fixed and
remaining findings, files and owners, tests, attack-path validation, recurring
or introduced findings, contract and documentation status, budgets and latest
checkpoint, recovery, residual risk, unreviewed surfaces, and every action
requiring separate authority.
