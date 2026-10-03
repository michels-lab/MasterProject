# CASE_NOTES — C11_energy2_test

**Estado:** CONTROLLED TEST — RUN PENDING  
**Caso padre:** `C11_topFixedFlux_airGapOF14`

## Objetivo
Medir el efecto real de pasar de 1 a 2 energy correctors en el bucle multi-región de `foamMultiRun`.

## Único cambio respecto a C11
`system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.

No se modifica `system/metal/fvSolution`, presión, malla, timestep, propiedades, condiciones de frontera, air gap ni modelo de solidificación.

Este caso no constituye una nueva V; es una prueba controlada C11→C11-energy2.
