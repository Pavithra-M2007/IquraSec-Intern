#!/usr/bin/env python3
"""
test_file_integrity_checker.py — Automated Unit Tests
======================================================
Tests for the File Integrity Checker tool.

These tests use Python's built-in 'unittest' framework — no external
packages are required. They test all the key functions in isolation
using temporary files and directories that are cleaned up after each test.

Run with:
    python3 tests/test_file_integrity_checker.py -v
"""

import json
import os
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Add the python_tool directory to the module search path so we can import
# file_integrity_checker without installing it as a package.
# ---------------------------------------------------------------------------
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_TOOL = os.path.join(REPO_ROOT, "python_tool")
sys.path.insert(0, PYTHON_TOOL)

import file_integrity_checker as fic   # The module we are testing


# ===========================================================================
# TestHashFile — tests for the hash_file() function
# ===========================================================================
class TestHashFile(unittest.TestCase):
    """Tests for the file hashing function."""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove temporary files after each test."""
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _write_file(self, name: str, content: str) -> str:
        """Helper: write content to a temp file and return its path."""
        path = os.path.join(self.tmp_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    # -----------------------------------------------------------------------
    def test_hash_returns_64_char_hex_string(self):
        """SHA-256 digest must be a 64-character lowercase hex string."""
        path = self._write_file("test.txt", "hello world")
        result = fic.hash_file(path)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_hash_known_value(self):
        """Verify hash against a known SHA-256 value for 'hello world'."""
        # Known SHA-256 of the exact string "hello world"
        KNOWN_HASH = "b94d27b9934d3e08a52e52d7da7dabfac484efe04294e576b8f63" \
                     "3a49bc5d6b"
        # Recalculate the known hash properly
        import hashlib
        known = hashlib.sha256(b"hello world").hexdigest()

        path = self._write_file("known.txt", "hello world")
        result = fic.hash_file(path)
        self.assertEqual(result, known)

    def test_different_content_different_hash(self):
        """Two files with different content must produce different hashes."""
        path1 = self._write_file("a.txt", "content A")
        path2 = self._write_file("b.txt", "content B")
        hash1 = fic.hash_file(path1)
        hash2 = fic.hash_file(path2)
        self.assertNotEqual(hash1, hash2)

    def test_same_content_same_hash(self):
        """Two files with identical content must produce the same hash."""
        path1 = self._write_file("x.txt", "identical content")
        path2 = self._write_file("y.txt", "identical content")
        hash1 = fic.hash_file(path1)
        hash2 = fic.hash_file(path2)
        self.assertEqual(hash1, hash2)

    def test_empty_file_returns_hash(self):
        """An empty file is valid and should return its SHA-256 hash."""
        path = self._write_file("empty.txt", "")
        result = fic.hash_file(path)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 64)

    def test_nonexistent_file_returns_none(self):
        """Attempting to hash a nonexistent file should return None."""
        path = os.path.join(self.tmp_dir, "does_not_exist.txt")
        result = fic.hash_file(path)
        self.assertIsNone(result)


# ===========================================================================
# TestScanDirectory — tests for scan_directory()
# ===========================================================================
class TestScanDirectory(unittest.TestCase):
    """Tests for the directory scanning function."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _write_file(self, rel_path: str, content: str) -> str:
        full = os.path.join(self.tmp_dir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)
        return full

    # -----------------------------------------------------------------------
    def test_scan_finds_top_level_files(self):
        """Scanner must find files in the top-level directory."""
        self._write_file("a.txt", "file a")
        self._write_file("b.txt", "file b")
        results = fic.scan_directory(self.tmp_dir)
        self.assertIn("a.txt", results)
        self.assertIn("b.txt", results)

    def test_scan_finds_nested_files(self):
        """Scanner must find files in subdirectories (recursive)."""
        self._write_file("sub/nested.txt", "nested content")
        results = fic.scan_directory(self.tmp_dir)
        self.assertIn(os.path.join("sub", "nested.txt"), results)

    def test_scan_empty_directory(self):
        """Scanning an empty directory should return an empty dict."""
        empty_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        results = fic.scan_directory(empty_dir)
        self.assertEqual(results, {})

    def test_scan_uses_relative_paths(self):
        """Stored paths must be relative to the scan root (not absolute)."""
        self._write_file("relative.txt", "content")
        results = fic.scan_directory(self.tmp_dir)
        for path in results.keys():
            self.assertFalse(os.path.isabs(path),
                             f"Expected relative path but got: {path}")

    def test_scan_returns_hashes(self):
        """Each entry must have a 64-character hex hash value."""
        self._write_file("c.txt", "some content")
        results = fic.scan_directory(self.tmp_dir)
        for path, digest in results.items():
            if digest != "UNREADABLE":
                self.assertEqual(len(digest), 64)


