#!/usr/bin/env python3
"""Tests for the dependency-free orchestration ledger validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_orchestration_ledger.py"
SPEC = importlib.util.spec_from_file_location("ledger_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def chained(records: list[dict]) -> str:
    prior = "GENESIS"
    lines = []
    for record in records:
        record["prior_digest"] = prior
        record["digest"] = MODULE.compute_digest(record)
        prior = record["digest"]
        lines.append(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def valid_records() -> list[dict]:
    return [
        {
            "record_type": "run",
            "schema_version": 1,
            "run_id": "run-1",
            "plan_id": "plan-1",
            "created_at": "2026-07-29T00:00:00Z",
            "repository": "example/repository",
            "plan_source": "approved-plan.md",
            "approval_evidence": "user-message-1",
            "outcome": "deliver the approved change",
            "scope": ["component"],
            "exclusions": [],
            "target": {"environment": "local"},
            "instruction_sources": ["AGENTS.md"],
            "routing_evidence": ["repository matrix"],
            "acceptance_criteria": [
                {"id": "AC-1", "verification_method": "run focused tests"}
            ],
            "work_graph": [
                {
                    "id": "WP-1",
                    "dependencies": [],
                    "owner": "worker",
                    "owned_paths": ["component"],
                    "exclusions": [],
                    "criteria": ["AC-1"],
                }
            ],
            "public_contracts": [],
            "documentation_claim_ids": [],
            "public_documentation_inventory": [],
            "documentation_quality_gate": "validate docs",
            "rollout": "local integration",
            "migration": "not applicable",
            "recovery": "revert patch",
            "risks": [],
            "assumptions": [],
            "decisions": [],
            "non_goals": [],
            "audit_scope": ["component"],
            "remediation_write_scope": ["component"],
            "budgets": {"max_iterations": 5, "max_cumulative_changed_files": 50},
            "checkpoint_rule": "checkpoint before any limit",
        },
        {
            "record_type": "transition",
            "sequence": 1,
            "status": "blocked",
            "prior_status": "pending",
            "next_status": "blocked",
            "slice_id": "slice-1",
            "work_package_id": "WP-1",
            "phase": "review",
            "comparison_base": "abc123",
            "result_revision": "def456",
            "gate_record_ids": ["gate-1"],
            "command_receipt_ids": ["command-1"],
            "blockers": [
                {"id": "approval-1", "status": "open", "reason": "approval required"}
            ],
            "budget_consumption": {
                "iterations": 1,
                "cumulative_changed_files": 2,
            },
        },
    ]


def completed_records() -> list[dict]:
    records = valid_records()
    records[1].update(
        status="in-progress",
        prior_status="pending",
        next_status="in-progress",
        blockers=[],
    )
    completed = dict(records[1])
    completed.update(
        sequence=2,
        status="completed",
        prior_status="in-progress",
        next_status="completed",
        criterion_evidence=["AC-1"],
    )
    final = {
        "record_type": "final",
        "sequence": 3,
        "status": "completed",
        "comparison_base": "abc123",
        "result_revision": "def456",
        "gate_record_ids": ["gate-final"],
        "command_receipt_ids": ["command-final"],
        "budget_consumption": {
            "iterations": 1,
            "cumulative_changed_files": 2,
        },
        "criteria_complete": True,
        "work_packages_complete": True,
        "receipts_valid": True,
        "independent_review_clear": True,
        "security_converged": True,
        "contracts_approved": True,
        "documentation_gate_passed": True,
        "recovery_recorded": True,
    }
    records.extend((completed, final))
    return records


class LedgerValidatorTests(unittest.TestCase):
    def run_cli(self, text: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_valid_chain_emits_compact_resume_state(self) -> None:
        result = self.run_cli(chained(valid_records()))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["current_state"]["slices"], {"slice-1": "blocked"})
        self.assertEqual(output["open_blockers"][0]["id"], "approval-1")
        self.assertEqual(
            output["budgets"]["consumption"]["cumulative_changed_files"], 2
        )
        self.assertEqual(len(output["latest_digest"]), 64)
        self.assertNotIn("approval required", result.stdout.split("open_blockers")[0])

    def test_tampered_record_fails(self) -> None:
        text = chained(valid_records()).replace(
            '"cumulative_changed_files":2', '"cumulative_changed_files":3'
        )
        result = self.run_cli(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("digest mismatch", result.stderr)

    def test_missing_required_record_fails(self) -> None:
        result = self.run_cli(chained(valid_records()[:1]))
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least one transition", result.stderr)

    def test_missing_required_field_fails(self) -> None:
        records = valid_records()
        del records[0]["budgets"]
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("budgets", result.stderr)

    def test_incomplete_full_header_fails(self) -> None:
        records = valid_records()
        del records[0]["recovery"]
        del records[0]["acceptance_criteria"]
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("acceptance_criteria", result.stderr)
        self.assertIn("recovery", result.stderr)

    def test_incomplete_final_line_fails(self) -> None:
        result = self.run_cli(chained(valid_records()).rstrip("\n"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("incomplete final line", result.stderr)

    def test_unknown_schema_fails(self) -> None:
        records = valid_records()
        records[0]["schema_version"] = 999
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("schema_version must be 1", result.stderr)

    def test_over_budget_fails(self) -> None:
        records = valid_records()
        records[1]["budget_consumption"]["iterations"] = 6
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceeds max_iterations", result.stderr)

    def test_budget_reset_fails(self) -> None:
        records = valid_records()
        second = dict(records[1])
        second.update(
            sequence=2,
            prior_status="blocked",
            next_status="in-progress",
            status="in-progress",
            budget_consumption={"iterations": 0, "cumulative_changed_files": 2},
        )
        records.append(second)
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("budget consumption reset", result.stderr)

    def test_final_followed_by_transition_fails(self) -> None:
        records = valid_records()
        records[1].update(
            record_type="final",
            status="blocked",
        )
        later = dict(valid_records()[1])
        later["sequence"] = 2
        records.append(later)
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("final record must be last", result.stderr)

    def test_invalid_status_transition_fails(self) -> None:
        records = valid_records()
        records[1].update(
            prior_status="pending", next_status="completed", status="completed"
        )
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid status transition", result.stderr)

    def test_missing_revision_and_receipts_fails(self) -> None:
        records = valid_records()
        del records[1]["result_revision"]
        del records[1]["gate_record_ids"]
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("result_revision", result.stderr)
        self.assertIn("gate_record_ids", result.stderr)

    def test_empty_receipt_references_fail(self) -> None:
        records = valid_records()
        records[1]["gate_record_ids"] = []
        records[1]["command_receipt_ids"] = []
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least one gate or command receipt ID", result.stderr)

    def test_completed_final_requires_all_completion_gates(self) -> None:
        records = valid_records()
        records[1].update(record_type="final", status="completed")
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("criteria_complete", result.stderr)

    def test_completed_final_rejects_blocked_state_and_open_blocker(self) -> None:
        records = valid_records()
        final = {
            "record_type": "final",
            "sequence": 2,
            "status": "completed",
            "comparison_base": "abc123",
            "result_revision": "def456",
            "gate_record_ids": ["gate-final"],
            "command_receipt_ids": ["command-final"],
            "budget_consumption": {
                "iterations": 1,
                "cumulative_changed_files": 2,
            },
            "criteria_complete": True,
            "work_packages_complete": True,
            "receipts_valid": True,
            "independent_review_clear": True,
            "security_converged": True,
            "contracts_approved": True,
            "documentation_gate_passed": True,
            "recovery_recorded": True,
        }
        records.append(final)
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("incomplete persisted states", result.stderr)

    def test_completed_final_rejects_open_blocker_after_work_completes(self) -> None:
        records = valid_records()
        records[1].update(
            status="in-progress", prior_status="pending", next_status="in-progress"
        )
        completed = dict(records[1])
        completed.update(
            sequence=2,
            status="completed",
            prior_status="in-progress",
            next_status="completed",
        )
        final = {
            "record_type": "final",
            "sequence": 3,
            "status": "completed",
            "comparison_base": "abc123",
            "result_revision": "def456",
            "gate_record_ids": ["gate-final"],
            "command_receipt_ids": ["command-final"],
            "budget_consumption": {
                "iterations": 1,
                "cumulative_changed_files": 2,
            },
            "criteria_complete": True,
            "work_packages_complete": True,
            "receipts_valid": True,
            "independent_review_clear": True,
            "security_converged": True,
            "contracts_approved": True,
            "documentation_gate_passed": True,
            "recovery_recorded": True,
        }
        records.extend((completed, final))
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("open blockers", result.stderr)

    def test_header_and_final_without_transition_fails(self) -> None:
        records = completed_records()
        records = [records[0], records[-1]]
        records[1]["sequence"] = 1
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("actual transition", result.stderr)

    def test_completed_final_rejects_omitted_declared_package(self) -> None:
        records = completed_records()
        records[0]["work_graph"].append(
            {
                "id": "WP-2",
                "dependencies": ["WP-1"],
                "owner": "worker",
                "owned_paths": ["other-component"],
                "exclusions": [],
                "criteria": ["AC-1"],
            }
        )
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("WP-2", result.stderr)

    def test_completed_final_rejects_omitted_criterion_evidence(self) -> None:
        records = completed_records()
        del records[2]["criterion_evidence"]
        result = self.run_cli(chained(records))
        self.assertEqual(result.returncode, 1)
        self.assertIn("criterion evidence", result.stderr)

    def test_composite_skills_preserve_parent_budget_precedence(self) -> None:
        orchestrator = (
            ROOT / "skills" / "orchestrate-system-change" / "SKILL.md"
        ).read_text(encoding="utf-8")
        security = (
            ROOT / "skills" / "secure-system-iteratively" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for text in (orchestrator, security):
            self.assertIn("stricter", text)
            self.assertIn("remaining applicable", text)
            self.assertIn("never resets parent consumption", text)

    def test_orchestrator_routes_approved_migration_delivery(self) -> None:
        description = (
            ROOT / "skills" / "orchestrate-system-change" / "SKILL.md"
        ).read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("including approved migrations", description)
        self.assertIn("migration application", description)

    def test_orchestrator_routes_approved_breaking_migration_plan(self) -> None:
        description = (
            ROOT / "skills" / "orchestrate-system-change" / "SKILL.md"
        ).read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("breaking migration plans", description)
        self.assertIn("unapproved breaking changes", description)


if __name__ == "__main__":
    unittest.main()
