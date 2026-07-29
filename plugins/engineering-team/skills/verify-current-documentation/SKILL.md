---
name: verify-current-documentation
description: Verify material external or unstable claims against current primary documentation matching the installed or targeted version, Region, partition, and configuration. Use as evidence for dependent work; never substitute latest documentation for a pinned older target unless upgrading.
---

# Verify Current Documentation

Create decision-grade evidence for version-sensitive external claims. Treat
training knowledge as hypothesis generation, never as proof.

## Workflow

1. Define the claims that materially affect the task. Avoid researching broad
   topics that cannot change the decision.
2. Establish the exact target from repository and user evidence: dependency,
   provider, protocol, standard, product edition, version, Region, partition,
   enabled features, and configuration. Record unknowns instead of assuming
   latest.
3. Delegate read-only research to `docs_researcher` when available. For separate
   products or standards, use independent bounded assignments and wait for all
   results.
4. Follow [references/evidence-policy.md](references/evidence-policy.md). Use
   primary, target-matched sources. Fetch the actual page or specification
   section; do not cite a search result page as evidence.
5. Cross-check release notes or migration guidance when behavior changed near
   the target version. Resolve contradictions or mark the claim unresolved.
6. Create or update `.codex/documentation-evidence.json` in the target project.
   Start from [assets/documentation-evidence.json](assets/documentation-evidence.json)
   when no ledger exists. Preserve unrelated valid claims.
7. Choose an explicit `valid_until` based on volatility and project risk. Service
   and Region availability generally needs a shorter window than a versioned
   specification. Record why the source is authoritative, how it matches the
   exact target, its volatility class, and the freshness rationale. Do not use a
   long validity exception without reviewable justification.
8. Validate the ledger from this skill directory:

   ```bash
   python3 ../../scripts/validate_documentation_evidence.py \
     /path/to/project/.codex/documentation-evidence.json
   ```

9. Stop dependent implementation when a required claim is stale, inferred,
   unresolved, secondary-only, or mismatched to the actual target. Report the
   missing evidence and next decisive check.

## Output

Return verified claims and decisions with nearby citations, the ledger path,
validator result, unresolved claims, expiry dates, and the work packages blocked
by missing evidence. If the environment is read-only, return complete JSON claim
entries for the parent to persist and validate.
