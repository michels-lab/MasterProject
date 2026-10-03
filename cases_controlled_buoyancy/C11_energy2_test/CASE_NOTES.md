# CASE_NOTES — C11_energy2_test

**Estado:** RUN-VERIFIED — ANALYSIS-VERIFIED  
**Caso padre:** `C11_topFixedFlux_airGapOF14`

## Objetivo
Medir el efecto real de pasar de 1 a 2 energy correctors en el bucle multi-región de `foamMultiRun`.

## Único cambio respecto a C11
`system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.

No se modifica `system/metal/fvSolution`, presión, malla, timestep, propiedades, condiciones de frontera, air gap ni modelo de solidificación.

Este caso no constituye una nueva V; es una prueba controlada C11→C11-energy2.


## Resultado verificado — 2026-10-03

El test completó 10 s con OpenFOAM Foundation 14.

Con `nEnergyCorrectors 2` en el `system/fvSolution` raíz, `foamLog` genera `h_0..h_5` y `e_0..e_5`. Con 3 outer correctors esto confirma 6 solves de energía por timestep. C11 normal genera solo `h_0..2` y `e_0..2`.

Comparación con C11 normal:
- T(t) central: idéntica byte por byte en 10,001 puntos; RMSE = 0 K; T(10 s)=1464.19 K en ambos.
- alphaL central: RMSE = 4.80e-8; diferencia máxima = 1e-6; alphaL(10 s)=0.964815 en ambos.
- U central: RMSE = 7.70e-9 m/s; diferencia máxima = 1e-7 m/s.
- Fracción líquida media: RMSE = 2.22e-8; diferencia máxima = 1e-7; valor a 10 s = 0.9620593 en ambos.
- Perfil y=20 mm a 10 s: T y alphaL idénticos; Uy RMSE = 4.04e-9 m/s; max |ΔUy| = 1e-8 m/s.
- Courant máximo = 0.0650864 en ambos.
- Continuidad acumulada final: 4.44517e-13 (C11) y 4.58617e-13 (energy2).

El sexto solve de entalpía alcanza residual mediano ~1.05e-10 y residual final ~1.57e-11, pero esta sobre-convergencia no cambia la solución física.

Costo de los runs persistidos:
- C11: executionTime 289.433 s; clockTime 302 s.
- C11-energy2: executionTime 387.542 s; clockTime 398 s.

Conclusión: los 2 energy correctors sí son efectivos cuando se definen en el PIMPLE raíz, pero no aportan un cambio físico observable en C11 y aumentan el costo. Se recomienda mantener 1 energy corrector.
