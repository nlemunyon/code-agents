#!/usr/bin/env python3
"""Validate an orchestration JSONL resume contract and emit compact state."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


RUN_FIELDS = {
    "record_type", "schema_version", "run_id", "plan_id", "prior_digest", "digest",
    "budgets", "created_at", "repository", "plan_source", "approval_evidence",
    "outcome", "scope", "exclusions", "target", "instruction_sources",
    "routing_evidence", "acceptance_criteria", "work_graph", "public_contracts",
    "documentation_claim_ids", "public_documentation_inventory",
    "documentation_quality_gate", "rollout", "migration", "recovery", "risks",
    "assumptions", "decisions", "non_goals", "audit_scope",
    "remediation_write_scope", "checkpoint_rule", "extensions",
}
COMMON_EVENT_FIELDS = {
    "record_type", "sequence", "timestamp", "prior_digest", "digest", "status",
    "prior_status", "next_status", "slice_id", "work_package_id", "phase", "actor",
    "ownership_scope", "comparison_base", "result_revision", "criterion_evidence",
    "changed_files", "contract_status", "findings", "dispositions",
    "gate_record_ids", "command_receipt_ids", "documentation_evidence",
    "public_documentation_coverage", "grade_level_status", "residual_risk",
    "reason", "blockers", "budget_consumption", "next_action", "resume_condition",
    "extensions",
}
FINAL_FIELDS = COMMON_EVENT_FIELDS | {
    "criteria_complete", "work_packages_complete", "receipts_valid",
    "independent_review_clear", "security_converged", "contracts_approved",
    "documentation_gate_passed", "recovery_recorded", "limitations",
}
WORK_STATUSES = {"pending", "in-progress", "completed", "blocked", "superseded"}
FINAL_STATUSES = {"completed", "blocked", "non-convergent"}
TRANSITIONS = {
    "pending": {"pending", "in-progress", "blocked", "superseded"},
    "in-progress": {"in-progress", "completed", "blocked", "superseded"},
    "blocked": {"blocked", "in-progress", "superseded"},
    "completed": {"completed"},
    "superseded": {"superseded"},
}
LIMIT_TO_CONSUMPTION = {
    "max_iterations": "iterations",
    "max_distinct_findings": "distinct_findings",
    "max_elapsed_minutes": "elapsed_minutes",
    "max_cumulative_changed_files": "cumulative_changed_files",
    "token_budget": "tokens",
}
CONSUMPTION_TO_LIMIT = {value: key for key, value in LIMIT_TO_CONSUMPTION.items()}
RUN_REQUIRED = (
    "schema_version", "run_id", "plan_id", "created_at", "repository",
    "plan_source", "approval_evidence", "outcome", "scope", "exclusions",
    "target", "instruction_sources", "routing_evidence", "acceptance_criteria",
    "work_graph", "public_contracts", "documentation_claim_ids",
    "public_documentation_inventory", "documentation_quality_gate", "rollout",
    "migration", "recovery", "risks", "assumptions", "decisions", "non_goals",
    "audit_scope", "remediation_write_scope", "budgets", "checkpoint_rule",
)


class LedgerError(ValueError):
    """The ledger violates its integrity or minimum resume contract."""


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LedgerError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _required(record: dict[str, Any], fields: tuple[str, ...], line: int) -> None:
    missing = [field for field in fields if field not in record]
    if missing:
        raise LedgerError(f"line {line}: missing required fields: {', '.join(missing)}")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def compute_digest(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "digest"}
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_budgets(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or not value:
        raise LedgerError("line 1: budgets must be a non-empty object")
    unknown = set(value) - set(LIMIT_TO_CONSUMPTION)
    if unknown:
        raise LedgerError(f"line 1: unknown budget limits: {', '.join(sorted(unknown))}")
    for key, limit in value.items():
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise LedgerError(f"line 1: budgets.{key} must be a positive integer")
    return value


def _validate_header(record: dict[str, Any]) -> dict[str, int]:
    _required(record, RUN_REQUIRED, 1)
    if record["schema_version"] != 1:
        raise LedgerError("line 1: schema_version must be 1")
    for field in (
        "run_id", "plan_id", "created_at", "repository", "plan_source",
        "approval_evidence", "outcome", "scope", "target",
        "documentation_quality_gate", "rollout", "migration", "recovery",
        "audit_scope", "remediation_write_scope", "checkpoint_rule",
    ):
        if record[field] in (None, "", [], {}):
            raise LedgerError(f"line 1: {field} must not be empty")
    for field in (
        "exclusions", "instruction_sources", "routing_evidence", "public_contracts",
        "documentation_claim_ids", "public_documentation_inventory", "risks",
        "assumptions", "decisions", "non_goals",
    ):
        if not isinstance(record[field], list):
            raise LedgerError(f"line 1: {field} must be an array")
    criteria = record["acceptance_criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise LedgerError("line 1: acceptance_criteria must be a non-empty array")
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict) or not _nonempty(criterion.get("id")) or not _nonempty(
            criterion.get("verification_method")
        ):
            raise LedgerError(
                f"line 1: acceptance_criteria[{index}] requires id and verification_method"
            )
    graph = record["work_graph"]
    if not isinstance(graph, list) or not graph:
        raise LedgerError("line 1: work_graph must be a non-empty array")
    for index, package in enumerate(graph):
        if not isinstance(package, dict):
            raise LedgerError(f"line 1: work_graph[{index}] must be an object")
        missing = [
            field
            for field in ("id", "dependencies", "owner", "owned_paths", "exclusions", "criteria")
            if field not in package
        ]
        if missing:
            raise LedgerError(
                f"line 1: work_graph[{index}] missing {', '.join(missing)}"
            )
        if not _nonempty(package["id"]) or not _nonempty(package["owner"]):
            raise LedgerError(f"line 1: work_graph[{index}] requires id and owner")
        if any(
            not isinstance(package[field], list)
            for field in ("dependencies", "owned_paths", "exclusions", "criteria")
        ):
            raise LedgerError(
                f"line 1: work_graph[{index}] collection fields must be arrays"
            )
    return _validate_budgets(record["budgets"])


def _validate_consumption(
    value: Any, previous: dict[str, int], limits: dict[str, int], line: int
) -> dict[str, int]:
    if not isinstance(value, dict):
        raise LedgerError(f"line {line}: budget_consumption must be an object")
    known = {LIMIT_TO_CONSUMPTION[key] for key in limits}
    unknown = set(value) - known
    if unknown:
        raise LedgerError(
            f"line {line}: unknown budget consumption: {', '.join(sorted(unknown))}"
        )
    current = dict(previous)
    for key in known:
        amount = value.get(key, previous.get(key, 0))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise LedgerError(
                f"line {line}: budget_consumption.{key} must be a nonnegative integer"
            )
        if amount < previous.get(key, 0):
            raise LedgerError(f"line {line}: budget consumption reset for {key}")
        limit_key = CONSUMPTION_TO_LIMIT[key]
        if amount > limits[limit_key]:
            raise LedgerError(
                f"line {line}: budget_consumption.{key} exceeds {limit_key}"
            )
        current[key] = amount
    return current


def _validate_event(
    record: dict[str, Any],
    line: int,
    previous_states: dict[tuple[str | None, str | None], str],
    previous_consumption: dict[str, int],
    limits: dict[str, int],
) -> dict[str, int]:
    record_type = record["record_type"]
    allowed = FINAL_FIELDS if record_type == "final" else COMMON_EVENT_FIELDS
    unknown = set(record) - allowed
    if unknown:
        raise LedgerError(f"line {line}: unknown fields: {', '.join(sorted(unknown))}")
    _required(
        record,
        (
            "sequence", "status", "comparison_base", "result_revision",
            "gate_record_ids", "command_receipt_ids", "budget_consumption",
        ),
        line,
    )
    if not _nonempty(record["comparison_base"]) or not _nonempty(record["result_revision"]):
        raise LedgerError(f"line {line}: comparison_base and result_revision must be non-empty")
    for field in ("gate_record_ids", "command_receipt_ids"):
        if not isinstance(record[field], list) or any(
            not _nonempty(item) for item in record[field]
        ):
            raise LedgerError(f"line {line}: {field} must be an array of non-empty IDs")
    if not record["gate_record_ids"] and not record["command_receipt_ids"]:
        raise LedgerError(
            f"line {line}: at least one gate or command receipt ID is required"
        )

    if record_type == "transition":
        _required(
            record,
            ("prior_status", "next_status", "slice_id", "work_package_id", "phase"),
            line,
        )
        if any(
            not _nonempty(record[field])
            for field in ("slice_id", "work_package_id", "phase")
        ):
            raise LedgerError(
                f"line {line}: slice_id, work_package_id, and phase must be non-empty"
            )
        prior, next_status = record["prior_status"], record["next_status"]
        if prior not in WORK_STATUSES or next_status not in WORK_STATUSES:
            raise LedgerError(f"line {line}: invalid status")
        if record["status"] != next_status or next_status not in TRANSITIONS[prior]:
            raise LedgerError(f"line {line}: invalid status transition {prior!r} -> {next_status!r}")
        key = (record.get("slice_id"), record.get("work_package_id"))
        recorded_previous = previous_states.get(key, "pending")
        if prior != recorded_previous:
            raise LedgerError(
                f"line {line}: prior_status {prior!r} does not match {recorded_previous!r}"
            )
        previous_states[key] = next_status
    elif record["status"] not in FINAL_STATUSES:
        raise LedgerError(f"line {line}: invalid final status")

    if record_type == "final" and record["status"] == "completed":
        completion = (
            "criteria_complete", "work_packages_complete", "receipts_valid",
            "independent_review_clear", "security_converged", "contracts_approved",
            "documentation_gate_passed", "recovery_recorded",
        )
        _required(record, completion, line)
        if any(record[field] is not True for field in completion):
            raise LedgerError(f"line {line}: completed final has an unsatisfied completion gate")
    return _validate_consumption(
        record["budget_consumption"], previous_consumption, limits, line
    )


def load_and_validate(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LedgerError(f"cannot read {path}: {exc}") from exc
    if not raw:
        raise LedgerError("ledger is empty")
    if not raw.endswith(b"\n"):
        raise LedgerError("incomplete final line")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LedgerError("ledger is not valid UTF-8") from exc

    records: list[dict[str, Any]] = []
    previous_digest = "GENESIS"
    expected_sequence = 1
    limits: dict[str, int] = {}
    consumption: dict[str, int] = {}
    states: dict[tuple[str | None, str | None], str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            raise LedgerError(f"line {line_number}: blank records are not allowed")
        try:
            record = json.loads(line, object_pairs_hook=_object_pairs)
        except (json.JSONDecodeError, LedgerError) as exc:
            raise LedgerError(f"line {line_number}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise LedgerError(f"line {line_number}: record must be an object")
        _required(record, ("record_type", "prior_digest", "digest"), line_number)
        record_type = record["record_type"]
        if line_number == 1:
            if record_type != "run":
                raise LedgerError("line 1: first record_type must be 'run'")
            unknown = set(record) - RUN_FIELDS
            if unknown:
                raise LedgerError(f"line 1: unknown fields: {', '.join(sorted(unknown))}")
            limits = _validate_header(record)
        elif record_type not in {"transition", "final"}:
            raise LedgerError(f"line {line_number}: unknown record_type {record_type!r}")
        if records and records[-1]["record_type"] == "final":
            raise LedgerError(f"line {line_number}: final record must be last")
        if record["prior_digest"] != previous_digest:
            raise LedgerError(f"line {line_number}: prior_digest does not match chain")
        digest = compute_digest(record)
        if record["digest"] != digest:
            raise LedgerError(f"line {line_number}: digest mismatch")
        if record_type in {"transition", "final"}:
            if record.get("sequence") != expected_sequence:
                raise LedgerError(f"line {line_number}: sequence must be {expected_sequence}")
            consumption = _validate_event(
                record, line_number, states, consumption, limits
            )
            expected_sequence += 1
        previous_digest = digest
        records.append(record)

    if len(records) < 2:
        raise LedgerError("ledger requires a run header and at least one transition")
    if not any(record["record_type"] == "transition" for record in records[1:]):
        raise LedgerError("ledger requires at least one actual transition")
    if records[-1]["record_type"] == "final" and records[-1]["status"] == "completed":
        incomplete = {
            f"{slice_id or '<global>'}/{package_id or '<global>'}": status
            for (slice_id, package_id), status in states.items()
            if status not in {"completed", "superseded"}
        }
        blockers = _open_blockers(records)
        if incomplete:
            raise LedgerError(
                "completed final conflicts with incomplete persisted states: "
                + ", ".join(f"{key}={value}" for key, value in sorted(incomplete.items()))
            )
        if blockers:
            raise LedgerError(
                "completed final conflicts with open blockers: "
                + ", ".join(sorted(blockers))
            )
        declared_packages = {
            package["id"] for package in records[0]["work_graph"]
        }
        persisted_packages = {
            package_id
            for (_, package_id), status in states.items()
            if package_id is not None and status in {"completed", "superseded"}
        }
        missing_packages = declared_packages - persisted_packages
        if missing_packages:
            raise LedgerError(
                "completed final lacks completed persisted work packages: "
                + ", ".join(sorted(missing_packages))
            )
        covered_criteria: set[str] = set()
        for record in records[1:]:
            evidence = record.get("criterion_evidence", [])
            if isinstance(evidence, dict):
                covered_criteria.update(
                    key for key in evidence if isinstance(key, str)
                )
            elif isinstance(evidence, list):
                for item in evidence:
                    if isinstance(item, str):
                        covered_criteria.add(item)
                    elif isinstance(item, dict) and isinstance(item.get("id"), str):
                        covered_criteria.add(item["id"])
        declared_criteria = {
            criterion["id"] for criterion in records[0]["acceptance_criteria"]
        }
        missing_criteria = declared_criteria - covered_criteria
        if missing_criteria:
            raise LedgerError(
                "completed final lacks criterion evidence: "
                + ", ".join(sorted(missing_criteria))
            )
    return records, compact_state(records)


def _open_blockers(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    blockers: dict[str, dict[str, Any]] = {}
    for record in records[1:]:
        for blocker in record.get("blockers", []):
            if isinstance(blocker, dict) and isinstance(blocker.get("id"), str):
                if blocker.get("status", "open") == "closed":
                    blockers.pop(blocker["id"], None)
                else:
                    blockers[blocker["id"]] = blocker
    return blockers


def compact_state(records: list[dict[str, Any]]) -> dict[str, Any]:
    header, latest = records[0], records[-1]
    slices: dict[str, str] = {}
    packages: dict[str, str] = {}
    blockers = _open_blockers(records)
    consumption: dict[str, int] = {}
    for record in records[1:]:
        if isinstance(record.get("slice_id"), str):
            slices[record["slice_id"]] = record["status"]
        if isinstance(record.get("work_package_id"), str):
            packages[record["work_package_id"]] = record["status"]
        consumption.update(record["budget_consumption"])
    return {
        "schema_version": header["schema_version"], "run_id": header["run_id"],
        "plan_id": header["plan_id"], "status": latest["status"],
        "current_state": {"slices": slices, "work_packages": packages},
        "open_blockers": list(blockers.values()),
        "budgets": {"limits": header["budgets"], "consumption": consumption},
        "latest_sequence": latest["sequence"], "latest_digest": latest["digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--pretty", action="store_true", help="indent compact JSON output")
    args = parser.parse_args()
    try:
        _, compact = load_and_validate(args.ledger)
    except LedgerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(
        compact, ensure_ascii=False, sort_keys=True,
        indent=2 if args.pretty else None,
        separators=None if args.pretty else (",", ":"),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
