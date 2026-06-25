import unittest

from tests.unit._utils import load_module


class TestFailureDiagnoser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "failure_diagnoser",
            "skills/simulation-workflow/simulation-validator/scripts/failure_diagnoser.py",
        )

    def test_detect_nan(self):
        """Test NaN detection."""
        result = self.mod.diagnose("NaN encountered in solver at step 1523")
        self.assertIn("Numerical blow-up", result["probable_causes"])

    def test_detect_inf(self):
        """Test Inf detection."""
        result = self.mod.diagnose("Field contains Inf values")
        self.assertIn("Numerical blow-up", result["probable_causes"])

    def test_detect_overflow(self):
        """Test overflow detection."""
        result = self.mod.diagnose("Overflow detected in computation")
        self.assertIn("Numerical blow-up", result["probable_causes"])

    def test_detect_divergence(self):
        """Test divergence detection."""
        result = self.mod.diagnose("Solution diverging at iteration 5000")
        self.assertIn("Convergence failure", result["probable_causes"])

    def test_detect_did_not_converge(self):
        """Genuine convergence failure phrasing is detected."""
        result = self.mod.diagnose("Newton: did not converge in 50 iterations")
        self.assertIn("Convergence failure", result["probable_causes"])

    def test_detect_max_iterations(self):
        """Max-iteration stagnation is detected as convergence failure."""
        result = self.mod.diagnose("Linear solver: max iterations (1000) reached")
        self.assertIn("Convergence failure", result["probable_causes"])

    def test_bare_residual_is_not_convergence_failure(self):
        """Regression (F2): the bare token 'residual' must NOT flag a failure.

        It appears in virtually every healthy solver log; flagging it caused
        successful runs to be diagnosed as 'Convergence failure'.
        """
        result = self.mod.diagnose("step 1 residual = 1e-8 converged successfully")
        self.assertNotIn("Convergence failure", result["probable_causes"])
        self.assertIn("Unknown", result["probable_causes"])

    def test_success_log_is_unknown(self):
        """Regression (F2): a fully successful run yields only 'Unknown'."""
        log = (
            "Timestep 100 | residual=1.27e-06\n"
            "Simulation Complete\n"
            "Mass conservation error: 1.00e-04\n"
        )
        result = self.mod.diagnose(log)
        self.assertEqual(result["probable_causes"], ["Unknown"])

    def test_domain_words_not_blowup(self):
        """Regression (F3): materials-domain words must NOT trigger blow-up."""
        for word in ["nanometer scale resolved", "infrastructure ready",
                     "financial summary", "information logged", "infinitesimal step"]:
            result = self.mod.diagnose(word)
            self.assertNotIn(
                "Numerical blow-up", result["probable_causes"],
                msg=f"false blow-up on {word!r}",
            )

    def test_genuine_nan_variants_detected(self):
        """Regression (F3): NaN, NaNs, infinity, overflow still detected."""
        for word in ["NaN at step 10", "NaNs everywhere",
                     "residual went to infinity", "Solution overflow"]:
            result = self.mod.diagnose(word)
            self.assertIn(
                "Numerical blow-up", result["probable_causes"],
                msg=f"missed blow-up on {word!r}",
            )

    def test_detect_memory(self):
        """Test out of memory detection."""
        result = self.mod.diagnose("Out of memory allocating array")
        self.assertIn("Memory exhaustion", result["probable_causes"])

    def test_detect_allocation_failed(self):
        """Test allocation failed detection."""
        result = self.mod.diagnose("std::bad_alloc: allocation failed")
        self.assertIn("Memory exhaustion", result["probable_causes"])

    def test_detect_disk_full(self):
        """Test disk full detection."""
        result = self.mod.diagnose("Error: disk full, cannot write checkpoint")
        self.assertIn("I/O error", result["probable_causes"])

    def test_detect_permission_denied(self):
        """Test permission denied detection."""
        result = self.mod.diagnose("Permission denied: /output/results.h5")
        self.assertIn("I/O error", result["probable_causes"])

    def test_unknown_failure(self):
        """Test unknown failure (no pattern match)."""
        result = self.mod.diagnose("All good, simulation completed successfully")
        self.assertIn("Unknown", result["probable_causes"])
        self.assertEqual(len(result["probable_causes"]), 1)

    def test_multiple_patterns(self):
        """Test multiple patterns detected."""
        log = "NaN in field\nSolution diverging\nOut of memory"
        result = self.mod.diagnose(log)
        self.assertIn("Numerical blow-up", result["probable_causes"])
        self.assertIn("Convergence failure", result["probable_causes"])
        self.assertIn("Memory exhaustion", result["probable_causes"])

    def test_fixes_provided(self):
        """Test recommended fixes are provided."""
        result = self.mod.diagnose("NaN encountered")
        self.assertGreater(len(result["recommended_fixes"]), 0)
        self.assertIn("dt", result["recommended_fixes"][0].lower())

    def test_case_insensitive(self):
        """Test pattern matching is case insensitive."""
        result_upper = self.mod.diagnose("NAN detected")
        result_lower = self.mod.diagnose("nan detected")
        self.assertEqual(result_upper["probable_causes"], result_lower["probable_causes"])

    def test_empty_log(self):
        """Test empty log returns Unknown."""
        result = self.mod.diagnose("")
        self.assertIn("Unknown", result["probable_causes"])

    def test_causes_and_fixes_match(self):
        """Test causes and fixes lists have same length."""
        result = self.mod.diagnose("NaN and divergence and out of memory")
        self.assertEqual(len(result["probable_causes"]), len(result["recommended_fixes"]))

    def test_multiline_log(self):
        """Test multiline log parsing."""
        log = """Step 1: residual = 1e-3
Step 2: residual = 1e-4
Step 3: NaN detected in temperature field
Solver stopped."""
        result = self.mod.diagnose(log)
        self.assertIn("Numerical blow-up", result["probable_causes"])


if __name__ == "__main__":
    unittest.main()
