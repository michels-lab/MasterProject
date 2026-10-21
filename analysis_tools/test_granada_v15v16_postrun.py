"""Synthetic regression tests for a read-only V15/V16 evidence package."""
import json
from pathlib import Path
import tempfile
import unittest
from granada_v15v16_postrun import (PAIRS, read_series, temperature_metrics,
                                     inspect_case, run, main)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cases = self.root/'cases_controlled_buoyancy'
        for case in sorted(set(sum(([a,b] for a,b in PAIRS), []))):
            folder = self.cases/case
            for sub in ['postProcessing/metal/temperatureProbe/0', 'logs', 'system']:
                (folder/sub).mkdir(parents=True, exist_ok=True)
            (folder/'postProcessing/metal/temperatureProbe/0/T').write_text('# Probe 0\n0 1500\n0.01 1499\n0.02 1498\n')
            (folder/'logs/CourantMax_0').write_text('0.01s 0.10\n0.02s 0.20\n')
            (folder/'logs/contCumulative_0').write_text('0.01s -0.001\n0.02s -0.002\n')
            (folder/'system/controlDict').write_text('// maxCo 999;\nmaxCo 0.25;\n')

    def test_four_comparable_pairs_and_non_destructive_exports(self):
        report = run(self.root)
        self.assertEqual(len(report['comparisons']), 4)
        self.assertEqual(report['comparisons'][0]['metrics']['rmse_K'], 0)
        self.assertEqual(report['verification'], 'NOT_PHYSICALLY_OR_EXPERIMENTALLY_VALIDATED')
        out = self.root/'report'
        self.assertEqual(main(['--root', str(self.root), '--out', str(out), '--strict']), 0)
        self.assertTrue((out/'evidence.json').exists())
        self.assertTrue((out/'pair_metrics.csv').exists())
        self.assertEqual(json.loads((out/'evidence.json').read_text())['format'], 'quickcup-foamlens-openfoam-evidence-v1')

    def test_courant_overshoot_detected(self):
        case = self.cases/PAIRS[0][1]
        (case/'logs/CourantMax_0').write_text('0.01s 0.2\n0.02s 0.255\n')
        info = inspect_case(case)
        self.assertEqual(info['courant_over_limit_count'], 1)
        self.assertIn('exceeds', ' '.join(info['alerts']))

    def test_missing_file_is_unknown_not_zero(self):
        case = self.cases/PAIRS[1][1]
        (case/'postProcessing/metal/temperatureProbe/0/T').unlink()
        report = run(self.root)
        self.assertIsNone(next(x for x in report['cases'] if x['case']==case.name)['source_files']['probe_T'])
        self.assertIsNone(report['comparisons'][1]['metrics'])

    def test_out_of_order_and_ambiguous_multi_probe_fail_closed(self):
        p = self.cases/PAIRS[0][0]/'postProcessing/metal/temperatureProbe/0/T'
        p.write_text('0 1500\n0.02 1498\n0.01 1499\n')
        with self.assertRaisesRegex(ValueError, 'out-of-order'):
            read_series(p)
        p.write_text('0 1500 1400\n')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            read_series(p)

    def test_foamlog_courant_initial_seed_marker_only(self):
        p = self.cases/PAIRS[0][0]/'logs/CourantMax_0'
        p.write_text('0\n0.01s 0.15\n0.02s 0.2\n')
        self.assertEqual(len(read_series(p)), 2)
        p.write_text('0\n0\n0.01s 0.15\n')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            read_series(p)

    def test_no_extrapolation_and_original_case_write_protection(self):
        with self.assertRaisesRegex(ValueError, 'insufficient'):
            temperature_metrics([(0, 1), (0.001, 1)], [(1, 2), (1.001, 2)])
        out = self.cases/PAIRS[0][0]/'output'
        with self.assertRaises(SystemExit):
            main(['--root', str(self.root), '--out', str(out)])


if __name__ == '__main__':
    unittest.main()
