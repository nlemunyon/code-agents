# Orchestration ledger contract

For multi-phase or resumable work, persist the authoritative ledger at the
project-approved `.codex` path (default `.codex/orchestration/<run-id>.jsonl`).
Confirm that the path is allowed by repository instructions before writing it.
A response, agent transcript, task list, or in-memory context may summarize the
ledger but must never be its authoritative state. If persistence is prohibited,
stop before implementation and request an approved durable location.

## Header

The first JSON Lines record is immutable and has `record_type: "run"`,
`prior_digest: "GENESIS"`, and its computed `digest`. Record:

- schema version, stable run and plan IDs, creation time, repository identity,
  plan source and approval evidence;
- outcome, scope, exclusions, target, applicable instruction sources, and the
  project routing evidence consumed;
- acceptance criteria, work graph, public contracts, documentation claim IDs,
  affected public-documentation inventory and quality-gate command,
  rollout, migration, recovery, risks, assumptions, decisions, and non-goals;
- separately authorized `audit_scope` and `remediation_write_scope`;
- configured `max_iterations`, `max_distinct_findings`,
  `max_elapsed_minutes`, and `max_cumulative_changed_files`, any explicit user-
  supplied token budget, plus the user-checkpoint rule. Unless the approved plan
  or user sets stricter values, record defaults of five correction/security
  iterations per slice, 25 distinct findings, 120 elapsed minutes, and 50
  cumulative changed files. Never infer a token budget.

Reject an incomplete plan before creating an execution transition. In
particular, every criterion needs a stable ID and verification method, and every
work package needs a stable ID, dependencies, owner, owned paths, exclusions,
and criteria.

## Append-only transitions

Compute every digest as SHA-256 over the UTF-8 encoding of the record with the
`digest` field omitted, object keys sorted lexicographically, no insignificant
whitespace, and JSON separators `,` and `:`. Arrays retain their recorded order.
Reject duplicate keys, non-UTF-8 input, malformed JSON, an incomplete final
line, unknown fields where the schema forbids them, a missing header digest, or
a chain whose first `prior_digest` is not the literal `GENESIS`.

Append one immutable `record_type: "transition"` record after every state change.
Never edit, remove, reorder, or replace earlier records. Each transition records:

- monotonically increasing sequence, timestamp, prior-record digest, and its own
  digest over canonical record content. Treat this local, unkeyed chain only as
  accidental-corruption and incomplete-write detection, not as proof against an
  actor who can rewrite the project;
- slice, work-package, phase, prior status, next status, actor, ownership scope,
  comparison base, and result revision;
- criterion evidence, changed files, contract status, findings and dispositions,
  gate-record IDs, command-receipt IDs, documentation evidence, public-doc
  coverage and grade-level status, residual risk,
  and the reason for continuing, closing, blocking, checkpointing, or replanning.

Use stable root-cause finding keys across iterations. A renamed or rediscovered
finding with the same root cause does not consume another distinct-finding slot.
Count the union of files changed during the entire run, not files in only the
latest iteration. Before exceeding any configured budget, append a `checkpoint`
transition and obtain explicit user direction. Never reset counters on resume.

## Evidence records

Append gate records conforming to
`../../review-system-change/references/gate-record.md`. A referenced command
receipt is valid only when it contains the exact command and working directory,
start and finish times, exit code, captured evidence or durable evidence path,
and a digest of that evidence. Recompute digests before consuming a receipt.
Treat missing, malformed, stale, target-mismatched, or digest-mismatched receipts
as failed evidence; an agent assertion or successful-looking prose cannot
replace them.

Accepted risk requires an explicit disposition, rationale, expiry or review
condition, and a validated approval receipt from the plan's named risk acceptor
whose authority covers the affected scope. Validate that receipt against a
separately controlled human-interaction or trusted-system record as defined by
the gate schema. Implementers and reviewers cannot author approval receipts or
self-authorize accepted risk.

## Resume and recovery

On start or resume, locate the ledger from project instructions or the user,
read it from the header through the last complete line, verify the digest chain,
recompute budgets and current state, validate referenced gate and command
receipts, then compare the recorded result revision with the worktree. Stop on a
gap, mutation, unknown record, missing artifact, or unexplained revision drift.
Resume only from the last verified transition; conversational context is not
recovery evidence.

Where the project provides a separately controlled signing or evidence store,
checkpoint the ledger's latest digest there and bind it to the repository and
tree identity. Verify that anchor on resume. Without such an anchor, explicitly
record that malicious ledger rewriting is outside the integrity guarantee.

## Completion

Child or composite workflows may reuse a gate only when its record covers the
same comparison base, result revision, scope, criteria, independence, and
freshness requirements. Reference the existing gate ID instead of duplicating
it. Slice gates never replace the final independent whole-plan review and
full-scope security gates.

Append `record_type: "final"` only after every criterion and work package is
complete, all required receipts validate, independent review has no unresolved
blocker, full-scope security has converged, contracts have approved status, the
public-documentation inventory proves verified usage, expected results, and
caller-facing error meaning and recovery in grade-12-or-lower authored prose, and
rollout, rollback, recovery, limitations, and residual risks are recorded.
