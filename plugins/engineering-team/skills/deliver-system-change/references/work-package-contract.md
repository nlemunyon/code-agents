# Work package contract

Give every implementation agent a bounded assignment with these fields.

## Required fields

- **Outcome:** one observable result the package must produce.
- **Inputs:** approved contract, decisions, dependencies, and evidence.
- **Ownership:** exact files, modules, migration, schema, or generated artifacts
  the agent may edit.
- **Exclusions:** adjacent work the agent must not absorb.
- **Dependencies:** packages that must finish first and handoffs it must consume.
- **Acceptance:** behavior and failure cases the implementation must satisfy.
- **Public contract impact:** none, additive, deprecated-but-compatible, or
  breaking; include the approval reference and migration plan for any break.
- **Documentation claims:** required ledger claim IDs and their current status.
- **Public docs:** list the docs in scope, their owner, examples, results, error
  help, and test proof. Follow
  [the documentation quality contract](documentation-quality-contract.md).
- **Verification:** commands or tests the agent must run.
- **Handoff:** diff summary, commands and results, assumptions, risks, and follow-up.

## Coordination rules

- Assign one writer per file and one owner per shared contract or migration.
- Keep discovery agents read-only.
- Finish and integrate contract or schema decisions before adapter work begins.
- Do not allow client, MCP, or API agents to create competing schema definitions.
- Let the data engineer own database migrations and data workflows; other agents
  consume the agreed persistence contract.
- Let the AI/ML engineer own model behavior, evaluation criteria, retrieval
  semantics, inference integration, and MCP protocol or adapter contracts. Let
  the data engineer own persistence, ingestion execution, pipeline operations,
  lineage, and migrations. Establish shared data contracts first and assign one
  owner to each contract and artifact.
- Let the GovCloud engineer own infrastructure-as-code changes and partition
  review; application agents provide runtime requirements.
- Keep the security engineer independent and read-only. Implementation owners
  apply verified remediations; the security engineer validates the result.
- Let the technical writer own standalone documentation files. When comments or
  docstrings share an implementation-owned source file, transfer file ownership
  or have the implementation owner apply the reviewed wording.
- Keep documented paths project-relative or use `$HOME`, `<repo-root>`,
  `%USERPROFILE%`, or `$env:USERPROFILE`; reject user-specific absolute home
  paths copied from a developer machine or tool output.
- Integrate and test after each dependency phase instead of waiting for one large
  merge at the end.
- Stop and return to the parent when evidence contradicts the approved contract,
  required ownership overlaps, or a task needs new external authority.
- Stop before any unapproved breaking change to an API, SDK, MCP surface,
  protocol, configuration, command, event, or externally consumed schema.
- Stop when a required documentation claim is missing, stale, inferred,
  unresolved, secondary-only, or mismatched to the actual target.
- Stop when public docs or their check fail.

## Example

```text
Outcome: Add typed client support for the approved job-status endpoint.
Inputs: Contract fixture v2 and API error table from the contract phase.
Ownership: src/client/jobs.py, tests/client/test_jobs.py.
Exclusions: Server routes, MCP tools, generated schemas, packaging metadata.
Dependencies: API contract tests are merged and passing.
Acceptance: Typed success result; documented not-found and unauthorized errors;
            existing client imports remain compatible.
Public contract impact: Additive; existing imports and signatures are unchanged.
Verification: Run the focused client tests and configured type checker.
Handoff: Changed public surface, commands/results, compatibility impact, risks.
```
