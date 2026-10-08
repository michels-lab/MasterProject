# CASE_NOTES — B15_adaptiveDt_fromB14

**Estado:** PREPARED_NOT_RUN · **Fecha:** 2026-10-08
**Padre controlado:** `B14_topFixedFlux_explicitRef`.
**Ejecución:** exclusivamente desde la laptop del investigador; subir outputs posteriormente a GitHub.

## Hipótesis y diseño
V15 es un experimento numérico paralelo B/C: investigar la sensibilidad del paso de tiempo adaptativo bajo la formulación de densidad tabulada B. Comparar B15 vs B14 a igualdad de tiempo físico, y contrastar los cambios con C15 vs C14.

**Diferencia única de archivo fuente:** `system/controlDict`:
- `adjustTimeStep no -> yes` (cambio numérico bajo prueba).
- `writeControl timeStep -> adjustableRunTime`, `writeInterval 100 -> 0.1` s (solamente para mantener tiempos físicos de salida comparables con 0.1 s; no es cambio constitutivo).
- Mantener `deltaT` inicial = 0.001 s, `maxCo=0.25`, `maxDeltaT=0.1` s, `endTime=10` s, `fvModels/relax=0.1`, todas las propiedades/tablas rho(T), interfaces, geometría, controles PIMPLE y condiciones de frontera B14.

La salida de temperatureProbe puede ser no uniformemente espaciada; NO comparar por número de fila. La serie de C15 tiene exactamente la misma estrategia adaptativa y cadencia física escrita. Las diferencias B/C deben interpretarse con la distinta formulación de densidad, no como réplica experimental.

## Riesgo específico de B
B14 presenta continuidad acumulada ≈ -0.031 a 10 s aunque la tapa es impermeable cara por cara; variar `deltaT` NO resuelve por sí solo el problema físico de densidad variable en volumen cerrado. La línea B física de superficie libre y shrinkage comenzará **después** de cerrar V16 (B15/B16 y C15/C16).

## Validación tras el push (PENDIENTE)
- [ ] Confirmar corrida finalizada a 10 s, maxCo real, deltaT(t), costo, y logs/resultados originales.
- [ ] Confirmar salidas a tiempo físico ~cada 0.1 s, perfiles, `topFlow` cara por cara, `metalTopPhiSum`, potencia térmica y sonda.
- [ ] Comparar B15 vs B14, C15 vs C14 y sensibilidad cruzada B/C con interpolación temporal, fracción líquida, T, U, presión, continuidad y conservación.
- [ ] Registrar anomalías en ambas bitácoras, matriz y análisis de V15. No marcar RUN_VERIFIED hasta contar con evidencia real del usuario.

**Ninguna simulación ejecutada al crear este caso en GitHub.**
