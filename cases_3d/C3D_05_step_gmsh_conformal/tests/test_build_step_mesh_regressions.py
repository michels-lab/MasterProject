#!/usr/bin/env python3
"""Regression: preserve callable CAD helpers when adding mesh branch locals.

The original HEX8 pilot failed at the very first STEP import with
UnboundLocalError: local variable volume_tags shadows top-level function.
These tests are Gmsh-free, fast, and must run before any expensive mesh.
"""
import ast
import importlib.util
from pathlib import Path
import symtable
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "build_step_mesh.py"


class CADMeshNameResolutionRegression(unittest.TestCase):
    def test_global_cad_functions_must_not_be_shadowed_in_main(self):
        source = SOURCE.read_text(encoding="utf-8")
        module_tree = ast.parse(source, filename=str(SOURCE))
        helpers = {
            node.name
            for node in module_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name != "main"
        }
        module_symbols = symtable.symtable(source, str(SOURCE), "exec")
        mains = [
            child for child in module_symbols.get_children()
            if child.get_name() == "main"
        ]
        self.assertEqual(len(mains), 1)
        main = mains[0]
        for name in ("volume_tags", "sha256", "relative_error"):
            self.assertIn(name, helpers)
            symbol = main.lookup(name)
            self.assertTrue(
                symbol.is_referenced(),
                f"CAD helper {name} is no longer referenced by main()",
            )
            self.assertTrue(
                symbol.is_global() and not symbol.is_local(),
                f"Regression: main() shadows global CAD helper {name} "
                "with a local assignment, causing UnboundLocalError",
            )

    def test_volume_tags_helper_is_callable_before_gmsh(self):
        spec = importlib.util.spec_from_file_location("c3d05_source_regression", SOURCE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.volume_tags([(2, 1), (3, 9)], "metal"), [(3, 9)])
        with self.assertRaisesRegex(ValueError, "exactly ONE CLOSED CAD solid"):
            module.volume_tags([(2, 1)], "mold")
        with self.assertRaisesRegex(ValueError, "exactly ONE CLOSED CAD solid"):
            module.volume_tags([(3, 1), (3, 2)], "metal")


if __name__ == "__main__":
    unittest.main()
