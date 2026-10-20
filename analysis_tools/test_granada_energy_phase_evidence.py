"""Synthetic source-format and scientific-integrity regression tests; no CFD."""
from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
from granada_energy_phase_evidence import CASE_PAIRS, FIELDS, analyze, inspect_case, main, read_data, trapezoid


def fixture_file(case, name, times=(0, 0.1, 0.2)):
    folder, filename, header = FIELDS[name]
    p=case/'postProcessing'/'metal'/folder/'0'/filename
    p.parent.mkdir(parents=True, exist_ok=True)
    values=[]
    for t in times:
        if name=='alphaL': v=[1-t*0.1]
        elif name=='latent_W': v=[10+t]
        elif name=='sensible_J': v=[1000-100*t]
        elif name=='top_W': v=[0, 20, 20]
        elif name=='mold_W': v=[0, 80, 80]
        else: v=[0, 100, 100]
        values.append(' '.join(str(x) for x in [t]+v))
    p.write_text('# Selection : all\n# Time\t'+ '\t'.join(header)+'\n'+'\n'.join(values)+'\n')
    return p


class EnergyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.cases={}
        for case in sorted(set(n for pair in CASE_PAIRS for n in pair)):
            base=self.root/'cases_controlled_buoyancy'/case
            self.cases[case]=base
            for name in FIELDS:
                fixture_file(base,name)

    def test_all_six_cases_and_four_controlled_pairs(self):
        data=analyze(self.root)
        self.assertEqual(len(data['cases']),6)
        self.assertEqual(len(data['paired_comparisons']),4)
        self.assertTrue(all(c['status']=='NUMERIC_SCREEN_PASSED' for c in data['cases']))
        self.assertAlmostEqual(data['cases'][0]['metrics']['integrated_boundary_total_J'],20)
        self.assertAlmostEqual(data['cases'][0]['metrics']['conditional_energy_residual_J'],-2.02,places=5)
        self.assertTrue(all(p['status']=='NUMERIC_COMPARISON_ONLY' for p in data['paired_comparisons']))

    def test_export_and_repeated_export_blocked(self):
        out=self.root/'report'
        self.assertEqual(main(['--root',str(self.root),'--out',str(out),'--strict']),0)
        self.assertTrue((out/'summary.md').is_file())
        self.assertTrue((out/'energy_phase_evidence.json').is_file())
        with self.assertRaises(SystemExit):
            main(['--root',str(self.root),'--out',str(out)])

    def test_missing_source_is_not_zero_or_success(self):
        p=fixture_file(self.cases[CASE_PAIRS[0][1]],'latent_W')
        p.unlink()
        case=inspect_case(self.cases[CASE_PAIRS[0][1]])
        self.assertIsNone(case['metrics'])
        self.assertIsNone(case['sources']['latent_W'])
        self.assertEqual(case['status'],'INCOMPLETE')

    def test_header_mismatch_and_monotonicity_rejected(self):
        p=fixture_file(self.cases[CASE_PAIRS[0][1]],'alphaL')
        s=p.read_text().replace('volAverage(phaseChangeSource:alpha1)','volAverage(someOtherField)')
        p.write_text(s)
        self.assertRaisesRegex(ValueError, 'unexpected column', read_data, p, FIELDS['alphaL'][2])
        fixture_file(self.cases[CASE_PAIRS[0][1]],'alphaL',times=(0,0.2,0.1))
        self.assertRaisesRegex(ValueError, 'nonmonotonic', read_data, p, FIELDS['alphaL'][2])

    def test_double_counting_and_boundary_mismatch_alert(self):
        p=fixture_file(self.cases[CASE_PAIRS[0][1]],'boundary_W')
        p.write_text(p.read_text().replace('0.1 0 100 100', '0.1 0 100 200'))
        c=inspect_case(self.cases[CASE_PAIRS[0][1]])
        self.assertEqual(c['status'],'REVIEW')
        self.assertIn('energyFlux != advective+heatFlux',' '.join(c['alerts']))
        self.assertIn('boundary != top+mold',' '.join(c['alerts']))

    def test_time_alignment_has_no_fabrication(self):
        fixture_file(self.cases[CASE_PAIRS[0][1]],'latent_W',times=(0,0.15,0.2))
        c=inspect_case(self.cases[CASE_PAIRS[0][1]])
        self.assertIn('unmatched physical timestamps',' '.join(c['alerts']))
        self.assertEqual(c['metrics']['shared_sample_count'],2)
        self.assertEqual(c['status'],'REVIEW')

    def test_alpha_bounds(self):
        p=fixture_file(self.cases[CASE_PAIRS[0][1]],'alphaL')
        p.write_text(p.read_text().replace('0.1 0.99', '0.1 1.5'))
        self.assertIn('outside nominal',' '.join(inspect_case(self.cases[CASE_PAIRS[0][1]])['alerts']))

    def test_no_output_into_cases(self):
        with self.assertRaises(SystemExit):
            main(['--root',str(self.root),'--out',str(self.cases[CASE_PAIRS[0][0]]/'report')])

    def test_trapezoid_signed_and_nonuniform(self):
        self.assertAlmostEqual(trapezoid([(0,2),(1,0),(3,-2)],1),-1)


if __name__=='__main__':
    unittest.main()
