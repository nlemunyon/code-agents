# Data and recovery review

- Constraints encode invariants and indexes support changed access patterns.
- Migrations support mixed versions and realistic volume.
- Backfills are bounded, resumable, idempotent, observable, and reconcilable.
- Transactions and concurrency cannot cause loss, duplication, or drift.
- Rollback or forward recovery, backup, restore, lineage, retention, deletion,
  quality checks, and consumed schemas are explicit.
