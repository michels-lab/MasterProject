# SUPERSEDED — early V12/V13 pressure prototypes

> **Do not use these directories as the canonical V12/V13 comparison.**
>
> This README documents the first provisional attempt only. The canonical cases are documented in `README_V12_V13_TESTS.md` and are run with `run_v12_v13_tests.sh`.

The provisional cases are:

| Family | Provisional V12 | Provisional V13 |
|---|---|---|
| B | `B12_fixedValueP_rgh` | `B13_prghPressureAtmosphere` |
| C | `C12_fixedValueP_rgh` | `C13_prghPressureAtmosphere` |

These prototypes used an initial `p_rgh value uniform 0` at `metalTop`. That is not hydrostatically consistent with the current case definition `p_rgh = p - rho*gh - pRef` for a 40 mm top surface, `pRef=1e5 Pa`, and atmospheric static pressure.

They are retained only as historical traceability.

Canonical replacements:
- `B12_topFixedValue_airGapOF14`: `fixedValue 2667.739248 Pa`
- `C12_topFixedValue_airGapOF14`: `fixedValue 2676.168 Pa`
- `B13_prghPressure_airGapOF14`: `prghPressure; p uniform 0; value uniform 2667.739248`
- `C13_prghPressure_airGapOF14`: `prghPressure; p uniform 0; value uniform 2676.168`

See `README_V12_V13_TESTS.md` and `PROJECT_AUDIT_LOG_ES.md` for the derivation, OpenFOAM 14 source basis, pressure-reference distinction, and required diagnostics.

The historical script `run_v12_v13_pressure_tests.sh` targets these provisional directories and should not be used for the canonical comparison.
