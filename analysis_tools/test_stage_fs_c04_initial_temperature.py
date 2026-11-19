"""FS-C04 initial screening T-only staging; 0 CFD/OpenFOAM in unit tests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from audit_fs_c02_local import read_alpha, read_temperature
from stage_fs_c04_initial_alpha import make_alpha
from stage_fs_c04_initial_temperature import (
    stage, guard_paths, check_T, create_T, fluid_thermal_values,
    T_METAL_K,T_AIR_K,T_MOLD_K,EXPECTED_AREAS_CM2,
    FLUID_PATCHES,MOLD_PATCHES,FLUID_CELLS,SAND_CELLS,
    METAL_CELLS,GAS_CELLS,
)

ALPHA=[1.]*METAL_CELLS+[0.]*GAS_CELLS


def boundary(names:list[str],*,fluid:bool)->str:
    text=["FoamFile { version 2.0; format ascii; class polyBoundaryMesh; }",
          str(len(names)),"("]
    for name in names:
        if fluid:
            wall=name=="fluid_to_mold"
            typ="mappedWall" if wall else "patch"
            neighbor=("    neighbourRegion mold;\n"
                      "    neighbourPatch mold_to_fluid;\n") if wall else ""
        else:
            wall=name=="mold_to_fluid"
            typ="mappedWall" if wall else "wall"
            neighbor=("    neighbourRegion fluid;\n"
                      "    neighbourPatch fluid_to_mold;\n") if wall else ""
        text.extend([name,"{",
                     "    type "+typ+";",
                     "    nFaces "+str((3136 if wall else {"atmosphereTop":448,"atmosphereSides":3040,"atmosphereLowerSides":256}.get(name,0)) if fluid else 0)+";",
                     "    startFace 0;",
                     *neighbor.splitlines(),
                     "}"])
    return "\n".join(text+[")"])+"\n"


class TemperatureStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c04-initial-T-")
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.src=root/"FS_C04_ALPHA_NATIVE_CHECK_synthetic"
        self.out=root/"FS_C04_T_INITIAL_STAGE_synthetic"
        (self.src/"0/fluid").mkdir(parents=True)
        (self.src/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json").write_text(
            '{"status":"NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD"}\n')
        alpha_text=make_alpha(ALPHA,{
            "fluid_to_mold":{"type":"mappedWall"},
            "atmosphereTop":{"type":"patch"},
            "atmosphereSides":{"type":"patch"},
            "atmosphereLowerSides":{"type":"patch"},
        })
        (self.src/"0/fluid/alpha.metal").write_text(alpha_text)
        for region,patches in (
            ("fluid",sorted(FLUID_PATCHES)),
            ("mold",sorted(MOLD_PATCHES)),
        ):
            mesh=self.src/"constant"/region/"polyMesh"
            mesh.mkdir(parents=True)
            for name in ("points","faces","owner","neighbour"):
                (mesh/name).write_text(f"FoamFile {{ format ascii; }}\n{region}-{name}\n")
            (mesh/"boundary").write_text(boundary(patches,fluid=(region=="fluid")))
        self.mock_audit={
            "status":"RECIPROCAL_THERMAL_CONTACT_GEOMETRY_VERIFIED_NO_CHT",
            "interface":{
                "interface_face_count":3136,
                "areas_by_initial_contact":{
                    k:{"area_cm2":v} for k,v in EXPECTED_AREAS_CM2.items()
                },
            },
        }

    def test_strict_phase_to_temperature_mapping(self):
        vals=fluid_thermal_values(ALPHA)
        self.assertEqual(len(vals),FLUID_CELLS)
        self.assertEqual(vals[:METAL_CELLS],[1500.]*METAL_CELLS)
        self.assertEqual(vals[METAL_CELLS:],[300.]*GAS_CELLS)
        self.assertEqual(sum(x==1500 for x in vals),METAL_CELLS)
        self.assertEqual(T_METAL_K,1500)
        self.assertEqual(T_AIR_K,300)
        self.assertEqual(T_MOLD_K,300)

    def test_wrong_phase_mask_rejected_even_if_length_ok(self):
        bad=ALPHA.copy()
        bad[0]=0.
        bad[-1]=1.
        self.assertEqual(sum(bad),METAL_CELLS)
        # This tool is deliberately aligned with the accepted alpha field,
        # not random metal order; stage() sources that alpha from audit.
        with self.assertRaisesRegex(ValueError,"invalid fluid alpha length"):
            fluid_thermal_values(ALPHA[:-1])
        bad[0]=.5
        with self.assertRaisesRegex(ValueError,"initial binary"):
            fluid_thermal_values(bad)

    def test_fluid_temperature_file_readback_and_absolute_kelvin_dimension(self):
        content=create_T(fluid_thermal_values(ALPHA),"fluid",FLUID_PATCHES)
        field=Path(self.tmp.name)/"T.fluid"
        field.write_text(content)
        result=check_T(field,"fluid",ALPHA)
        self.assertEqual(result["cells"],34368)
        self.assertEqual(result["min_T_K"],300)
        self.assertEqual(result["max_T_K"],1500)
        self.assertTrue(result["non_solving_boundary_placeholders"])
        self.assertEqual(read_temperature(field,expected_cells=34368)[0],1500)
        self.assertEqual(content.count("type calculated;"),4)
        self.assertNotIn("coupledTemperature;",content)
        self.assertNotIn("fixedValue;",content)

    def test_solid_temperature_file_is_uniform_300_with_four_placeholders(self):
        content=create_T([300.]*SAND_CELLS,"mold",MOLD_PATCHES)
        field=Path(self.tmp.name)/"T.mold"
        field.write_text(content)
        result=check_T(field,"mold")
        self.assertEqual(result["cells"],7680)
        self.assertEqual(result["min_T_K"],300)
        self.assertEqual(result["max_T_K"],300)
        self.assertEqual(read_temperature(field,expected_cells=7680)[-1],300)
        self.assertEqual(content.count("type calculated;"),4)

    def test_wrong_field_dimensions_fail(self):
        field=Path(self.tmp.name)/"T.fluid"
        field.write_text(create_T(fluid_thermal_values(ALPHA),"fluid",
                                  FLUID_PATCHES).replace(
                                      "[0 0 0 1 0 0 0]","[0 0 0 0 0 0 0]"))
        with self.assertRaisesRegex(ValueError,"absolute temperature"):
            check_T(field,"fluid",ALPHA)

    def test_fake_solver_thermal_bc_rejected_even_if_readable(self):
        field=Path(self.tmp.name)/"T.fluid"
        field.write_text(create_T(fluid_thermal_values(ALPHA),"fluid",
                                  FLUID_PATCHES).replace("type calculated;",
                                                        "type fixedValue;",1))
        with self.assertRaisesRegex(ValueError,"non-placeholder"):
            check_T(field,"fluid",ALPHA)

    def test_wrong_T_metal_assignment_detected_even_same_mean(self):
        field=Path(self.tmp.name)/"T.fluid"
        swapped=fluid_thermal_values(ALPHA)
        swapped[0]=300.
        swapped[-1]=1500.
        self.assertAlmostEqual(sum(swapped),sum(fluid_thermal_values(ALPHA)))
        field.write_text(create_T(swapped,"fluid",FLUID_PATCHES))
        with self.assertRaisesRegex(ValueError,"not aligned"):
            check_T(field,"fluid",ALPHA)

    def test_read_only_source_and_new_copy_with_both_thermal_fields(self):
        before={p.relative_to(self.src):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.rglob("*") if p.is_file()}
        with patch("stage_fs_c04_initial_temperature.audit_contacts",
                   return_value=self.mock_audit):
            record=stage(self.src,self.out)
        self.assertEqual(record["status"],"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT")
        self.assertTrue((self.out/"0/fluid/T").exists())
        self.assertTrue((self.out/"0/mold/T").exists())
        self.assertFalse((self.src/"0/fluid/T").exists())
        self.assertFalse((self.src/"0/mold/T").exists())
        self.assertFalse(record["T_boundary_conditions_valid_for_solver"])
        self.assertFalse(record["native_OpenFOAM_T_read_verified"])
        self.assertFalse(record["CFD_executed"])
        self.assertFalse(record["CTH_or_VOF_solver_executed"])
        self.assertEqual(record["phase_cell_counts"],
                         {"metal":2368,"air":32000,"sand":7680})
        after={p.relative_to(self.src):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in self.src.rglob("*") if p.is_file()}
        self.assertEqual(before,after)

    def test_reject_missing_measured_interface_areas(self):
        broken={"status":self.mock_audit["status"],
                "interface":{"interface_face_count":3136,
                             "areas_by_initial_contact":{
                                k:{"area_cm2":v+0.1}
                                for k,v in EXPECTED_AREAS_CM2.items()}}}
        with patch("stage_fs_c04_initial_temperature.audit_contacts",
                   return_value=broken):
            with self.assertRaisesRegex(ValueError,"audit or measured areas"):
                stage(self.src,self.out)
        self.assertFalse(self.out.exists())

    def test_no_overwrite_even_if_existing_case_empty(self):
        self.out.mkdir()
        with self.assertRaisesRegex(ValueError,"refusing overwrite"):
            guard_paths(self.src,self.out)

    def test_reject_symlinked_source_before_copy(self):
        (self.src/"trap").symlink_to(self.src/"nonexistent")
        with patch("stage_fs_c04_initial_temperature.audit_contacts",
                   return_value=self.mock_audit):
            with self.assertRaisesRegex(ValueError,"symlink"):
                stage(self.src,self.out)
        self.assertFalse(self.out.exists())

    def test_non_model_control_inputs_are_not_installed(self):
        with patch("stage_fs_c04_initial_temperature.audit_contacts",
                   return_value=self.mock_audit):
            stage(self.src,self.out)
        for path in ("0/fluid/U","0/fluid/p_rgh",
                     "0/mold/alpha.metal","constant/fluid/physicalProperties"):
            self.assertFalse((self.out/path).exists())


if __name__=="__main__":
    unittest.main()
