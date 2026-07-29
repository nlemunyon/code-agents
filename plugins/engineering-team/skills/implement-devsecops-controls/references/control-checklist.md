# DevSecOps control checklist

Select only surfaces present in the target repository.

## Identity and execution

- Default-deny job and token permissions; elevate per job only when required.
- Separate trusted branch, release, fork, and pull-request execution contexts.
- Prevent untrusted code, scripts, caches, artifacts, and outputs from crossing
  into jobs with secrets or write credentials.
- Pin runner images, actions, tools, and reusable workflows appropriately; record
  controlled update mechanisms.
- Bound concurrency, retries, timeouts, cancellation, and resource consumption.

## Source and supply chain

- Verify dependency lockfiles, allowed sources, update policy, and reachability
  before treating scanner output as actionable.
- Scan source, dependencies, containers, infrastructure, and secrets at the
  earliest useful boundary without duplicating noisy gates.
- Generate and retain provenance, attestations, SBOMs, signatures, hashes, and
  build metadata where the threat model requires them.
- Protect build inputs and outputs from substitution, confusion, replay, and
  cross-tenant cache or artifact poisoning.

## Delivery and policy

- Validate configuration, infrastructure, containers, migrations, and policy
  before promotion; keep destructive actions separately approval-gated.
- Make environment promotion identities, approvals, artifact identity, and
  rollback explicit. Promote the verified artifact rather than rebuilding it.
- Fail closed for required security controls while distinguishing infrastructure
  failure from a validated product finding.
- Record suppressions and exceptions with owner, scope, rationale, evidence,
  compensating controls, expiry, and independent approval.

## Evidence and operations

- List docs for public commands, config, policies, and build files.
- Link each item to its source and owner.
- Check grade 12 prose, tested use, results, and error help.
- Block when the list or check is missing or fails.
- Preserve actionable logs and receipts without secrets, tokens, sensitive
  payloads, or excessive personal data.
- Test normal, denied, partial-failure, retry, cancellation, tampered-artifact,
  stale-evidence, and rollback behavior.
- Record exact commands, versions, runner context, exit status, limitations, and
  durable evidence locations.
- Distinguish control configuration, observed enforcement, assessment evidence,
  risk acceptance, and formal compliance decisions.
