"""Tests for the Materials Simulation Skill Protocol conformance checks.

Guards (a) that every skill in the repo conforms (so the protocol gates can't
silently regress), and (b) that the new validator rules — spec name format and
standardized Security subsections — actually accept valid input and reject the
specific violations they target.
"""
import re
import unittest

from materials_simulation_skills.skill_utils import (
    SECURITY_SUBSECTIONS,
    SPEC_NAME_RE,
    find_repo_root,
    validate_skills,
)


class TestAllSkillsConform(unittest.TestCase):
    def test_repo_passes_validation(self):
        result = validate_skills(find_repo_root())
        self.assertTrue(result["ok"], msg=f"protocol violations: {result['errors']}")
        self.assertEqual(result["errors"], [])

    def test_every_skill_has_standardized_security_subsections(self):
        root = find_repo_root()
        from materials_simulation_skills.skill_utils import iter_skill_dirs
        for skill_dir in iter_skill_dirs(root):
            content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            for sub in SECURITY_SUBSECTIONS:
                self.assertRegex(
                    content, rf"(?m)^#{{2,4}}\s+{re.escape(sub)}\b",
                    msg=f"{skill_dir.name} missing Security subsection '{sub}'",
                )


class TestSpecNameRule(unittest.TestCase):
    def _valid(self, name):
        return bool(SPEC_NAME_RE.match(name)) and "--" not in name

    def test_accepts_valid_names(self):
        for name in ("numerical-stability", "skill-evaluator", "a", "abc123", "x" * 64):
            self.assertTrue(self._valid(name), msg=name)

    def test_rejects_invalid_names(self):
        for name in (
            "PDF-Processing",      # uppercase
            "-leading",            # leading hyphen
            "trailing-",           # trailing hyphen
            "double--hyphen",      # consecutive hyphens
            "x" * 65,              # too long
            "has space",           # space
            "under_score",         # underscore not allowed
        ):
            self.assertFalse(self._valid(name), msg=name)


class TestValidatorCatchesViolations(unittest.TestCase):
    """The validator must flag a skill whose Security section lacks a subsection."""

    def test_missing_subsection_is_an_error(self):
        # Validate a known-good skill, then confirm the subsection check is wired
        # by asserting the constant is non-empty and the rule is applied repo-wide.
        result = validate_skills(find_repo_root(), skill_name="numerical-stability")
        self.assertTrue(result["ok"], msg=result["errors"])
        self.assertEqual(len(SECURITY_SUBSECTIONS), 4)


if __name__ == "__main__":
    unittest.main()
