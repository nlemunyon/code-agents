from __future__ import annotations

import re
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)

EXPECTED: dict[str, dict[str, tuple[str, ...]]] = {
    "audit-system-security": {
        "triggers": ("audit", "security findings", "repository or scoped path"),
        "exclusions": ("not implementing fixes", "iterative remediation", "Git diff"),
    },
    "bootstrap-project-context": {
        "triggers": ("repository guidance", "Codex configuration", "onboarding"),
        "exclusions": ("one-off code change", "user-level agent installation"),
    },
    "deliver-system-change": {
        "triggers": ("implement", "approved", "cross-system plan"),
        "exclusions": ("not initial planning", "orchestration", "without separate authorization"),
    },
    "diagnose-system-failure": {
        "triggers": ("diagnose", "cross-system failures", "root causes"),
        "exclusions": ("report by default", "do not implement fixes", "change review"),
    },
    "implement-devsecops-controls": {
        "triggers": ("implement", "CI/CD", "delivery-security automation"),
        "exclusions": ("not audit-only review", "application vulnerability remediation", "without separate authorization"),
    },
    "install-global-agents": {
        "triggers": ("install", "user-level Codex configuration", "global roles"),
        "exclusions": ("not project-specific context", "local agent overrides"),
    },
    "plan-system-change": {
        "triggers": ("plan", "complex cross-system", "executable work packages"),
        "exclusions": ("before implementation", "do not deliver", "orchestrate an approved plan"),
    },
    "remediate-security-findings": {
        "triggers": ("implement and verify fixes", "selected", "validated security findings"),
        "exclusions": ("not discovering findings", "iterative repository-wide", "unapproved breaking public contracts"),
    },
    "review-system-change": {
        "triggers": ("independently review", "implemented complex change", "change set"),
        "exclusions": ("do not diagnose", "unexplained failure", "edit findings unless explicitly requested"),
    },
    "verify-current-documentation": {
        "triggers": ("verify", "current primary documentation", "version, Region, partition"),
        "exclusions": ("never substitute latest documentation", "pinned older target", "unless upgrading"),
    },
}


def frontmatter(skill_name: str) -> tuple[str, str]:
    text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
    name_match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
    description_match = DESCRIPTION_RE.search(text)
    if name_match is None or description_match is None:
        raise AssertionError(f"{skill_name}: incomplete frontmatter")
    return name_match.group(1).strip(), description_match.group(1).strip()


class SkillRoutingDescriptionTests(unittest.TestCase):
    def test_names_and_compact_descriptions_preserve_contracts(self) -> None:
        for skill_name, contract in EXPECTED.items():
            with self.subTest(skill=skill_name):
                actual_name, description = frontmatter(skill_name)
                self.assertEqual(skill_name, actual_name)
                self.assertLessEqual(len(description.split()), 45)
                self.assertGreaterEqual(len(description.split()), 25)
                for phrase in contract["triggers"] + contract["exclusions"]:
                    self.assertIn(phrase.casefold(), description.casefold())

    def test_security_workflows_are_disambiguated(self) -> None:
        _, audit = frontmatter("audit-system-security")
        _, remediate = frontmatter("remediate-security-findings")
        self.assertIn("not implementing fixes", audit)
        self.assertIn("selected, validated security findings", remediate)
        self.assertIn("iterative remediation", audit)
        self.assertIn("iterative repository-wide audit-remediation", remediate)

    def test_change_workflows_are_disambiguated(self) -> None:
        _, plan = frontmatter("plan-system-change")
        _, deliver = frontmatter("deliver-system-change")
        self.assertIn("before implementation", plan)
        self.assertIn("approved complex cross-system plan", deliver)
        self.assertIn("do not deliver", plan)
        self.assertIn("not initial planning", deliver)
        self.assertIn("orchestrate an approved plan", plan)
        self.assertIn("audit-remediation orchestration", deliver)

    def test_review_and_diagnosis_are_disambiguated(self) -> None:
        _, review = frontmatter("review-system-change")
        _, diagnose = frontmatter("diagnose-system-failure")
        self.assertIn("implemented complex change", review)
        self.assertIn("unexplained failure", review)
        self.assertIn("root causes", diagnose)
        self.assertIn("change review", diagnose)


if __name__ == "__main__":
    unittest.main()
