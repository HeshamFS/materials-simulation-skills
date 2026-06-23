import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.unit._utils import load_module


class TestFairPackager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "fair_packager",
            "skills/data-management/fair-simulation-packager/scripts/fair_packager.py",
        )

    def _build(self, **kwargs):
        params = dict(
            project_name="proj",
            engine="LAMMPS",
            inputs=[],
            outputs=[],
            units={},
            structure_id=None,
            engine_version=None,
        )
        params.update(kwargs)
        return self.mod.build_manifest(**params)

    # --- F4: tri-state has_hashes_for_existing_files ---

    def test_has_hashes_null_when_no_files(self):
        """Regression (F4): with no files the check is not applicable -> None."""
        manifest = self._build()
        self.assertIsNone(manifest["fair_checks"]["has_hashes_for_existing_files"])

    def test_has_hashes_null_when_only_missing_files(self):
        """Regression (F4): only nonexistent files means no existing file -> None."""
        manifest = self._build(inputs=["definitely-not-a-real-file.xyz"])
        self.assertIsNone(manifest["fair_checks"]["has_hashes_for_existing_files"])
        self.assertIn("definitely-not-a-real-file.xyz", manifest["missing_files"])

    def test_has_hashes_true_when_existing_file_hashed(self):
        """Regression (F4): an existing file yields a sha256 and the check is True."""
        with TemporaryDirectory() as tmp:
            fpath = Path(tmp) / "in.lammps"
            fpath.write_text("units metal\n", encoding="utf-8")
            manifest = self._build(inputs=[str(fpath)])
        self.assertTrue(manifest["fair_checks"]["has_hashes_for_existing_files"])
        rec = manifest["file_inventory"]["inputs"][0]
        self.assertTrue(rec["exists"])
        self.assertIn("sha256", rec)
        self.assertIn("size_bytes", rec)

    # --- core behavior ---

    def test_units_parsed(self):
        units = self.mod.parse_units("energy=eV,length=angstrom")
        self.assertEqual(units, {"energy": "eV", "length": "angstrom"})

    def test_units_require_key_value(self):
        with self.assertRaises(ValueError):
            self.mod.parse_units("energy")

    def test_units_reject_unsafe_chars(self):
        with self.assertRaises(ValueError):
            self.mod.parse_units("energy=eV;rm -rf")

    def test_missing_file_recorded_not_dropped(self):
        manifest = self._build(outputs=["traj.dump"])
        self.assertEqual(manifest["missing_files"], ["traj.dump"])
        self.assertFalse(manifest["file_inventory"]["outputs"][0]["exists"])

    def test_provenance_fields(self):
        manifest = self._build()
        self.assertIn("working_directory", manifest["provenance"])
        self.assertEqual(
            manifest["provenance"]["manifest_schema"],
            "materials-simulation-skills.fair-manifest.v1",
        )

    def test_engine_version_check(self):
        manifest = self._build(engine_version="2024.1")
        self.assertTrue(manifest["fair_checks"]["has_engine_version"])
        self.assertEqual(manifest["engine_version"], "2024.1")

    def test_recommended_next_steps_populated(self):
        manifest = self._build()
        self.assertTrue(len(manifest["recommended_next_steps"]) > 0)

    def test_empty_project_name_rejected(self):
        with self.assertRaises(ValueError):
            self._build(project_name="  ")

    # --- security hardening (must match SKILL.md Security claims) ---

    def test_control_char_rejected(self):
        with self.assertRaises(ValueError):
            self._build(project_name="bad\x01name")

    def test_field_length_cap(self):
        """Regression: fields longer than MAX_FIELD_LEN are rejected."""
        with self.assertRaises(ValueError):
            self._build(project_name="a" * (self.mod.MAX_FIELD_LEN + 1))

    def test_entry_count_cap(self):
        """Regression: lists with more than MAX_ENTRIES entries are rejected."""
        big = ",".join(f"f{i}" for i in range(self.mod.MAX_ENTRIES + 1))
        with self.assertRaises(ValueError):
            self.mod._split_csv(big, "inputs")

    def test_entry_count_cap_at_limit_ok(self):
        ok = ",".join(f"f{i}" for i in range(self.mod.MAX_ENTRIES))
        result = self.mod._split_csv(ok, "inputs")
        self.assertEqual(len(result), self.mod.MAX_ENTRIES)

    def test_oversized_file_rejected(self):
        """A file larger than MAX_FILE_SIZE raises ValueError (exit code 2 path)."""
        original = self.mod.MAX_FILE_SIZE
        try:
            self.mod.MAX_FILE_SIZE = 4
            with TemporaryDirectory() as tmp:
                fpath = Path(tmp) / "big.dat"
                fpath.write_text("0123456789", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.mod.file_record(str(fpath))
        finally:
            self.mod.MAX_FILE_SIZE = original


if __name__ == "__main__":
    unittest.main()
