---
name: orchestrate-system-change
description: Execute an approved cross-system plan, including approved migrations and breaking migration plans, through delivery, review, and security convergence. Not for narrow edits, missing plans, migration application, production mutation, unapproved breaking changes, or external communications.
---

# Orchestrate System Change

Drive approved vertical slices to verified convergence. Child skills own their
implementation detail; this skill owns composition, authority, durable state,
gates, and stopping decisions.

## Validate the contract

1. Resolve repository instructions, approved plan, target, exclusions, routing
   evidence, and worktree state. Preserve unrelated changes.
2. Require outcome, criteria, current-state evidence, contracts and compatibility,
   ordered ownership, verification, recovery, documentation evidence and public-
   documentation gate, risks, decisions, and non-goals. Return to
   `$plan-system-change` if a gap could change implementation.
3. Block dependent work on stale, inferred, unresolved, secondary-only, expired,
   or target-mismatched required evidence. Apply
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
4. Invocation authorizes plan-scoped repository edits and safe local checks only.
   It does not authorize deployment, release, publication, migration application,
   production or cloud/database mutation, credential access, or external contact.
5. Preserve public API, client, MCP, protocol, configuration, command, event,
   model-interface, and data contracts. Stop before any unapproved break.

## Initialize durable state

Convert the plan into dependency-ordered, observable slices. Keep shared
contracts and schemas sequential; parallelize only disjoint ownership.

Create the append-only ledger specified by
[the ledger contract](references/orchestration-ledger.md), mapping criteria,
packages, paths, contracts, claims, commands, reviewers, and recovery. Persist
multi-phase or resumable runs at an approved `.codex` path; conversation state is
not authoritative. Before resume, validate the complete digest chain and
receipts, use the ledger validator's compact state, and reconcile its recorded
revision with the worktree. On drift or invalid evidence, fail closed.
The validator is
`plugins/engineering-team/scripts/validate_orchestration_ledger.py`.

Use pending, in-progress, completed, blocked, and superseded states. Only one
integration slice may be in progress, though its independent packages may run
concurrently.

## Slice state machine

For each dependency-ready slice:

1. **Deliver:** Invoke `$deliver-system-change` for the bounded slice with exact
   outcome, inputs, ownership, exclusions, dependencies, criteria, contracts,
   evidence, tests, and handoff. One writer owns each file, schema, migration,
   lockfile, generated artifact, and public contract. Route repository delivery-
   security controls through `$implement-devsecops-controls`; external actions
   remain separately gated.
2. **Integrate:** Inspect handoffs and diffs centrally, enforce ownership, and run
   focused then slice-wide verification. Reports alone are not evidence.
3. **Review:** Invoke `$review-system-change` independently on the integrated
   comparison base. Reuse a delivery review only if it is writer-independent and
   satisfies the same complete gate contract. Classify findings as blocking,
   authorized to fix, approved accepted risk, duplicate, invalid, or awaiting a
   decision. Accepted risk requires a named owner and approval receipt.
4. **Correct:** Send authorized non-security corrections through bounded
   `$deliver-system-change`; rerun affected checks and independent review.
5. **Secure:** Invoke `$secure-system-iteratively` with explicit, separate
   `audit_scope` and `remediation_write_scope`. Security work cannot expand plan
   authority or break a public contract.
6. **Recheck:** Review and verify the post-security integrated state. Route any
   regression through the same tracked correction paths.
7. **Close:** Close only with objective criterion evidence, resolved or approved
   findings, security convergence, approved contract status, viable recovery,
   and a passing documentation inventory and quality gate.

Append a ledger transition after every phase, including gate and command receipt
IDs. Never rewrite history or discard unresolved evidence.

## Budgets and stop rules

Use plan or user limits; otherwise allow per slice at most five correction or
security iterations, 25 distinct root causes, 120 elapsed minutes, and 50
cumulative unique changed files. Use a token budget only when explicitly
supplied. Counters survive renames, restarts, and resume. Checkpoint before a
limit and request direction. A child workflow may impose a lower limit; the
stricter remaining applicable parent or child limit wins, and child invocation
or resume never resets parent consumption.

Continue only after a closed slice and measurable progress. Re-sequence or split
within approved contracts; return to planning when evidence changes architecture,
scope, criteria, contracts, migration, trust boundaries, or recovery.

Stop blocked when evidence, ownership, approval, authority, dependency, or an
independent reviewer is unavailable. Stop non-convergent when the same root cause
survives two correction cycles, a cycle makes no measurable progress, equivalent
findings recur, or plan premises conflict with implementation. Persist the next
action and exact resume condition; never substitute self-review.

## Final convergence and handoff

Run the whole-plan verification matrix, independent `$review-system-change`, and
full authorized-scope `$secure-system-iteratively`; after remediation, rerun
whole-plan review and tests. Fresh matching child gates may be referenced by ID,
but never replace final whole-plan review and security gates.

Converge only when all criteria and packages complete, required evidence and
documentation gates pass, no blocking independent finding remains, security
converges, contracts are approved, and rollout, rollback, and recovery match the
result.

Lead the handoff with completed, blocked, or non-convergent. Report plan identity,
slice state, behavior, ownership, contracts, artifacts, iterations, findings,
tests, evidence expiry, budgets and checkpoint, recovery, residual and unreviewed
risk, plus actions needing separate authority. Do not deploy or communicate
externally.
