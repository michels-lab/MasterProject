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

Por defecto el runner procesa **todas las carpetas B*/C*** existentes en
`cases_controlled_buoyancy/`, incluidas las variantes históricas y actuales
(B3–B13/C3–C13 y variantes `airGapOF14` que existan en el repositorio).

No vuelve a simular. Para cada caso:
- si encuentra malla + directorios temporales con `metal/phi`, ejecuta el postprocesamiento;
- si no existe `phi` guardado en los tiempos locales, lo marca como `SKIPPED`;
- si `foamPostProcess` falla, lo marca como `FAILED`;
- genera `analysis_results/top_surface_flow_batch/status.tsv` con el estado de toda la campaña.

Esto permite saber exactamente qué versiones históricas pueden compararse
espacialmente sin rerun y cuáles requerirían una decisión posterior.