# ===========================================================================
# TestSaveAndLoadBaseline — tests for save_baseline() and load_baseline()
# ===========================================================================
class TestSaveAndLoadBaseline(unittest.TestCase):
    """Tests for saving and loading JSON baselines."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.baseline_path = os.path.join(self.tmp_dir, "baseline.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    def test_save_creates_file(self):
        """save_baseline() must create the output file."""
        hashes = {"file.txt": "abc123" * 10 + "abcd"}
        result = fic.save_baseline(hashes, self.baseline_path, self.tmp_dir)
        self.assertTrue(result)
        self.assertTrue(os.path.isfile(self.baseline_path))

    def test_save_and_load_round_trip(self):
        """Data saved with save_baseline() must be exactly recoverable."""
        import hashlib
        hashes = {
            "alpha.txt": hashlib.sha256(b"alpha").hexdigest(),
            "beta.txt":  hashlib.sha256(b"beta").hexdigest(),
        }
        fic.save_baseline(hashes, self.baseline_path, self.tmp_dir)
        loaded = fic.load_baseline(self.baseline_path)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["files"], hashes)

    def test_load_nonexistent_returns_none(self):
        """Loading a nonexistent baseline file should return None."""
        bad_path = os.path.join(self.tmp_dir, "no_such_file.json")
        result = fic.load_baseline(bad_path)
        self.assertIsNone(result)

    def test_load_invalid_json_returns_none(self):
        """Loading a file with invalid JSON content should return None."""
        with open(self.baseline_path, "w") as fh:
            fh.write("{ this is not valid json !!! }")
        result = fic.load_baseline(self.baseline_path)
        self.assertIsNone(result)

    def test_load_missing_files_key_returns_none(self):
        """A JSON file without the 'files' key should return None."""
        with open(self.baseline_path, "w") as fh:
            json.dump({"metadata": {}, "data": {}}, fh)
        result = fic.load_baseline(self.baseline_path)
        self.assertIsNone(result)

    def test_saved_baseline_has_metadata(self):
        """The saved JSON must include a 'metadata' section."""
        fic.save_baseline({}, self.baseline_path, self.tmp_dir)
        loaded = fic.load_baseline(self.baseline_path)
        self.assertIn("metadata", loaded)
        self.assertIn("created_at", loaded["metadata"])
        self.assertIn("tool",       loaded["metadata"])


# ===========================================================================
# TestCompareFiles — tests for compare_files()
# ===========================================================================
class TestCompareFiles(unittest.TestCase):
    """Tests for the file comparison logic."""

    def test_unchanged_file(self):
        """A file with the same hash in both sets must be 'unchanged'."""
        baseline = {"file.txt": "aabbcc" * 10 + "aabb"}
        current  = {"file.txt": "aabbcc" * 10 + "aabb"}
        result = fic.compare_files(baseline, current)
        self.assertIn("file.txt", result["unchanged"])
        self.assertEqual(len(result["modified"]), 0)

    def test_modified_file(self):
        """A file with a different hash must appear in 'modified'."""
        baseline = {"file.txt": "a" * 64}
        current  = {"file.txt": "b" * 64}
        result = fic.compare_files(baseline, current)
        self.assertEqual(len(result["modified"]), 1)
        self.assertEqual(result["modified"][0]["path"], "file.txt")
        self.assertEqual(result["modified"][0]["baseline_hash"], "a" * 64)
        self.assertEqual(result["modified"][0]["current_hash"],  "b" * 64)

    def test_new_file_detected(self):
        """A file present in the current scan but not the baseline is 'new'."""
        baseline = {}
        current  = {"new_file.txt": "c" * 64}
        result = fic.compare_files(baseline, current)
        self.assertIn("new_file.txt", result["new"])

    def test_missing_file_detected(self):
        """A file in the baseline but not the current scan is 'missing'."""
        baseline = {"deleted.txt": "d" * 64}
        current  = {}
        result = fic.compare_files(baseline, current)
        self.assertIn("deleted.txt", result["missing"])

    def test_all_categories_together(self):
        """Test all four categories in a single comparison."""
        baseline = {
            "unchanged.txt": "1" * 64,
            "modified.txt":  "2" * 64,
            "missing.txt":   "3" * 64,
        }
        current = {
            "unchanged.txt": "1" * 64,   # Same — should be unchanged
            "modified.txt":  "9" * 64,   # Different — should be modified
            "new_file.txt":  "4" * 64,   # Not in baseline — should be new
            # "missing.txt" not present  — should be missing
        }
        result = fic.compare_files(baseline, current)
        self.assertIn("unchanged.txt", result["unchanged"])
        self.assertEqual(result["modified"][0]["path"], "modified.txt")
        self.assertIn("new_file.txt",  result["new"])
        self.assertIn("missing.txt",   result["missing"])

    def test_empty_baseline_and_current(self):
        """Comparing two empty sets should produce no changes."""
        result = fic.compare_files({}, {})
        self.assertEqual(result["unchanged"], [])
        self.assertEqual(result["modified"],  [])
        self.assertEqual(result["new"],       [])
        self.assertEqual(result["missing"],   [])


# ===========================================================================
# TestEndToEnd — integration tests using real temp directories
# ===========================================================================
class TestEndToEnd(unittest.TestCase):
    """
    Integration tests: create real files, build a baseline, then check.
    These tests exercise the full workflow from start to finish.
    """

    def setUp(self):
        self.tmp_dir      = tempfile.mkdtemp()
        self.scan_dir     = os.path.join(self.tmp_dir, "scan_target")
        self.baseline_out = os.path.join(self.tmp_dir, "baseline.json")
        os.makedirs(self.scan_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _write(self, rel_path: str, content: str):
        """Write a file inside the scan directory."""
        full = os.path.join(self.scan_dir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)

    # -----------------------------------------------------------------------
    def test_no_changes_after_baseline(self):
        """
        After creating a baseline and scanning without changes,
        compare_files should find no modifications, no new files,
        and no missing files.
        """
        self._write("a.txt", "content A")
        self._write("b.txt", "content B")

        hashes = fic.scan_directory(self.scan_dir)
        fic.save_baseline(hashes, self.baseline_out, self.scan_dir)

        loaded      = fic.load_baseline(self.baseline_out)
        current     = fic.scan_directory(self.scan_dir)
        comparison  = fic.compare_files(loaded["files"], current)

        self.assertEqual(len(comparison["modified"]), 0)
        self.assertEqual(len(comparison["new"]),      0)
        self.assertEqual(len(comparison["missing"]),  0)

    def test_detects_modified_file(self):
        """After modifying a file, compare_files must detect it."""
        self._write("mod.txt", "original content")
        hashes = fic.scan_directory(self.scan_dir)
        fic.save_baseline(hashes, self.baseline_out, self.scan_dir)

        # Modify the file AFTER the baseline was saved
        self._write("mod.txt", "CHANGED content")

        loaded     = fic.load_baseline(self.baseline_out)
        current    = fic.scan_directory(self.scan_dir)
        comparison = fic.compare_files(loaded["files"], current)

        modified_paths = [m["path"] for m in comparison["modified"]]
        self.assertIn("mod.txt", modified_paths)

    def test_detects_new_file(self):
        """A file added after the baseline was saved must show as 'new'."""
        self._write("existing.txt", "exists from the start")
        hashes = fic.scan_directory(self.scan_dir)
        fic.save_baseline(hashes, self.baseline_out, self.scan_dir)

        # Add a new file AFTER the baseline
        self._write("added.txt", "I was added later")

        loaded     = fic.load_baseline(self.baseline_out)
        current    = fic.scan_directory(self.scan_dir)
        comparison = fic.compare_files(loaded["files"], current)

        self.assertIn("added.txt", comparison["new"])

    def test_detects_deleted_file(self):
        """A file deleted after the baseline was saved must show as 'missing'."""
        self._write("will_be_deleted.txt", "temporary content")
        hashes = fic.scan_directory(self.scan_dir)
        fic.save_baseline(hashes, self.baseline_out, self.scan_dir)

        # Delete the file AFTER the baseline
        os.remove(os.path.join(self.scan_dir, "will_be_deleted.txt"))

        loaded     = fic.load_baseline(self.baseline_out)
        current    = fic.scan_directory(self.scan_dir)
        comparison = fic.compare_files(loaded["files"], current)

        self.assertIn("will_be_deleted.txt", comparison["missing"])


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    # verbose=2 prints each test name and result on its own line
    unittest.main(verbosity=2)
