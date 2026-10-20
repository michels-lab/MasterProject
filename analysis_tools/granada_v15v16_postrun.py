#!/usr/bin/env python3
"""Non-destructive post-run evidence gate for QuickCup B/C V15/V16.

This program never runs OpenFOAM, edits original cases, or establishes physical
or experimental validation. Inputs are genuine committed probe and foamLog files.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

PAIRS = (
    ('B14_topFixedFlux_explicitRef', 'B15_adaptiveDt_fromB14'),
    ('C14_topFixedFlux_explicitRef', 'C15_adaptiveDt_fromC14'),
    ('B14_topFixedFlux_explicitRef', 'B16_phaseRelax025_fromB14'),
    ('C14_topFixedFlux_explicitRef', 'C16_phaseRelax025_fromC14'),
)
PROBE = Path('postProcessing/metal/temperatureProbe/0/T')
CO = Path('logs/CourantMax_0')
CONT = Path('logs/contCumulative_0')
CONTROL = Path('system/controlDict')


def read_series(path: Path, *, probe=False):
    """Return strictly ordered numerical (t, y) points; don't guess bad data."""
    if not path.is_file():
        raise ValueError(f'missing file: {path}')
    rows = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        cells = line.split()
        if len(cells) != 2:
            raise ValueError(f'{path}:{i}: expected exactly one time and one value')
        try:
            t = float(cells[0].removesuffix('s'))
            y = float(cells[1])
        except ValueError as exc:
            raise ValueError(f'{path}:{i}: nonnumeric row') from exc
        if not all(map(math.isfinite, (t, y))) or t < 0:
            raise ValueError(f'{path}:{i}: invalid finite physical time/value')
        if rows and t <= rows[-1][0]:
            raise ValueError(f'{path}:{i}: repeated/out-of-order physical time')
        rows.append((t, y))
    if not rows:
        raise ValueError(f'{path}: no measurements')
    return rows


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def max_co_limit(control: Path):
    if not control.is_file():
        return None
    raw = control.read_text(encoding='utf-8', errors='replace')
    raw = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw, flags=re.S)
    matches = re.findall(r'(?m)^\s*maxCo\s+([0-9.eE+-]+)\s*;', raw)
    if len(matches) != 1:
        return None
    value = float(matches[0])
    return value if math.isfinite(value) and value > 0 else None


def interpolated(rows, t):
    """Linear interpolation only inside measured interval, never extrapolate."""
    if t < rows[0][0] - 1e-10 or t > rows[-1][0] + 1e-10:
        raise ValueError('requested extrapolation')
    import bisect
    xs = [r[0] for r in rows]
    j = bisect.bisect_left(xs, t)
    if j == len(rows):
        return rows[-1][1]
    if j == 0 or math.isclose(xs[j], t, abs_tol=1e-10):
        return rows[j][1]
    t0, y0 = rows[j-1]
    t1, y1 = rows[j]
    return y0 + (t - t0) * (y1 - y0) / (t1 - t0)


def temperature_metrics(a, b, step=0.01):
    start = max(a[0][0], b[0][0])
    stop = min(a[-1][0], b[-1][0])
    # Fixed physical-time clock anchored to integer multiples of 0.01 s.
    i0 = math.ceil((start - 1e-9) / step)
    i1 = math.floor((stop + 1e-9) / step)
    if i1 <= i0:
        raise ValueError('insufficient common physical-time interval')
    diffs = [interpolated(b, i*step) - interpolated(a, i*step)
             for i in range(i0, i1 + 1)]
    return {'first_common_time_s': round(i0*step, 10),
            'last_common_time_s': round(i1*step, 10),
            'aligned_samples': len(diffs),
            'rmse_K': math.sqrt(math.fsum(v*v for v in diffs)/len(diffs)),
            'max_abs_delta_K': max(map(abs, diffs)),
            'delta_at_last_common_s_K': diffs[-1]}


