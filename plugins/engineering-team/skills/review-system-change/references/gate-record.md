# Review and security gate record

Use this schema for review and security gates. Store it in the orchestration
ledger or another project-approved durable `.codex` artifact. Missing required
fields fail the gate closed.

## Identity and coverage

- `schema_version`, `gate_id`, `gate_kind`, `created_at`;
- immutable `comparison_base` and `result_revision` identifiers;
- exact `scope` and `exclusions`;
- stable acceptance `criteria_ids` and the method used for each;
- reviewer `identity`, `role`, and `independence` evidence identifying all
  implementation owners and conflicts checked;
- `methods`, `limitations`, and `unreviewed_surfaces`.

The reviewer must be independent of writers for the reviewed scope. A missing
reviewer, bare role name without identity, or unsubstantiated independence claim
fails the gate.

## Findings and dispositions

Each finding contains a stable `finding_id`, canonical `root_key`, predecessor
IDs and relationships, title, severity, locations, concrete failure or attack
path, evidence, impact, and one disposition: `fixed`,
`blocking`, `accepted_risk`, `duplicate`, or `invalid`. A duplicate references
the canonical root key. Fixed findings reference the result revision and
verification receipts.

`accepted_risk` additionally requires rationale, residual impact, expiry or
review condition, named `risk_acceptor`, and an `approval_receipt` proving that
the acceptor has authority for this scope. Reviewer recommendation, implementer
consent, silence, or plan approval without named risk authority is insufficient.

The approval receipt records a stable receipt ID, trusted source or immutable
human-interaction record, approver identity, independently verified authority,
decision, exact finding and scope IDs, timestamp, content digest, and readback
verification evidence. Bind the digest to all of those fields. The implementer
and reviewer must not author the receipt. Missing, mutable, self-authored,
identity-mismatched, scope-mismatched, or digest-invalid approval evidence fails
closed; field presence alone is never proof of authorization.

## Verification receipts

Each receipt records `receipt_id`, exact `command`, `working_directory`,
`started_at`, `finished_at`, integer `exit_code`, `evidence` or a durable
`evidence_path`, and `evidence_sha256`. Recompute the digest and require the
expected exit status. Record skipped or unavailable checks as limitations, not
passing receipts. Missing, forged, stale, or target-mismatched receipts fail the
criterion they support.

## Result, freshness, and reuse

Record `result` as `pass`, `fail`, or `blocked`, the criteria-to-receipt mapping,
open blockers, contract compatibility, and residual risk. Also record
the affected public-documentation inventory, grade-level result, verified usage,
expected-result coverage, caller-facing error meaning and recovery coverage, and
explicit `Not applicable` reasons. Missing inventory or checks fail closed.
`valid_until` or an explicit freshness condition plus invalidation triggers,
including result-revision change, scope or criteria change, relevant file
change, expired documentation evidence, new finding evidence, reviewer conflict,
and failed rerun.

A parent may reference a child gate by `gate_id` only when comparison base,
result revision, scope, criteria, independence, receipts, and freshness still
match. Reuse prevents duplicate work; it does not waive the final whole-plan
review or full-scope security gate.
