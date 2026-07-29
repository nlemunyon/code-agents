---
name: implement-devsecops-controls
description: Implement repository-scoped CI/CD, provenance, scanning, policy-as-code, pipeline, and promotion controls. Use for delivery-security automation, not audit-only review, application vulnerability remediation, deployment, release execution, cloud mutation, credential rotation, or repository-settings changes without separate authorization.
---

# Implement DevSecOps Controls

Improve the software-delivery path without conflating control implementation
with independent security assessment or authorization to operate external systems.

## Establish the delivery contract

1. Resolve the repository root, applicable instructions, exact write scope,
   comparison base, target CI/CD platform, runner trust model, environments,
   identities, artifacts, registries, deployment boundaries, and rollback path.
2. Inventory workflows, reusable actions, build definitions, container files,
   infrastructure validation, policy, scanners, dependency automation, signing,
   provenance, release metadata, and required checks. Read
   [the control checklist](references/control-checklist.md) only for relevant
   surfaces.
3. Separate repository changes from external mutations. Editing workflow or
   policy files does not authorize running releases, changing branch protection,
   updating repository secrets, rotating credentials, promoting environments,
   publishing artifacts, or mutating cloud resources.
4. Classify affected public and delivery contracts. Preserve stable commands,
   configuration, events, artifacts, interfaces, and consumer workflows unless
   the user explicitly approves a necessary breaking migration and rollback plan.
   List docs for each public command, config key, policy, or build file. Apply
   [the documentation quality contract](../deliver-system-change/references/documentation-quality-contract.md).
5. Invoke `$verify-current-documentation` for material version-, platform-,
   action-, scanner-, cloud-, Region-, partition-, registry-, or standard-
   sensitive claims. Required unresolved or target-mismatched evidence blocks
   dependent implementation.

## Implement safely

1. Baseline the current behavior and failure mode with local lint, validation,
   policy, fixture, or build-only tests. Never expose repository secrets or run
   untrusted contributions with privileged credentials.
2. Assign `devsecops_engineer` as writer for delivery automation, policy-as-code,
   build security, provenance, and supply-chain controls. Use `security_engineer`
   independently for threat-led requirements and final validation;
   `govcloud_engineer` for GovCloud architecture and partition behavior; and the
   appropriate application, data, AI/ML, UI, or infrastructure owner for changes
   outside the delivery boundary.
3. Implement the smallest root-cause control. Use least-privilege job tokens,
   immutable dependency references where supported, trusted build inputs,
   isolated untrusted jobs, deterministic artifacts, explicit promotion gates,
   protected evidence, and safe failure behavior.
4. Do not weaken required checks, suppress findings, broaden permissions, or
   hide diagnostics to obtain a passing pipeline. A justified exception requires
   stable identity, exact scope, accountable owner, evidence, expiry, and
   independent approval; otherwise record it as blocked.
5. Keep one writer per workflow, policy, lockfile, generated artifact, public
   contract, and infrastructure file. Preserve unrelated changes.

## Verify and hand off

Run narrow validators after each change and broader repository checks before
completion. Exercise trusted and untrusted inputs, missing permissions, scanner
findings, artifact verification failure, retry, cancellation, partial failure,
promotion denial, and rollback paths where applicable. Prefer dry runs and local
fixtures; unavailable hosted checks remain explicit limitations. Block when
the public docs list or its check fails.

Require an independent `security_engineer` review for changed trust boundaries,
credentials, provenance, signing, policy enforcement, or security gates, and a
`quality_engineer` review for cross-boundary behavior. Report controls added,
files changed, commands and results, documentation evidence, contract impact,
external actions not performed, residual risk, rollout/rollback instructions,
and any action requiring separate authority. Never claim that pipeline controls
or passing scans prove compliance, certification, or authorization.
