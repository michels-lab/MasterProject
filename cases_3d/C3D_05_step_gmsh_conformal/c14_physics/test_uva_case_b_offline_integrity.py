"""Synthetic regressions only: no OpenFOAM, no CFD, no original case."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "offline", Path(__file__).with_name("POSTPROCESAR_CASO_B_C14_EXISTENTE.py"))
offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offline)


class OfflineIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.work = self.root / "work"

    def test_independent_output(self):
        self.assertEqual(offline.checked_paths(self.source, self.work),
                         (self.source.resolve(), self.work.resolve()))

    def test_same_tree(self):
        for output in (self.source, self.source / "nested", self.root):
            with self.subTest(output=output), self.assertRaises(ValueError):
                offline.checked_paths(self.source, output)

    def test_parent_alias(self):
        alias = self.root / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            offline.checked_paths(self.source, alias / "nested")

    def test_direct_output_alias(self):
        self.work.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            offline.checked_paths(self.source, self.work)

    def test_nested_and_dangling_links(self):
        self.work.mkdir()
        (self.work / "dangling").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            offline.reject_links(self.work)

    def test_native_done_without_log(self):
        self.work.mkdir()
        (self.work / "log.C14B.test.DONE").touch()
        with self.assertRaises(ValueError):
            offline.native(self.work, "test", "unused", "0:10", ())

    def test_foamlog_done_without_log(self):
        self.work.mkdir()
        (self.work / "log.C14B.foamLog.DONE").touch()
        with self.assertRaises(ValueError):
            offline.run_foam_log(self.work)

    def test_native_previous_log(self):
        self.work.mkdir()
        (self.work / "log.C14B.test.DONE").touch()
        (self.work / "log.C14B.test").write_text("native output\n")
        self.assertEqual(offline.native(self.work, "test", "unused", "0:10", ())["result"],
                         "PREVIOUSLY_COMPLETED")


if __name__ == "__main__":
    unittest.main()
