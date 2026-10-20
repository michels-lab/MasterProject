#!/usr/bin/env python3
"""Read-only phase/energy evidence from original QuickCup OpenFOAM postProcessing.

Diagnostic arithmetic only; no CFD runs and NO proof of physical energy closure.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

CASE_PAIRS = (
    ('B14_topFixedFlux_explicitRef', 'B15_adaptiveDt_fromB14'),
    ('C14_topFixedFlux_explicitRef', 'C15_adaptiveDt_fromC14'),
    ('B14_topFixedFlux_explicitRef', 'B16_phaseRelax025_fromB14'),
    ('C14_topFixedFlux_explicitRef', 'C16_phaseRelax025_fromC14'),
)
FIELDS = {
    'alphaL': ('metalMeanLiquidFraction', 'volFieldValue.dat', ('volAverage(phaseChangeSource:alpha1)',)),
    'latent_W': ('metalLatentHeatPower', 'volFieldValue.dat', ('volIntegrate(latentHeatRateVol)',)),
    'sensible_J': ('metalSensibleEnthalpy', 'volFieldValue.dat', ('volIntegrate(rho,h)',)),
    'top_W': ('metalTopEnergyPower', 'surfaceFieldValue.dat', ('sum(energyAdvectiveFlux)', 'sum(heatFlux)', 'sum(energyFlux)')),
    'mold_W': ('metalMoldEnergyPower', 'surfaceFieldValue.dat', ('sum(energyAdvectiveFlux)', 'sum(heatFlux)', 'sum(energyFlux)')),
    'boundary_W': ('metalBoundaryEnergyPower', 'surfaceFieldValue.dat', ('sum(energyAdvectiveFlux)', 'sum(heatFlux)', 'sum(energyFlux)')),
}


def read_data(path: Path, headers: tuple[str, ...]):
    if not path.is_file():
        raise ValueError(f'missing source {path}')
    data, declared = [], None
    for n, line in enumerate(path.read_text(encoding='utf8', errors='replace').splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            if line[1:].strip().startswith('Time'):
                declared = tuple(line[1:].strip().split()[1:])
            continue
        parts = line.split()
        if len(parts) != len(headers) + 1:
            raise ValueError(f'{path}:{n}: expected {len(headers)} columns, got {len(parts)-1}')
        try:
            row = tuple(float(x) for x in parts)
        except ValueError as exc:
            raise ValueError(f'{path}:{n}: nonnumeric field') from exc
        if not all(map(math.isfinite, row)) or row[0] < 0:
            raise ValueError(f'{path}:{n}: invalid time or field value')
        if data and row[0] <= data[-1][0]:
            raise ValueError(f'{path}:{n}: nonmonotonic/repeated time')
        data.append(row)
    if declared != headers:
        raise ValueError(f'{path}: unexpected column header {declared}; expected {headers}')
    if len(data) < 2:
        raise ValueError(f'{path}: at least 2 measured timestamps required')
    return data


def time_map(data, *, decimals=7):
    times = {}
    for row in data:
        key = round(row[0], decimals)
        if key in times:
            raise ValueError(f'ambiguous duplicate timestamp after {decimals}-digit alignment: {key}')
        if abs(key-row[0]) > 0.5 * 10**(-decimals) + 1e-12:
            raise ValueError('misaligned physical time')
        times[key] = row
    return times


def trapezoid(rows, col):
    if len(rows) < 2:
        raise ValueError('at least two samples needed')
    return math.fsum((rows[i][0]-rows[i-1][0])*(rows[i][col]+rows[i-1][col])/2 for i in range(1,len(rows)))


def close(a, b):
    # Numeric diagnostic comparison (source ASCII values may be rounded).
    return abs(a-b) <= 1e-3 + 1e-5*max(abs(a), abs(b))


def inspect_case(case_root: Path):
    output = {'case': case_root.name, 'status': 'INCOMPLETE', 'sources': {}, 'checks': {}, 'metrics': None, 'alerts': [],
              'scope': 'original postProcessing scalar reductions; not a full region conservation audit'}
    maps = {}
    for key, (folder, filename, header) in FIELDS.items():
        path = case_root/'postProcessing'/'metal'/folder/'0'/filename
        try:
            rows = read_data(path, header)
            maps[key] = time_map(rows)
            output['sources'][key] = {'path': str(path.relative_to(case_root)),
                                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                      'sample_count': len(rows), 'last_time_s': rows[-1][0]}
        except (ValueError, OSError) as exc:
            output['sources'][key] = None
            output['alerts'].append(f'{key}: {exc}')
    if len(maps) != len(FIELDS):
        return output
    times = sorted(set.intersection(*(set(d) for d in maps.values())))
    output['checks']['shared_samples'] = len(times)
    output['checks']['unaligned_samples'] = {k: len(v)-len(times) for k,v in maps.items()}
    if len(times) < 2:
        output['alerts'].append('insufficient real shared timestamps for integration')
        return output
    if any(len(v) != len(times) for v in maps.values()):
        output['alerts'].append('source files have unmatched physical timestamps; only their intersection was compared')
    rows = {name: [field[t] for t in times] for name, field in maps.items()}
    for i, t in enumerate(times):
        if rows['alphaL'][i][1] < -1e-6 or rows['alphaL'][i][1] > 1+1e-6:
            output['alerts'].append(f'alphaL outside nominal [0,1] at {t}s')
        for name in ('top_W', 'mold_W', 'boundary_W'):
            v=rows[name][i]
            if not close(v[1] + v[2], v[3]):
                output['alerts'].append(f'{name} energyFlux != advective+heatFlux at {t}s')
        for col, label in ((1, 'advective'), (2, 'thermal'), (3, 'total')):
            if not close(rows['top_W'][i][col] + rows['mold_W'][i][col], rows['boundary_W'][i][col]):
                output['alerts'].append(f'boundary != top+mold ({label}) at {t}s')
    alpha=rows['alphaL']
    H=rows['sensible_J']
    E_boundary=trapezoid(rows['boundary_W'], 3)
    E_latent=trapezoid(rows['latent_W'], 1)
    deltaH=H[-1][1]-H[0][1]
    output['metrics']={
        't_start_s': times[0], 't_end_s': times[-1], 'shared_sample_count': len(times),
        'mean_alphaL_initial': alpha[0][1], 'mean_alphaL_final': alpha[-1][1],
        'change_mean_alphaL': alpha[-1][1]-alpha[0][1],
        'sensible_enthalpy_change_J': deltaH,
        'integrated_boundary_total_J': E_boundary,
        'integrated_top_total_J': trapezoid(rows['top_W'], 3),
        'integrated_mold_total_J': trapezoid(rows['mold_W'], 3),
        'integrated_boundary_advective_J': trapezoid(rows['boundary_W'], 1),
        'integrated_boundary_heat_J': trapezoid(rows['boundary_W'], 2),
        'integrated_latent_source_J': E_latent,
        'conditional_energy_residual_J': deltaH + E_boundary - E_latent,
    }
    output['checks']['boundary_partition_integral_J'] = E_boundary - output['metrics']['integrated_top_total_J'] - output['metrics']['integrated_mold_total_J']
    output['status'] = 'REVIEW' if output['alerts'] else 'NUMERIC_SCREEN_PASSED'
    return output


def analyze(root: Path):
    names=sorted(set(n for pair in CASE_PAIRS for n in pair))
    case_root=root/'cases_controlled_buoyancy'
    records={name: inspect_case(case_root/name) for name in names}
    pairs=[]
    for parent, variant in CASE_PAIRS:
        p, v = records[parent]['metrics'], records[variant]['metrics']
        row={'parent': parent, 'variant': variant, 'status': 'MISSING_EVIDENCE', 'delta_final_mean_alphaL': None,
             'delta_integrated_boundary_J': None, 'delta_conditional_residual_J': None}
        if p and v and math.isclose(p['t_start_s'], v['t_start_s'],abs_tol=1e-7) and math.isclose(p['t_end_s'],v['t_end_s'],abs_tol=1e-7):
            row.update(status='NUMERIC_COMPARISON_ONLY',
                       delta_final_mean_alphaL=v['mean_alphaL_final']-p['mean_alphaL_final'],
                       delta_integrated_boundary_J=v['integrated_boundary_total_J']-p['integrated_boundary_total_J'],
                       delta_conditional_residual_J=v['conditional_energy_residual_J']-p['conditional_energy_residual_J'])
        elif p and v:
            row['status']='NON_EQUIVALENT_TIME_INTERVAL'
        pairs.append(row)
    return {'schema':'quickcup-energy-phase-evidence-v1', 'origin':'read-only original OpenFOAM postProcessing',
            'energy_assumptions':'Residual is conditional on sign, source and region definitions; not validated conservation',
            'verification':'NUMERIC_SCREEN_ONLY_NOT_CFD_OR_EXPERIMENTAL_VALIDATION',
            'field_units_from_project_guide':{'alphaL':'1','latent_W':'W','sensible_J':'J','top_W':'W','mold_W':'W','boundary_W':'W'},
            'cases':[records[n] for n in names], 'paired_comparisons':pairs}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out',type=Path,required=True,help='new empty directory outside simulation cases')
    parser.add_argument('--strict',action='store_true',help='nonzero if missing or invalid data')
    args=parser.parse_args(argv)
    root=args.root.resolve(); out=args.out.resolve()
    cases=root/'cases_controlled_buoyancy'
    if out == cases or cases in out.parents or out == root:
        parser.error('will not write into original simulation data')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error('output must be a new or empty directory (no overwrite)')
    report=analyze(root)
    out.mkdir(parents=True, exist_ok=True)
    (out/'energy_phase_evidence.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    cols=['case','status','t_end_s','shared_sample_count','mean_alphaL_final','sensible_enthalpy_change_J',
          'integrated_boundary_total_J','integrated_latent_source_J','conditional_energy_residual_J','alerts']
    with (out/'energy_phase_metrics.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for c in report['cases']:
            w.writerow({'case':c['case'],'status':c['status'],**{k:v for k,v in (c['metrics'] or {}).items() if k in cols},
                        'alerts':'; '.join(c['alerts'])})
    lines=['# QuickCup energy / phase screening','',
           'SOURCE-BASED NUMERIC DIAGNOSTICS ONLY. No OpenFOAM execution, no experimental validation.',
           'The conditional residual is not proof of physical conservation; signs, regions and other source terms require independent review.','',
           '| Case | Status | Last αL | Conditional residual (J) | Alerts |', '|---|---|---:|---:|---:|']
    for c in report['cases']:
        m=c['metrics'] or {}
        lines.append(f"| {c['case']} | {c['status']} | {m.get('mean_alphaL_final','n/a')} | {m.get('conditional_energy_residual_J','n/a')} | {len(c['alerts'])} |")
    lines += ['', '## Scientific limitations', '', '- energyFlux already equals energyAdvectiveFlux + heatFlux; do not add it again.',
              '- Sensible enthalpy does not include latent energy; the residual includes the latent source once as a conditional diagnostic.',
              '- No mold side flux reciprocity, full boundary/source terms, spatial front or experimental curve validation was performed.',
              '- Comparing B and C requires separate physical-equivalence checks.','']
    (out/'summary.md').write_text('\n'.join(lines),encoding='utf8')
    bad = any(c['status']!='NUMERIC_SCREEN_PASSED' for c in report['cases']) or any(p['status']!='NUMERIC_COMPARISON_ONLY' for p in report['paired_comparisons'])
    print(f"Energy/phase evidence: {len(report['cases'])} cases; {len(report['paired_comparisons'])} parent→variant comparisons; issues={bad}")
    print('CFD execution: NO; physical/experimental validation: NO')
    return int(args.strict and bad)


if __name__ == '__main__':
    raise SystemExit(main())
