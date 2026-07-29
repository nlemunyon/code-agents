---
name: review-system-change
description: Independently review an implemented complex change for correctness, security, compatibility, data integrity, operability, coverage, and cross-boundary regressions. Assess a diff or change set; do not diagnose an unexplained failure or edit findings unless explicitly requested.
---

# Review System Change

Review the changed behavior as a system, not as an isolated diff.

## Workflow

1. Establish the comparison base, intended outcome, acceptance criteria,
   repository guidance, project agent-routing matrix, and verification already
   performed. Use routing evidence to select specialist reviewers for boundaries
   that actually changed.
2. Map changed files to behavior and boundaries using
   [references/review-checklist.md](references/review-checklist.md) as the
   mandatory core; then read only its linked checklists for changed boundaries.
   Read enough surrounding code and tests to reconstruct the real path. Apply
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md)
   to the affected public-surface inventory.
3. Select relevant independent reviewers from the canonical
   [agent-routing reference](../bootstrap-project-context/references/agent-routing.md)
   and verified project matrix. Use scoped reviewers when a required role is
   unavailable. Wait for all passes, verify findings, and remove duplicates.
   A `devsecops_engineer` reviewer must be a different agent from every writer
   in the reviewed scope. Because the role is workspace-write capable, constrain
   it to review-only actions, compare the worktree before and after its pass, and
   report any mutation as a failed independence gate. Use `security_engineer`
   for independent security conclusions and risk dispositions.
4. Check shared contracts end to end: server schema, client surface, MCP tool,
   persistence model, errors, authorization, compatibility, and rollout states.
   Compare the before and after public surface, including signatures, schemas,
   required fields, errors, defaults, names, and semantics. Treat an unapproved
   breaking change as blocking even when tests were updated to accept it.
5. Validate `.codex/documentation-evidence.json` when the change depends on
   external versioned or volatile behavior. Treat missing, stale, inferred,
   unresolved, secondary-only, or target-mismatched required claims as blocking.
6. Run or inspect the narrowest meaningful verification. Do not claim coverage
   from tests that do not exercise the changed behavior.
7. Confirm user README content, developer docs, examples, docstrings, comments,
   and release or migration guidance match the shipped behavior. Run the
   bundled portable-documentation validator and treat user-specific absolute
   home paths as blocking documentation defects. Fail closed when the
   public-documentation inventory or quality check is missing or fails.
8. Reject speculative findings. A finding must identify a concrete failure mode,
   affected behavior, and supporting evidence.

## Output

Lead with findings ordered by severity. For each finding include location,
failure mode, impact, evidence or reproduction, and the smallest defensible
remediation. Then list open questions, test gaps, and residual risks. If there
are no findings, say so and state what was reviewed and what could not be
verified. Report public-contract compatibility and approval status explicitly.
Do not edit files while using this skill unless asked to address the findings.
