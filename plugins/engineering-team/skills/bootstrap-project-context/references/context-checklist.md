# Project context checklist

Capture evidence for the following areas. Omit irrelevant sections rather than
filling them with generic advice.

## Repository and ownership

- Repository root, nested instruction files, and generated-code boundaries
- Major packages or services and the team or role that owns each
- Public interfaces and compatibility promises
- Baselines and tests for API schemas, public Python imports and signatures, MCP
  surfaces, protocols, configuration, commands, events, and externally consumed
  data schemas
- User README, developer docs, API references, examples, generated docs, and
  documentation ownership
- Sensitive directories, data, credentials, and prohibited operations
- Security boundary, data classification, threat model, and applicable standards
  or contractual control baselines

## Agent selection evidence

- Detected task signals and boundaries: architecture, API, client, AI/ML, MCP,
  UI, UX, accessibility, data, infrastructure, security, documentation, quality,
  and version-sensitive external research
- Primary implementation role for each owned path, public contract, migration,
  schema, generated artifact, and documentation surface
- Read-only analysis and independent-review roles required for each boundary
- Commands and evidence each role must return before its work is accepted
- Roles unavailable globally, unnecessary for this project, or requiring a
  project-specific override, with the evidence and reason
- Ownership conflicts and sequencing constraints that prevent concurrent edits

## Architecture and execution

- Process entry points and request or event flows
- API, client library, protocol, database, worker, and infrastructure boundaries
- Shared schemas, code generation, and dependency direction
- Runtime configuration and secret injection
- Container build, local orchestration, health checks, and startup ordering
- Installed and target versions for external libraries, frameworks, providers,
  protocols, services, standards, Regions, partitions, and feature flags
- Canonical primary documentation, release notes, specifications, and authorized
  private documentation sources

## Developer workflow

- Supported language and tool versions
- Bootstrap, build, format, lint, type-check, unit-test, integration-test, and
  end-to-end commands
- How to run one test, one package, and the full suite
- Documentation build, link, spelling, example, and generated-reference checks
- List of public docs, their owners, and source links
- Docs check for grade 12 prose, tested use, results, and error help
- A block when the list or check is missing or fails
- Portable path convention: project-relative paths, `$HOME`, `<repo-root>`, or
  the appropriate Windows home variable; no user-specific absolute home paths
- Documentation evidence ledger location, validation command, ownership, and
  freshness expectations; if the installed validator path is unknown, record
  that unresolved rather than documenting a placeholder command
- Required local services and deterministic fixtures
- CI jobs that define acceptance

## Database and data workflows

- Database engine, ORM or query layer, migration framework, and test database
- Transaction boundaries, constraints, indexes, retention, and backup assumptions
- Batch or streaming workflows, schedules, retries, checkpoints, lineage,
  reconciliation, and data-quality checks
- Rules for creating, applying, rolling back, and validating migrations

## Delivery and operations

- Image registry and runtime platform
- Environment promotion and configuration differences
- Observability, alerting, audit, backup, restore, and incident commands
- Deployment, migration, release, and rollback operations that require explicit
  authorization
- Cloud partition, account, Region, compliance, and network boundaries
- Security evidence, vulnerability handling, incident response, and the human
  owners authorized to accept risk or make compliance claims

## Durable output

Put verified, stable instructions and the project-specific agent-routing matrix
in `AGENTS.md`. Put Codex settings and custom agent definitions in `.codex/`.
Put detailed domain or workflow knowledge in project-scoped skills. Do not
duplicate reusable role definitions or large documentation that already has a
clear canonical location; link to it and explain when to read it. Keep paths
portable and do not copy user-specific absolute paths from tool output.
