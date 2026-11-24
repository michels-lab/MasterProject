"""FS-C08 conservative FV ledger tests: all properties strictly synthetic, NO CFD."""
import json
import math
from pathlib import Path
import tempfile
import unittest

import fs_c08_conservative_reference as m


def curve(v0,v1=None):
    return m.Curve(((200.,float(v0)),(2000.,float(v0 if v1 is None else v1))))


def material(*,variable_density=False,variable_cp=False):
    return m.Thermo(
        rho_liquid=curve(7000,6900 if variable_density else None),
        rho_solid=curve(7300,7200 if variable_density else None),
        cp_liquid=curve(600,800 if variable_cp else None),
        cp_solid=curve(550,680 if variable_cp else None),
        cp_gas=curve(700,800 if variable_cp else None),
        latent_liquid_minus_solid_J_kg=200000,
        gas_R_J_kg_K=287,
        T_reference_K=300,
        provenance="SYNTHETIC_UNIT_TEST_NOT_JMATPRO",
    )


def cells(th=None):
    th=th or material()
    temp=1400.
    ml=0.042
    V=ml/th.density("liquid",temp)+4e-6
    return (m.Cell(V,ml,0.,1e-6,temp),)


def check(res,*,atol=1e-8):
    a=res["audit"]
    for p,v in a["phase_mass_residual_kg"].items():
        if not abs(v)<atol:raise AssertionError((p,v))
    if not abs(a["metal_mass_residual_kg"])<atol:
        raise AssertionError(a["metal_mass_residual_kg"])
    if not abs(a["global_energy_residual_J"])<atol:
        raise AssertionError(a["global_energy_residual_J"])


