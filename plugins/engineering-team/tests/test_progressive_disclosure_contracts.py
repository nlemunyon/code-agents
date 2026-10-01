"""Contracts for quality-preserving progressive disclosure."""

from pathlib import Path
import re
import unittest


PLUGIN = Path(__file__).parents[1]
SKILLS = PLUGIN / "skills"
ROUTING = SKILLS / "bootstrap-project-context" / "references" / "agent-routing.md"
WORKFLOWS = ("plan-system-change", "review-system-change", "audit-system-security")


def _links(path: Path) -> list[Path]:
    text = path.read_text()
    return [
        (path.parent / target).resolve()
        for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text)
        if not target.startswith(("http://", "https://"))
    ]


class ProgressiveDisclosureContractsTest(unittest.TestCase):
    def test_domain_indexes_link_existing_references(self) -> None:
        checklists = {
            "plan-system-change": "boundary-checklist.md",
            "review-system-change": "review-checklist.md",
            "audit-system-security": "audit-checklist.md",
        }
        for skill, checklist_name in checklists.items():
            checklist = SKILLS / skill / "references" / checklist_name
            links = [path for path in _links(checklist) if path.parent == checklist.parent]
            self.assertGreaterEqual(len(links), 5)
            self.assertTrue(all(path.is_file() for path in links))

    def test_skills_require_core_before_domain_disclosure(self) -> None:
        expected = {
            "plan-system-change": "mandatory contract, security, evidence, and verification core",
            "review-system-change": "mandatory core",
            "audit-system-security": "mandatory core",
        }
        for skill, marker in expected.items():
            text = " ".join((SKILLS / skill / "SKILL.md").read_text().split())
            self.assertIn(marker, text)
            self.assertIn("then read only", text)

    def test_all_key_boundaries_remain_reachable(self) -> None:
        combined = "\n".join(
            path.read_text()
            for skill in WORKFLOWS
            for path in (SKILLS / skill / "references").glob("*.md")
        ).lower()
        for boundary in (
            "api", "python client", "mcp", "ui/ux", "database", "migration",
            "backfill", "container", "infrastructure", "ci/cd", "govcloud",
            "documentation", "cryptography", "supply-chain", "rollback",
        ):
            self.assertIn(boundary, combined)

    def test_workflows_use_canonical_role_routing(self) -> None:
        for skill in (*WORKFLOWS, "deliver-system-change"):
            text = (SKILLS / skill / "SKILL.md").read_text()
            self.assertIn("bootstrap-project-context/references/agent-routing.md", text)
        routing = ROUTING.read_text()
        for role in (
            "system_architect", "api_engineer", "client_engineer", "ai_ml_engineer",
            "ui_engineer", "ux_engineer", "data_engineer", "govcloud_engineer",
            "devsecops_engineer", "security_engineer", "docs_researcher",
            "technical_writer", "quality_engineer",
        ):
            self.assertIn(f"`{role}`", routing)

    def test_canonical_routing_preserves_ai_ml_data_ownership_split(self) -> None:
        routing = ROUTING.read_text()
        self.assertIn("model behavior, evaluation criteria, retrieval", routing)
        self.assertIn("inference integration, and MCP adapters to `ai_ml_engineer`", routing)
        self.assertIn("persistence, ingestion execution, pipeline operations, lineage, and", routing)
        self.assertIn("migrations to `data_engineer`", routing)
        self.assertIn("Establish their shared data contract before", routing)

    def test_review_and_audit_preserve_independence_limits(self) -> None:
        review = (SKILLS / "review-system-change" / "SKILL.md").read_text()
        audit = (SKILLS / "audit-system-security" / "SKILL.md").read_text()
        self.assertIn("different agent from every writer", review)
        self.assertIn("report any mutation as a failed independence gate", review)
        self.assertIn("audit coverage never authorizes edits", audit)
        self.assertIn("Delegation never authorizes external scans", audit)


if __name__ == "__main__":
    unittest.main()
