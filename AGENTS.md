# Repository Guidelines

## Purpose

Maintain a reusable, project-neutral Codex engineering team. Keep proprietary
project facts, credentials, internal endpoints, schemas, and organization policy
out of this repository. Put those details in the target project's `AGENTS.md`,
`.codex/`, or project-scoped skill references.

## Structure

- `.agents/plugins/marketplace.json`: repo marketplace for installing the
  toolkit through Codex.
- `plugins/engineering-team/skills/`: one focused workflow per skill.
- `plugins/engineering-team/templates/custom-agents/`: narrow specialist roles.
- `plugins/engineering-team/templates/project/`: files used to bootstrap a repo.
- `plugins/engineering-team/scripts/`: deterministic validators and installers.
- `plugins/engineering-team/tests/`: isolated tests for user-level installers.

## Authoring rules

- Keep skill `SKILL.md` files concise and imperative.
- Put detailed checklists in a skill's `references/` directory.
- Make custom agents narrow, opinionated, and explicit about edit authority.
- Prefer inherited model settings so the toolkit ages gracefully.
- Require current primary documentation for versioned platforms such as AWS.
- Cite exact versions and control identifiers when mapping security standards.
- Keep documentation portable. Use repository-relative paths, `$HOME`,
  `<repo-root>`, `%USERPROFILE%`, or `$env:USERPROFILE`; never copy a
  user-specific absolute home path from local tool output into documentation,
  examples, docstrings, or comments.
- Keep user and developer docs, code comments, and docstrings at U.S. grade 12
  or below. This limit does not apply to LLM prompts, agent instructions, or
  skill control files. Do not score code, URLs, public names, schemas, or text
  made by a tool. Do score the prose that explains them.
- Add developer docs for each public surface. This includes libraries, imports,
  APIs, MCP tools, commands, config, events, and schemas. Add a tested example,
  the result, and user errors with their meaning and fix. If a result or error
  does not apply, state why.
- Treat public contracts as stable by default: API operations and schemas,
  public Python imports and signatures, MCP tools and resources, protocols,
  configuration, commands, events, and externally consumed data schemas.
  Prefer additive backward compatibility. Do not implement a breaking change
  without proving that no compatible alternative works, obtaining explicit
  user approval, and documenting versioning, deprecation, migration,
  compatibility-window, and rollback plans.
- Distinguish security guidance, control implementation, assessment evidence,
  and formal compliance or certification; never treat them as interchangeable.
- Never let multiple agents edit the same file, schema migration, public
  contract, or generated artifact concurrently.
- Do not authorize deployments, cloud mutations, database migrations, releases,
  or external messages merely because a workflow delegates work.
- Keep the marketplace plugin name aligned with the plugin directory and
  manifest, and keep its local source path at `./plugins/engineering-team`.
- Keep user-level installation conservative: preserve unrelated Codex config,
  reject role-name collisions, back up mutations, detect local edits, and
  require explicit approval before forcing replacement or removal.

## Documentation evidence policy

For every material external claim whose behavior may vary by version, date,
Region, partition, service availability, or configuration:

1. Determine the installed or explicitly targeted version from repository or
   user evidence before researching.
2. Verify the claim with current primary documentation matching that target.
3. Record the source, version, retrieval and expiry dates, supporting section,
   evidence, decision, and confidence in the documentation evidence ledger.
4. Treat training knowledge and secondary sources as discovery aids, not proof.
5. Do not mark a required claim ready or implement against it while it is stale,
   inferred, unresolved, or documented only for a different version or Region.

## Verification

Check the marketplace JSON and source path. Run the agent, path, and docs
checks. Check each skill with `quick_validate.py`. Check the plugin manifest
before handoff.
Run the global-agent manager tests in an isolated temporary Codex home.
Forward-test orchestration skills on an isolated fixture before trusting them
on a work repository.
