# Spatial metalTop flow post-processing

This diagnostic compares an impermeable top (e.g. B11) against pressure
boundary variants that permit a non-zero solver flux (e.g. B13).

It is retrospective: it reads existing time directories and does **not** run
`foamMultiRun`.

Outputs:
- face-by-face `phi` and patch fields on `metalTop`;
- net `sum(phi)`;
- `sumMag(phi)`, i.e. sum of absolute face contributions;
- minimum/maximum local face flux;
- an 80-point line of `U`, `T`, `p_rgh`, `rho`, and `alphaL` at y=39.75 mm.

Why both net and absolute flux matter:
`sum(phi)≈0` can hide simultaneous local inflow/outflow.  `sumMag(phi)`
detects that cancellation.

The patch `U` field should not be used alone to infer permeability because the
current cases use `U=slip` at metalTop; the solved mass-flux field `phi` is
the direct boundary diagnostic.

Default run:

```bash
bash analysis_tools/run_top_surface_flow_postprocessing.sh
```

The default processes B11 and B13.
