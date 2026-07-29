# Interface and adapter planning

## API service

- Operations, request and response models, status and error semantics
- Authentication, authorization, tenancy, rate limits, retries, and timeouts
- Domain-service boundaries, observability, contract tests, and generated docs

## Python client

- Imports, signatures, sync or async model, types, and exceptions
- Serialization, pagination, retries, timeouts, compatibility, and ergonomics
- Supported Python versions, packaging, dependencies, release notes, and tests

## MCP and protocols

- Tool and resource names, descriptions, schemas, output, and error mapping
- Transport, initialization, capability discovery, cancellation, and timeouts
- Authorization, sensitive data, confirmation for consequential actions, and
  end-to-end protocol tests
- Reuse of the supported client or domain layer instead of duplicated logic
