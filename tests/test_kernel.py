import tempfile
import unittest
from pathlib import Path

from victor_skill_kernel.core import Skill, SkillRegistry, audit_skills, load_skills, route_skill

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class KernelTests(unittest.TestCase):
    def test_loads_canonical_skills(self):
        skills = load_skills(SKILLS)
        self.assertGreaterEqual(len(skills), 8)
        self.assertIn("victor-production-engineering-forge", {s.name for s in skills})

    def test_audit_has_no_high_findings_for_canonical_bundle(self):
        report = audit_skills(load_skills(SKILLS))
        high = [f for f in report.findings if f.severity == "high"]
        self.assertEqual(high, [], high)

    def test_routes_database_task_to_sql(self):
        ranked = route_skill("optimize SQL indexes and transaction query", load_skills(SKILLS), top_k=3)
        self.assertEqual(ranked[0][0].name, "sql-expert")

    def test_routes_local_ai_build_to_forge(self):
        ranked = route_skill("build a production local AI application repository and package it", load_skills(SKILLS), top_k=3)
        self.assertEqual(ranked[0][0].name, "victor-production-engineering-forge")

    def test_generated_not_trusted_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "registry.db"
            reg = SkillRegistry(db)
            try:
                with self.assertRaises(ValueError):
                    reg.receipt("x", "promote", "")
                rid = reg.receipt("x", "validated", "tests/test_kernel.py::test_generated_not_trusted_without_evidence")
                self.assertGreater(rid, 0)
            finally:
                reg.close()

    def test_overlap_detects_near_duplicate_engineering_skills(self):
        a = Skill(
            name="local-app-builder", description="build local production applications", path="a", body="build test package deploy",
            capabilities=("local-apps", "testing", "deployment"), jurisdiction="production-engineering"
        )
        b = Skill(
            name="repo-synthesizer", description="build production repositories", path="b", body="build test package deploy",
            capabilities=("local-apps", "testing", "deployment"), jurisdiction="production-engineering"
        )
        report = audit_skills([a, b])
        self.assertTrue(any({p.a, p.b} == {a.name, b.name} and p.score >= 0.52 for p in report.overlaps))
        self.assertEqual(len(report.merge_groups), 1)


if __name__ == "__main__":
    unittest.main()
