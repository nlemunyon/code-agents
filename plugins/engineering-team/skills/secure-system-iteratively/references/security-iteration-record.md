# Security iteration record

An audit-only run may return this record in its handoff. Before any remediation
or multi-iteration run, persist the authoritative record at a project-approved
path, defaulting to `.codex/security/<run-id>.jsonl`, or append compatible
records to the parent orchestration ledger. If repository instructions prohibit
persistence, stop before mutation and request an approved durable location. A
response or agent transcript may summarize a mutating run but is never its
authoritative state. Preserve prior entries and append transitions instead of
rewriting history.

For standalone persisted records, use the orchestration ledger's canonical JSON,
sequence, prior-digest, self-digest, receipt, resume, and integrity rules. A
local unkeyed digest chain detects accidental corruption, not malicious rewriting;
use and verify a separately controlled anchor when the project provides one.
On resume, verify the complete digest chain, budgets, current tree identity, and
referenced gate evidence before continuing. Missing or altered evidence blocks
convergence.

## Run contract

- run ID and status: active, converged, blocked, or non-convergent;
- comparison base and current tree identity;
- `audit_scope`, exclusions, and affected trust boundaries;
- `remediation_write_scope`, excluded writes, and authorized verification;
- applicable `AGENTS.md` files and the project agent-routing matrix;
- resolved roles, project overrides, availability, independence, assigned
  surfaces, and actual read/write capability limitations;
- external-action and public-contract authority limits;
- budgets, consumption, checkpoint, and resume condition.

Unless the user or project sets stricter limits, use at most three iterations,
ten newly handled findings per iteration, 60 minutes elapsed execution, and 25
cumulative files changed. Count a generated source and its generated output as
separate files. Use a token budget only when the user explicitly supplies one.
Checkpoint after each audit, classification, remediation batch, validation, and
re-audit. Stop before exceeding any limit; preserve the record as `blocked` with
the next dependency-ready action and the evidence or authority needed to resume.
Changing a budget is an explicit run-contract decision, not silent scope drift.
When this record is nested in an orchestration run, compare both records before
each phase: the stricter remaining applicable limit wins, and child creation or
resume never resets parent consumption.

## Finding record

Give every candidate a stable run-independent ID such as `SEC-<root-hash>` and
never reuse it for another root cause. Record:

- canonical root-cause key: normalized vulnerable boundary or invariant,
  dangerous operation, and missing or failed control;
- title, severity, confidence, status, and exact locations;
- source-to-sink path, preconditions, affected assets, impact, and evidence;
- first-seen and last-tested comparison bases;
- predecessor IDs and relationship: duplicate-of, supersedes, regression-of,
  introduced-by-fix-for, or split-from;
- disposition owner, writer ownership, changed files, tests, contract impact,
  documentation evidence, affected public-documentation inventory, grade-level
  status, usage/result/error coverage, residual risk, and blocker or resume
  condition. Missing inventory or documentation-quality checks fail closed.

Keep the stable ID when locations, severity, or evidence change without changing
the root cause. Create a new ID and predecessor relationship when the root cause
materially changes. Deduplicate on the canonical key, not title or location.

Statuses are `candidate`, `validated`, `authorized`, `fixed-pending-validation`,
`closed`, `invalid`, `duplicate`, `blocked`, or `risk-acceptance-proposed`.
Risk acceptance remains proposed until an accountable human decision owner and
an approval reference are recorded. Only then record `risk-accepted`, including
scope, rationale, expiry or review date, and compensating controls. Absence of a
reply or an agent recommendation is never approval.

## Gate evidence

When a review or orchestration gate exists, link its
[gate record](../../review-system-change/references/gate-record.md). Reuse
evidence only when it
is current, reproducible, independent of every relevant writer, covers the same
comparison base, scope, acceptance criteria, and security boundary, and records
the required commands and results. Mark reused evidence and its source. Reuse
may satisfy an intermediate gate; it never narrows or replaces the final
independent full-scope audit.
