# Security audit checklist

Always apply this threat-led core. Then read only the linked domain checklists
supported by scope evidence. Record selected and excluded domains.

## Architecture and source-to-sink analysis

- Identify assets, actors, entry points, trust boundaries, privileges, tenancy,
  sensitive data, external services, admin paths, and failure domains.
- Trace authentication, authorization, ownership, isolation, and attacker input
  through validation to interpreters, queries, files, networks, subprocesses,
  loaders, redirects, and other security sinks.
- Check canonicalization, size bounds, races, and plausible injection,
  traversal, request-smuggling, unsafe parsing, and denial-of-service paths.
- Verify reachability, protections, preconditions, impact, and compensating
  controls before validating a finding.

## Evidence and reporting

- Anchor findings to exact locations and plausible attack paths; reject keyword,
  age-only, generic-best-practice, and implausible misuse findings.
- Resolve versions and use target-matched primary evidence for volatile claims.
- Distinguish vulnerabilities, hardening, missing evidence, policy gaps, and
  accepted residual risk.
- Cite exact control identifiers without equating review or control presence
  with compliance or certification.
- Report excluded paths, unavailable tools, stale evidence, target mismatches,
  and untested behavior.

## Domain routing

- APIs, MCP, models, retrieval, inference: [API, MCP, and AI](api-mcp-and-ai.md)
- Databases, workflows, sensitive data, crypto: [data and cryptography](data-and-cryptography.md)
- Secrets, dependencies, artifacts, CI/CD: [supply chain](supply-chain.md)
- Containers, infrastructure, cloud, GovCloud: [runtime and cloud](runtime-and-cloud.md)
- Public help affected by findings: [documentation](documentation.md)
