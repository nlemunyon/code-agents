# Engineering Team Developer Reference

This guide covers the public developer surfaces in the Engineering Team
plugin. The root `README.md` covers setup and common workflows.

## Public interface rules

Treat skill names, role names, script commands, plugin metadata, and the
documentation evidence schema as stable public interfaces. Prefer additive
changes. Follow the compatibility rules in the root `AGENTS.md`.

Write user and developer docs, code comments, and docstrings at U.S. grade 12
or below. This limit does not apply to agent prompts or skill instructions.
Code, URLs, public names, and schema literals do not count toward the score.
The prose that explains them still counts.

Each public interface needs:

- A short purpose statement.
- Inputs and limits.
- A working usage example.
- The expected return value or output.
- Caller-facing errors, what they mean, and how to recover.

State why a return value or error does not apply. Do not leave the section
blank.

## Skills

Invoke a skill by naming it in a request, such as:

```text
Use $plan-system-change to plan an additive API change.
```

The expected result is the report or repository change described by the
skill. A skill stops and reports a blocker when required evidence, approval,
or ownership is missing. Skill failures do not grant permission to deploy,
publish, release, migrate data, or change an external system.

| Skill | Expected result |
| --- | --- |
| `$audit-system-security` | A read-only security audit with proof. |
| `$bootstrap-project-context` | Up-to-date project and Codex files. |
| `$deliver-system-change` | The approved plan, built and tested. |
| `$diagnose-system-failure` | Proof of what caused the fault. |
| `$implement-devsecops-controls` | Safer build and delivery checks. |
| `$install-global-agents` | A safe agent setup or status report. |
| `$orchestrate-system-change` | A set loop for build, review, and fixes. |
| `$plan-system-change` | A work plan based on facts. |
| `$remediate-security-findings` | Tested fixes for chosen security flaws. |
| `$review-system-change` | A separate review of the change. |
| `$secure-system-iteratively` | A set loop for audits and fixes. |
| `$verify-current-documentation` | Proof from current docs for the target. |

Each skill has its full input rules, failure conditions, and output format in
`plugins/engineering-team/skills/<skill-name>/SKILL.md`.

## Agent roles

Roles are installed as Codex custom agents. Their input is a bounded assignment
from the parent agent. They return evidence, changed files when they have write
authority, test results, risks, and unresolved questions.

| Role | Public responsibility |
| --- | --- |
| `ai_ml_engineer` | AI, ML, and MCP work. |
| `api_engineer` | API rules, access, and tests. |
| `client_engineer` | Public Python clients and packages. |
| `data_engineer` | Data plans, moves, checks, and repair. |
| `devsecops_engineer` | Safe build and delivery tools. |
| `docs_researcher` | Read-only checks of primary sources. |
| `govcloud_engineer` | AWS GovCloud plans and run work. |
| `quality_engineer` | A separate check of code and tests. |
| `security_engineer` | A read-only security check. |
| `system_architect` | Read-only system plans and tradeoffs. |
| `technical_writer` | User, developer, API, and code docs. |
| `ui_engineer` | Usable and open user screens. |
| `ux_engineer` | Read-only checks of user flows and access. |

Bad or shared tasks go back to the parent for a fix. A task does not let a role
ship a release, deploy, move data, or send a message.

## Script commands

Run commands from the repository root. All validators write a success summary
to standard output and diagnostics to standard error.

### Manage global agents

```bash
python3 plugins/engineering-team/scripts/manage_global_agents.py status
python3 plugins/engineering-team/scripts/manage_global_agents.py install --dry-run
python3 plugins/engineering-team/scripts/manage_global_agents.py uninstall --dry-run
```

The command returns exit code `0` after a successful status check, dry run, or
change. It reports installed, planned, preserved, or blocked files. Invalid
configuration and unsafe collisions return a nonzero code with a recovery
message. Install and uninstall refuse unsafe replacement unless the user
reviews the conflict and explicitly uses the supported force option.

