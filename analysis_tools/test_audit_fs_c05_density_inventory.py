"""FS-C05 mixture mass inventory native-rho reader; no CFD in CI."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from audit_fs_c05_density_inventory import (
    read_native_rho, phase_inventory, audit_density_inventory,
)


def write_rho(path:Path,vals:list[float],dims="[1 -3 0 0 0 0 0]"):
    path.parent.mkdir(parents=True,exist_ok=True)
    internal=("nonuniform List<scalar> "+str(len(vals))+
              "\n(\n"+"\n".join(str(x) for x in vals)+"\n)\n")
    path.write_text(
        "FoamFile {version 2.0; format ascii; class volScalarField;"
        " object rho;}\n"
        "dimensions "+dims+";\n"
        "internalField "+internal+";\n"
        "boundaryField {}\n"
    )


class RealRhoParsers(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="fs-c05-rho-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.case=self.root/"FS_C05_WALL_Q_PROBE_fixture"
        self.case.mkdir()
        for stamp in ("0","1e-07","2e-07"):
            (self.case/stamp).mkdir()

    def test_correct_dimensions_and_rho_native_cell_read(self):
        file=self.case/"1e-07/fluid/rho"
        write_rho(file,[6820.,1.16,1.17])
        self.assertEqual(read_native_rho(file,3),[6820.,1.16,1.17])

    def test_reject_wrong_density_dimensions(self):
        file=self.case/"1e-07/fluid/rho"
        write_rho(file,[6820.,1.16],dims="[0 0 0 1 0 0 0]")
        with self.assertRaisesRegex(ValueError,"SI kg/m3"):
            read_native_rho(file,2)

    def test_reject_wrong_density_cell_count(self):
        file=self.case/"1e-07/fluid/rho"
        write_rho(file,[6820.,1.16])
        with self.assertRaisesRegex(ValueError,"cell list"):
            read_native_rho(file,3)

    def test_reject_rho_negative_or_nan(self):
        file=self.case/"1e-07/fluid/rho"
        write_rho(file,[6820.,float("nan")])
        with self.assertRaisesRegex(ValueError,"strictly positive"):
            read_native_rho(file,2)

    def test_inventory_calculates_true_mixture_mass_and_separate_gas_residual(self):
        data=phase_inventory([2.,3.,5.],[1.,0.5,0.],
                             [6820.,(0.5*6820.+0.5*1.2),1.2])
        self.assertAlmostEqual(data["iron_volume_m3"],3.5)
        self.assertAlmostEqual(data["iron_mass_kg_ASSUMING_CONSTANT_IRON_RHO"],
                               3.5*6820.)
        self.assertAlmostEqual(data["air_mass_kg_AS_RESIDUAL_OF_MIXTURE_RHO"],
                               6.5*1.2,places=8)
        self.assertFalse(data["mass_conservation_validated"])

    def test_inventory_rejects_impossible_negative_air_mass(self):
        with self.assertRaisesRegex(ValueError,"positive gas inventory"):
            phase_inventory([1.,1.],[1.,0.],[4000.,1.])

    def test_missing_both_native_rho_gives_explicit_not_measured(self):
        x=audit_density_inventory(self.case)
        self.assertEqual(x["status"],
                         "NATIVE_RHO_NOT_WRITTEN_AT_BOTH_STEPS_NO_MASS_CLOSURE")
        self.assertFalse(x["native_density_inventory_observed"])
        self.assertFalse(x["mass_conservation_validated"])

    def test_missing_one_native_rho_field_does_not_emit_partial_success(self):
        write_rho(self.case/"1e-07/fluid/rho",[1.])
        with self.assertRaisesRegex(ValueError,"only one"):
            audit_density_inventory(self.case)


if __name__=="__main__":
    unittest.main()
