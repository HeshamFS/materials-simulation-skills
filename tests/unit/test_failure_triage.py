import unittest

from tests.unit._utils import load_module


def _symptoms(result):
    return [c["symptom"] for c in result["likely_causes"]]


def _categories(result):
    return [c["category"] for c in result["likely_causes"]]


class TestFailureTriage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "failure_triage",
            "skills/robustness/simulation-failure-triage/scripts/failure_triage.py",
        )

    def triage(self, **kwargs):
        params = dict(
            code="LAMMPS",
            stage="runtime",
            symptoms=[],
            log_text="",
            recent_change=None,
        )
        params.update(kwargs)
        return self.mod.triage_failure(**params)

    # --- F1: segfault must be a crash, not corrupted-output / I/O failure ---

    def test_segfault_is_crash_not_io(self):
        """Regression (F1): SIGSEGV must classify as a memory-fault crash."""
        result = self.triage(
            log_text="Program received signal SIGSEGV, Segmentation fault"
        )
        self.assertIn("crash", _symptoms(result))
        self.assertNotIn("corrupted-output", _symptoms(result))
        self.assertNotIn("I/O failure", _categories(result))
        self.assertIn("process crash / memory fault", _categories(result))

    def test_segfault_variants_are_crash(self):
        """Regression (F1): all common crash signatures route to 'crash'."""
        for phrase in [
            "segmentation fault",
            "received signal SIGSEGV",
            "terminated with signal 11",
            "core dumped",
        ]:
            result = self.triage(log_text=phrase)
            self.assertIn("crash", _symptoms(result), msg=f"missed crash on {phrase!r}")

    def test_crash_first_action_not_disk(self):
        """Regression (F1): crash guidance must not steer to disk/scratch."""
        result = self.triage(log_text="Segmentation fault")
        action = next(c["first_action"] for c in result["likely_causes"]
                      if c["symptom"] == "crash")
        self.assertNotIn("disk/scratch", action)
        self.assertIn("debugger", action.lower())

    # --- F2: OOM must classify as memory exhaustion ---

    def test_out_of_memory_is_memory_exhaustion(self):
        """Regression (F2): OOM classifies as memory exhaustion."""
        result = self.triage(log_text="slurmstepd: error: Out of memory, job killed")
        self.assertIn("out-of-memory", _symptoms(result))
        self.assertIn("memory exhaustion", _categories(result))

    def test_oom_variants(self):
        """Regression (F2): bad_alloc / oom-kill / allocation failed -> OOM."""
        for phrase in [
            "std::bad_alloc thrown",
            "oom-kill event triggered",
            "MPI allocation failed",
        ]:
            result = self.triage(log_text=phrase)
            self.assertIn(
                "out-of-memory", _symptoms(result),
                msg=f"missed OOM on {phrase!r}",
            )

    def test_bare_killed_stays_incomplete_run(self):
        """A bare SIGKILL remains ambiguous (incomplete-run), not OOM."""
        result = self.triage(log_text="slurmstepd: Killed")
        self.assertIn("incomplete-run", _symptoms(result))
        self.assertNotIn("out-of-memory", _symptoms(result))

    # --- F5: log excerpt preserves original casing ---

    def test_log_excerpt_preserves_case(self):
        """Regression (F5): excerpt keeps original casing of evidence."""
        result = self.triage(code="VASP", log_text="ZBRENT bracketing FATAL")
        self.assertEqual(result["evidence"]["log_excerpt"], "ZBRENT bracketing FATAL")

    def test_matching_still_case_insensitive(self):
        """Matching remains case-insensitive despite preserved excerpt."""
        upper = self.triage(log_text="SEGMENTATION FAULT")
        lower = self.triage(log_text="segmentation fault")
        self.assertEqual(_symptoms(upper), _symptoms(lower))

    # --- existing behavior preserved ---

    def test_missing_potential_symptom_string(self):
        """The emitted symptom is 'missing-potential' (hyphen)."""
        result = self.triage(log_text="Pair coeff for atom types missing")
        self.assertIn("missing-potential", _symptoms(result))

    def test_invalid_stage_raises(self):
        with self.assertRaises(ValueError):
            self.triage(stage="bogus")

    def test_empty_code_raises(self):
        with self.assertRaises(ValueError):
            self.triage(code="   ")

    # --- security caps ---

    def test_too_many_symptoms_raises(self):
        with self.assertRaises(ValueError):
            self.triage(symptoms=["a"] * 60)

    def test_overlong_symptom_raises(self):
        with self.assertRaises(ValueError):
            self.triage(symptoms=["x" * 101])

    def test_overlong_code_raises(self):
        with self.assertRaises(ValueError):
            self.triage(code="C" * 101)

    def test_caps_allow_normal_input(self):
        result = self.triage(symptoms=["nan"], code="LAMMPS")
        self.assertIn("nan", _symptoms(result))


if __name__ == "__main__":
    unittest.main()
