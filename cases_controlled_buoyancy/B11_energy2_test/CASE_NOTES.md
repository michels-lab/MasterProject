# CASE_NOTES — B11_energy2_test

**Estado:** PREPARED — NOT YET LOCALLY RUN-VERIFIED  
**Caso padre:** `B11_topFixedFlux_airGapOF14`

## Objetivo

Medir el efecto real de pasar de 1 a 2 energy correctors en la familia B usando el mismo baseline físico B11.

## Único cambio respecto a B11

`system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.

No se modifica `system/metal/fvSolution`, presión, malla, timestep, propiedades, condiciones de frontera, air gap ni modelo de solidificación.

Este caso no constituye una nueva V; es una prueba numérica controlada B11→B11-energy2.

## Criterio de verificación local

La corrida válida para documentación de tesis debe ejecutarse localmente en la PC del usuario con OpenFOAM Foundation 14. Con `nOuterCorrectors = 3` y `nEnergyCorrectors = 2`, después de `foamLog` se espera observar seis series de energía por timestep: `h_0..h_5` y `e_0..e_5`.

No marcar RUN-VERIFIED hasta completar y revisar esa corrida local.