def inspect_case(case: Path):
    out = {'case': case.name, 'source_files': {}, 'diagnostics': {}, 'alerts': [], 'notes': []}
    for kind, path, isprobe in [('probe_T', PROBE, True), ('courant', CO, False),
                                ('continuity', CONT, False)]:
        source = case/path
        try:
            rows = read_series(source, probe=isprobe)
            out['source_files'][kind] = {'path': str(path), 'sha256': sha256(source),
                                          'samples': len(rows), 'last_time_s': rows[-1][0]}
            out['diagnostics'][kind] = rows
        except ValueError as exc:
            out['source_files'][kind] = None
            out['alerts'].append(str(exc))
    limit = max_co_limit(case/CONTROL)
    out['maxCo_configured'] = limit
    if limit is None:
        out['alerts'].append('Cannot determine unique active maxCo from controlDict')
    if 'courant' in out['diagnostics']:
        co = out['diagnostics']['courant']
        out['courant_max_observed'] = max(y for _, y in co)
        out['courant_over_limit_count'] = None if limit is None else sum(y > limit for _, y in co)
        if limit is not None and out['courant_over_limit_count']:
            out['alerts'].append('Observed Courant exceeds configured maxCo; inspect adaptive stepping')
    if 'continuity' in out['diagnostics']:
        out['continuity_cumulative_last'] = out['diagnostics']['continuity'][-1][1]
        out['notes'].append('Continuity is diagnostic evidence, not proof of mass closure')
    return out


def run(root: Path):
    cases_root = root/'cases_controlled_buoyancy'
    names = sorted(set(sum(([a,b] for a,b in PAIRS), [])))
    raw = {name: inspect_case(cases_root/name) for name in names}
    pairs = []
    for parent, child in PAIRS:
        entry = {'parent': parent, 'variant': child, 'metrics': None, 'alerts': []}
        pa = raw[parent]['diagnostics'].get('probe_T')
        pb = raw[child]['diagnostics'].get('probe_T')
        if pa and pb:
            try:
                entry['metrics'] = temperature_metrics(pa, pb)
            except ValueError as exc:
                entry['alerts'].append(str(exc))
        else:
            entry['alerts'].append('Missing measured parent or child temperature probe')
        pairs.append(entry)
    cases = []
    for name in names:
        v = raw[name]
        v.pop('diagnostics')  # Do not duplicate raw full series in a portable report.
        cases.append(v)
    return {'format': 'quickcup-foamlens-openfoam-evidence-v1',
            'scope': 'post-run numerical evidence screen B/C V15/V16',
            'execution': 'read-only; no CFD executed',
            'verification': 'NOT_PHYSICALLY_OR_EXPERIMENTALLY_VALIDATED',
            'temperature_alignment': 'common measured time 0.01 s; no extrapolation',
            'temperature_units': 'K (QuickCup-specific probe convention; verify source)',
            'cases': cases, 'comparisons': pairs}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--out', type=Path, required=True,
                   help='New report folder, outside of simulation case directories')
    p.add_argument('--strict', action='store_true',
                   help='Fail if data missing, alignment impossible, or Courant alert')
    args = p.parse_args(argv)
    root = args.root.resolve()
    out = args.out.resolve()
    if out == root or (root/'cases_controlled_buoyancy') in out.parents or out == root/'cases_controlled_buoyancy':
        p.error('Refusing output in original CFD case tree')
    if out.exists() and any(out.iterdir()):
        p.error('Output folder must not contain previous reports; choose a fresh destination')
    report = run(root)
    out.mkdir(parents=True, exist_ok=True)
    (out/'evidence.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    with (out/'pair_metrics.csv').open('w', encoding='utf-8', newline='') as f:
        fields = ['parent', 'variant', 'first_common_time_s', 'last_common_time_s',
                  'aligned_samples', 'rmse_K', 'max_abs_delta_K', 'delta_at_last_common_s_K', 'alerts']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for x in report['comparisons']:
            writer.writerow({'parent': x['parent'], 'variant': x['variant'],
                             **(x['metrics'] or {}), 'alerts': '; '.join(x['alerts'])})
    warning_count = sum(bool(x['alerts']) for x in report['cases']) + sum(bool(x['alerts']) for x in report['comparisons'])
    print(f'QuickCup postrun evidence: {len(report["cases"])} cases, {len(report["comparisons"])} pairs; {warning_count} case/pair alerts')
    print(f'No OpenFOAM run; no physical or experimental validation. Output: {out}')
    return int(args.strict and warning_count > 0)


if __name__ == '__main__':
    raise SystemExit(main())
