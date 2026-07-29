# System boundary checklist

Always apply the core below. Then read only the linked domain checklists whose
boundaries are present. Record each selected or excluded domain with repository
evidence so progressive disclosure cannot hide a consumer.

## Behavior and contract

- Actor, entry point, observable outcome, acceptance criteria, and non-goals
- Input, output, validation, errors, authorization, idempotency, and concurrency
- Compatibility, deprecation, versioning, and mixed-version operation
- Ownership of the canonical schema and any generated artifacts
- Baseline or snapshot of every affected public operation, import, signature,
  tool, resource, prompt, command, configuration key, event, and schema
- Change classification: none, additive, deprecated-but-compatible, or breaking
- For a proposed break: necessity evidence, compatible alternatives rejected,
  explicit approval, affected consumers, migration, compatibility window, and
  rollback

## Security and assurance

- Assets, actors, trust boundaries, data classification, threats, and abuse cases
- Authentication, authorization, tenancy, secrets, cryptography, and auditability
- Input, output, injection, deserialization, file, path, command, and network risk
- Dependency provenance, build integrity, sensitive-data handling, recovery, and
  accountable risk ownership
- Applicable standards and exact control identifiers without equating engineering
  review with formal compliance or certification

## External documentation evidence

- Repository or user evidence for the exact installed or targeted version
- Primary source authority and exact version, Region, partition, or edition match
- Release notes or migration guidance for behavior changes near the target
- Retrieval and validity dates appropriate to source volatility
- Required claim IDs linked to dependent work packages
- Inferred, unresolved, conflicting, stale, and secondary-only claims kept out of
  implementation premises

## Verification and delivery

- Contract, schema, import, or snapshot tests that fail on unapproved public
  surface changes
- Tests tied to every acceptance criterion and failure mode
- Telemetry proving successful rollout and detecting partial failure
- Ordered deployment and migration steps, feature flags, and compatibility window
- Rollback versus forward-recovery decision and data consequences
- Explicit actions requiring human, compliance, security, or production approval

## Domain routing

- Database, migrations, backfills, and workflows:
  [data lifecycle](data-lifecycle.md)
- API, Python client, MCP, protocols, and adapters:
  [interfaces and adapters](interfaces-and-adapters.md)
- Containers, runtime, infrastructure, CI/CD, and operations:
  [runtime and delivery](runtime-and-delivery.md)
- Public documentation and developer experience:
  [documentation](documentation.md)
- AWS GovCloud, standards mappings, and assurance detail:
  [regulated environments](regulated-environments.md)