### Validate agent templates

```bash
python3 plugins/engineering-team/scripts/validate_agent_templates.py
```

Success returns `0` and the number of valid agents. Invalid TOML, missing
fields, bad role names, unsafe sandbox settings, or missing policy markers
return `1` with the file and reason.

### Validate documentation evidence

```bash
python3 plugins/engineering-team/scripts/validate_documentation_evidence.py \
  .codex/documentation-evidence.json
```

Success returns `0` with the claim and warning counts. Invalid JSON, expired
required claims, missing target evidence, or mismatched sources return `1`.
Use `--as-of YYYY-MM-DD` for a repeatable validation date. Use `--allow-empty`
only while a project evidence ledger is being created.

### Validate documentation quality

```bash
python3 plugins/engineering-team/scripts/validate_documentation_quality.py \
  --changed-from HEAD README.md plugins/engineering-team/DEVELOPER.md \
  plugins/engineering-team/scripts \
  --inventory plugins/engineering-team/public-documentation.json
```

Success returns `0` and a short report. Hard prose or missing interface docs
return `1` and explain what to fix. Bad input, options, or JSON return `2`.
The command help lists its inventory and baseline options.

### Validate portable documentation

```bash
python3 plugins/engineering-team/scripts/validate_portable_documentation.py .
```

Success returns `0` and the number of checked files. A user-specific home path,
missing input path, or unreadable documentation returns `1` with its location
and a portable replacement.

### Validate prompt budgets

```bash
python3 plugins/engineering-team/scripts/validate_prompt_budgets.py
```

Success returns `0` and reports prompt size by loading group and scenario. A
budget increase returns `1` and names the group that grew. Bad JSON, an unknown
content rule, or an unreadable source returns `2`. Add `--show-duplicates` to
list prose blocks that occur in three or more active prompt files. The budget
file keeps the pre-change measure and the lower ratchet used for later changes.

### Validate an orchestration ledger

```bash
python3 plugins/engineering-team/scripts/validate_orchestration_ledger.py \
  .codex/orchestration-ledger.jsonl
```

Success returns `0` and compact JSON with the current state, open blockers,
budget use, and latest digest. An invalid or changed chain returns `1` and
names the bad record. Use `--pretty` for indented output.

### Validate release identity

```bash
python3 plugins/engineering-team/scripts/validate_release_identity.py \
  --base-ref HEAD
```

Success returns `0` when the plugin payload is unchanged or its version has
advanced. A changed payload with the old version returns `1`. Git or manifest
read errors return `2`.

### Validate workflow references

```bash
python3 plugins/engineering-team/scripts/validate_workflow_references.py
```

Success returns `0` with skill and role counts. Unknown skill or role names,
bad skill metadata, or missing default prompts return `1` with the location.

## Plugin and marketplace metadata

The plugin contract is in
`plugins/engineering-team/.codex-plugin/plugin.json`. The repository
marketplace entry is in `.agents/plugins/marketplace.json`.

The plugin manifest returns metadata to Codex rather than a runtime value.
Invalid JSON, a mismatched plugin name or source path, and a payload change
without a version change are validation errors. Fix the source metadata or
advance the version before handoff.

## Documentation evidence schema

Projects that depend on changing external behavior use
`.codex/documentation-evidence.json`. Start from
`plugins/engineering-team/skills/verify-current-documentation/assets/documentation-evidence.json`.

The validator expects schema version `1`, a date, a scope, and a claim list.
Each required claim needs project proof and the exact target. It also needs a
primary source, source dates, a decision, and verified confidence.

Validation returns a claim count and warnings. Missing, stale, inferred,
unresolved, secondary-only, or target-mismatched required claims fail. The
validator explains the field that needs repair.

## Verification

Run the full source checks listed in the root `README.md`. Safe examples in
this guide are the same commands used by the repository verification suite.
