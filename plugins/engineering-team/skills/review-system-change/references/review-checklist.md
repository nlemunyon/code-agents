# Cross-system review checklist

Always apply this core to the changed path. Then read only the linked domain
checklists for changed boundaries. Record selected and excluded domains with
diff or repository evidence.

## Correctness and contracts

- Map acceptance criteria to executable behavior and tests.
- Compare server, client, MCP, database, generated schemas, validation, errors,
  defaults, retries, and timeouts end to end.
- Baseline public APIs, Python imports, MCP surfaces, protocols, configuration,
  commands, events, and consumed schemas. Reject unapproved breaking changes.
- Verify mixed-version rollout, rollback, authorization, tenancy, concurrency,
  and failure behavior.

## Security and evidence

- Trace affected assets, actors, trust boundaries, inputs, privileges, sensitive
  data, threats, and plausible abuse cases.
- Check authorization at the owning boundary and protect secrets from output,
  logs, fixtures, telemetry, and external services.
- Validate required external claims against target-matched primary sources and
  block stale, inferred, unresolved, secondary-only, or mismatched evidence.
- Distinguish guidance, controls, evidence, assessment, risk acceptance, and
  formal compliance or certification.

## Verification quality

- Tests fail without the intended behavior and cover relevant invalid,
  unauthorized, retry, concurrency, migration, and rollback paths.
- Mocks do not hide the boundary they claim to verify.
- Manual evidence records exact commands, inputs, versions, and results.
- Report skipped or unavailable checks as residual risk.

## Domain routing

- API, client, MCP, UI/UX, protocols: [interfaces and experience](interfaces-and-experience.md)
- Database, migrations, workflows: [data and recovery](data-and-recovery.md)
- Containers, infrastructure, CI/CD: [runtime and delivery](runtime-and-delivery.md)
- Public docs and developer experience: [documentation](documentation.md)
- GovCloud and standards: [regulated environments](regulated-environments.md)