class ConservativeControlVolume(unittest.TestCase):
    def test_isolated_adiabatic_solidification_conserves_total_mass_energy(self):
        th=material()
        before=cells(th)
        dt=0.1
        gamma=210.
        result=m.advance(before,th,m.Step(dt,(gamma,)))
        check(result)
        after=result["cells"][0]
        self.assertAlmostEqual(after.m_liquid_kg,before[0].m_liquid_kg-gamma*before[0].V_m3*dt)
        self.assertAlmostEqual(after.m_solid_kg,gamma*before[0].V_m3*dt)
        self.assertGreater(after.T_K,before[0].T_K)  # latent to sensible enthalpy
        self.assertLess(result["audit"]["geometric_metal_volume_delta_m3"],0)
        self.assertGreater(result["diagnostics"][0].V_gas_m3,m.geometry(before[0],th).V_gas_m3)
        self.assertLess(result["diagnostics"][0].pressure_gas_Pa,m.geometry(before[0],th).pressure_gas_Pa*1.01)
        exact=gamma*before[0].V_m3*dt*(1/7300-1/7000)
        self.assertAlmostEqual(result["audit"]["constant_initial_T_conversion_only_volume_delta_m3"],exact,places=17)
        self.assertFalse(result["audit"]["is_full_OpenFOAM_3D_CFD_solver"])

    def test_melting_gamma_negative_conserves_energy_and_swells_metal(self):
        th=material()
        c=m.Cell(1e-5,0.012,0.025,2e-6,1350.)
        result=m.advance((c,),th,m.Step(0.1,(-100.,)))
        check(result)
        self.assertGreater(result["audit"]["geometric_metal_volume_delta_m3"],0)
        self.assertLess(result["cells"][0].T_K,c.T_K)
        self.assertAlmostEqual(result["audit"]["solidification_mass_liquid_to_solid_kg"],-1e-4)

    def test_FV_internal_liquid_and_gas_advection_energy_equal_opposite(self):
        th=material()
        c1=m.Cell(1e-5,0.028,0.0,2e-6,1500.)
        c2=m.Cell(1e-5,0.014,0.0,2e-6,1300.)
        result=m.advance((c1,c2),th,m.Step(
            0.1,(0,0),
            faces=(m.Face(0,1,liquid_kg_s=0.0008,gas_kg_s=-0.000001,heat_W=5.),)
        ))
        check(result)
        self.assertAlmostEqual(sum(c.m_liquid_kg for c in result["cells"]),0.042)
        self.assertAlmostEqual(sum(c.m_gas_kg for c in result["cells"]),4e-6)
        self.assertGreater(result["cells"][1].T_K,c2.T_K)
        self.assertLess(result["cells"][0].T_K,c1.T_K)

    def test_open_boundary_liquid_outflow_keeps_global_metal_balance(self):
        th=material()
        c=cells(th)[0]
        result=m.advance((c,),th,m.Step(
            0.1,(20.,),boundaries=(m.Boundary(0,"liquid",0.001),)
        ))
        check(result)
        a=result["audit"]
        self.assertAlmostEqual(a["outward_boundary_mass_kg"]["liquid"],1e-4)
        self.assertAlmostEqual(a["metal_mass_residual_kg"],0.,places=14)
        self.assertAlmostEqual(a["global_energy_residual_J"],0.,places=8)

    def test_open_boundary_gas_inflow_requires_energy_temperature(self):
        th=material()
        c=cells(th)[0]
        with self.assertRaisesRegex(ValueError,"inflow requires"):
            m.advance((c,),th,m.Step(.1,(0.,),boundaries=(m.Boundary(0,"gas",-1e-7),)))
        result=m.advance((c,),th,m.Step(.1,(0.,),boundaries=(m.Boundary(0,"gas",-1e-7,300.),)))
        check(result)
        self.assertAlmostEqual(result["cells"][0].m_gas_kg,1e-6+1e-8)

    def test_variable_cp_rho_and_latent_enthalpy_inversion(self):
        th=material(variable_density=True,variable_cp=True)
        c=cells(th)[0]
        result=m.advance((c,),th,m.Step(.1,(200.,),external_heat_W=(-15.,)))
        check(result,atol=2e-7)
        self.assertGreater(result["cells"][0].T_K,200.)
        self.assertAlmostEqual(m.geometry(result["cells"][0],th).E_J,
                               result["audit"]["global_energy_final_J"])
        self.assertNotAlmostEqual(th.rho_liquid.at(1400),th.rho_liquid.at(1500))
        self.assertNotAlmostEqual(th.cp_liquid.at(1400),th.cp_liquid.at(1500))

    def test_tabulation_no_extrapolation(self):
        p=curve(600,800)
        self.assertAlmostEqual(p.at(1100),700)
        self.assertAlmostEqual(p.integral(200,2000),700*1800)
        self.assertAlmostEqual(p.integral(2000,200),-700*1800)
        with self.assertRaisesRegex(ValueError,"outside property curve"):
            p.at(100)
        with self.assertRaisesRegex(ValueError,"outside property curve"):
            p.integral(180,300)

    def test_negative_gamma_or_flux_cannot_overdraw_a_phase(self):
        th=material()
        c=cells(th)[0]
        for step in (m.Step(1.,(1e9,)),m.Step(1.,(-1e9,)),
                     m.Step(1.,(0.,),boundaries=(m.Boundary(0,"liquid",1.0),))):
            with self.subTest(step=step),self.assertRaisesRegex(ValueError,"Negative"):
                m.advance((c,),th,step)

    def test_bad_temperature_from_energy_raises_instead_of_extrapolating(self):
        th=material()
        c=cells(th)[0]
        with self.assertRaisesRegex(ValueError,"Enthalpy outside"):
            m.advance((c,),th,m.Step(1.,(0.,),external_heat_W=(1e9,)))

    def test_overfilled_cell_is_rejected_even_if_masses_conserved(self):
        th=material()
        c=m.Cell(1e-5,0.07,0.,0.,1400.)
        # exactly full, import more metal without exporting anything
        with self.assertRaisesRegex(ValueError,"overfill"):
            m.advance((c,),th,m.Step(.1,(0.,),boundaries=(m.Boundary(0,"liquid",-0.0001,1400.),)))

    def test_solid_internal_face_is_allowed_and_conserves_solid_mass(self):
        th=material()
        c1=m.Cell(1e-5,0.01,0.02,1e-6,1450.)
        c2=m.Cell(1e-5,0.01,0.02,1e-6,1350.)
        result=m.advance((c1,c2),th,m.Step(.1,(0.,0.),faces=(m.Face(0,1,solid_kg_s=0.0001),)))
        check(result)
        self.assertAlmostEqual(result["cells"][0].m_solid_kg,0.01999)

    def test_synthetic_scenario_load_and_cli_json_is_explicitly_unvalidated(self):
        case=(Path(__file__).resolve().parents[1] / "freesurface/FS-C08_conservative_phase_mass/fixtures/SYNTHETIC_TWO_CELL_REFERENCE.json")
        th,cs,step,doc=m.load_scenario(case)
        result=m.printable(m.advance(cs,th,step),doc)
        self.assertEqual(result["case_purpose"],"SYNTHETIC_TEST_ONLY")
        self.assertFalse(result["physical_3d_shrinkage_validated"])
        self.assertFalse(result["openfoam_14_solver_executed"])
        self.assertEqual(len(result["result_cells"]),2)
        with tempfile.TemporaryDirectory() as tmp:
            invalid=Path(tmp)/"sc.json"
            payload=json.loads(case.read_text())
            payload["provenance"]="JMatPro"  # false lab provenance forbidden
            invalid.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"pretend JMatPro"):
                m.load_scenario(invalid)


if __name__=="__main__":
    unittest.main()
