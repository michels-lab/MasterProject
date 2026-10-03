# B14_topFixedFlux_explicitRef

Parent case: `B11_topFixedFlux_airGapOF14`.

Purpose: controlled V14 implementation of the supervisor-requested pressure-reference location and direct metalTop face diagnostics, while retaining the V11 impermeable `fixedFluxPressure + slip` formulation.

## Controlled changes

- `pRefPoint (0.02 0.04 0.005)`
- `pRefValue 1e5`
- `nEnergyCorrectors 2` recorded in PIMPLE for configuration traceability
- inline `topFlow` function object: face-wise `U` and `phi`, `writeControl writeTime`

All other physical/numerical settings are inherited from B11.

## Methodological status

**CONFIG-VERIFIED / NOT YET RUN.**

Important OF14 note: the regional solver is `fluid`. In Foundation v14, `fluid::thermophysicalPredictor()` does not read `nEnergyCorrectors`; the keyword is active in `multiphaseEuler`. The run log will be used to verify the effective behavior rather than assuming the keyword changes the solution.
