# Security remediation checklist

Use only the sections relevant to the validated root cause.

## Fix design

- Remove or constrain the dangerous capability at a trusted boundary instead of
  matching known payloads, hiding errors, or suppressing diagnostics.
- Preserve secure defaults when callers omit configuration or use older clients.
- Apply authorization to the requested object, tenant, action, and current
  principal; do not rely only on UI visibility or caller-supplied ownership.
- Use structured APIs for queries, commands, paths, templates, serialization,
  redirects, and network destinations. Keep canonicalization and validation in
  the same trust domain as the sensitive operation.
- Bound input size, recursion, time, concurrency, memory, retries, external
  calls, model inference, and tool execution where exhaustion is part of the
  attack path.

## API, MCP, and AI/ML

- Keep API and MCP operations narrow, authorize consequential actions, validate
  tool schemas, constrain returned data, and preserve cancellation and timeout
  behavior.
- Treat retrieved content, prompts, model output, tool output, uploaded data,
  and model artifacts as untrusted at every execution boundary.
- Prevent prompt or tool injection from granting new capabilities; enforce
  policy outside model-generated text.
- Preserve model-interface and evaluation contracts, test privacy and cross-user
  isolation, and verify provider data-handling assumptions from current primary
  documentation.

## Data, secrets, and cryptography

- Minimize sensitive data and remove it from logs, exceptions, fixtures,
  telemetry, caches, prompts, and generated artifacts.
- Use least-privilege database roles, parameterized operations, explicit tenant
  boundaries, safe migration ordering, and tested recovery.
- Never place real credentials in tests. Treat real secret rotation or revocation
  as a separate externally consequential action requiring explicit authority.
- Use supported cryptographic libraries and key-management mechanisms; include
  data migration and mixed-version behavior when changing stored formats.

## Dependencies and supply chain

- Confirm the vulnerable feature is reachable and select the narrowest supported
  fixed version compatible with the project target.
- Update manifests and lockfiles through the project tool; inspect transitive
  changes, lifecycle scripts, provenance, checksums, licenses, and runtime impact.
- Do not claim a version bump fixes the finding until the resolved dependency
  graph and original attack path are verified.
- Preserve reproducible builds and least-privilege CI/CD permissions.

## Verification and rollout

- Inventory each affected public surface and link its source, docs, owner,
  example, expected result, error guidance, and verification.
- Require authored prose at U.S. grade 12 or lower, verified usage, expected
  returns or outputs, and caller-facing error meaning and recovery. Require an
  explicit `Not applicable` reason when needed.
- Fail closed when the documentation inventory or quality check is missing or
  fails.
- Make the original safe proof fail before the fix and pass after it, or explain
  why a deterministic baseline is unsafe or impractical.
- Test normal behavior plus bypass variants, alternate encodings, malformed
  input, unauthorized principals, concurrency, failure, and rollback paths that
  are relevant to the root cause.
- Confirm tests exercise the real security boundary rather than a mock that
  bypasses it.
- Document configuration changes, deployment order, compatibility windows,
  monitoring, rollback or forward recovery, and any action needing separate
  user authorization.
- Report residual exposure and compensating controls without claiming the system
  is secure or compliant.
