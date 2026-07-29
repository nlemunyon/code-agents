---
name: diagnose-system-failure
description: Diagnose cross-system failures, integration bugs, inconsistent interfaces, data drift, deployment-only faults, intermittent errors, or unclear root causes. Investigate and report by default; do not implement fixes or perform a change review unless explicitly requested.
---

# Diagnose System Failure

Prove the failing boundary and root cause before proposing remediation.

## Workflow

1. Capture the exact symptom, expected behavior, environment, inputs, timing,
   frequency, error text, correlation identifiers, and last known good state.
2. Reproduce with the smallest safe path available. Do not mutate production,
   live data, cloud resources, or shared environments to obtain a reproduction.
3. Trace the request and data path using
   [references/failure-matrix.md](references/failure-matrix.md). Distinguish
   client-side, protocol, service, persistence, workflow, container, network,
   and cloud-control-plane failures.
4. When the search space has independent branches, delegate read-only evidence
   collection to relevant specialists. Give each agent one hypothesis family
   and require commands, logs, file references, and disconfirming evidence. Use
   `devsecops_engineer` for CI/CD, runner, build, artifact, scanner, policy, and
   promotion-path failures; diagnosis alone does not authorize pipeline edits
   or external reruns.
5. When a hypothesis depends on version-specific external behavior, invoke
   `$verify-current-documentation` or delegate to `docs_researcher`. Match the
   actual environment version and configuration; do not diagnose from latest
   documentation or memory alone.
6. Build a short hypothesis table. Rank hypotheses by evidence and information
   gain, not intuition. Run the cheapest discriminating checks first.
7. Add temporary diagnostics only when existing evidence cannot distinguish the
   remaining hypotheses. Keep sensitive values out of logs and remove temporary
   instrumentation before handoff unless explicitly retained.
8. Confirm the root cause by explaining the complete causal chain and showing a
   test, trace, or observation that fails before remediation and succeeds after
   it. If proof is incomplete, state bounded uncertainty and the next decisive
   check.
9. Prefer remediation that preserves public API, client, MCP, protocol,
   configuration, event, and schema contracts. Classify any unavoidable break
   and stop for explicit approval and migration planning before implementation.
10. When the fix changes public help, list the docs in scope and apply
    [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
    Block when the list or docs check fails.

## Output

Return the symptom and scope, evidence collected, causal chain, ruled-out
hypotheses, root cause confidence, impact, safe remediation options, regression
test needed, documentation sources for version-specific behavior, and
operational follow-up. Do not implement a fix unless the user requested
diagnosis and repair.
