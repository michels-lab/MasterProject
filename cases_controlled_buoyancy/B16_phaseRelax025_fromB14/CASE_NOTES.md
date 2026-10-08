# CASE_NOTES — B16_phaseRelax025_fromB14

**Estado:** PREPARED_NOT_RUN · **Fecha:** 2026-10-08
**Padre controlado:** `B14_topFixedFlux_explicitRef`.
**Ejecución:** exclusivamente en laptop, después GitHub recibe los resultados por push.

## Hipótesis y diseño
V16 estudia por separado el coeficiente de relajación del cambio de fase en las familias B y C. `B16` es independiente de `B15`, como `C16` lo es de `C15`.

**Una sola diferencia de archivo de entrada frente a B14:** `constant/metal/fvModels` dentro de `phaseChangeSource`: `relax 0.1 -> 0.25`. No se cambian `relaxationFactors` en `system/fvSolution` ni `maxCo=0.25`. `adjustTimeStep no`, `deltaT 0.001` s fijo, EOS `rho(T)`, malla, materiales y BC de B14 quedan intactos.

La `relax` de `solidificationMeltingSource` afecta la corrección de fracción líquida, fuentes latentes y potencialmente trayectoria termo-hidrodinámica. No es lo mismo que subrelajación lineal de presión/velocidad ni cambiar Courant.

## Riesgo específico B
B14 ya presenta problema de continuidad acumulada en volumen rígido cerrado. No presentar un cambio de relajación como una corrección de esa incompatibilidad. El desarrollo de B con superficie libre, gas y shrinkage comienza después de completar V16 como línea física independiente.

## Validación tras push (PENDIENTE)
- [ ] Validar finalización, deltaT fijo, Courant, residuales y comparación de tiempos.
- [ ] Comparar B16 vs B14 por tiempo físico: `alphaL`, `dAlphaLdt`, `latentHeatRateVol`, frente de fase, T/U, continuidad, energía y top `phi` cara por cara.
- [ ] Comparar sensibilidad de relajación en B16-B14 contra C16-C14; advertir si sólo cambia el rendimiento numérico o la física.
- [ ] Registrar con evidencia resultados en logs ES/EN, CASE_NOTES, análisis y matriz. No declarar corrida completada por archivo preparado.

**Ninguna simulación ejecutada al crear este caso en GitHub.**
