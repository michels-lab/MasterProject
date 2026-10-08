# CASE_NOTES — B11_energy2_test

**Estado:** PREPARED / CLEAN INPUTS / NOT RUN-VERIFIED
**Caso padre:** `B11_topFixedFlux_airGapOF14`
**Fecha de auditoría:** 2026-10-08

## Propósito y cambio controlado
Comparar B11 con su variante de dos correctores de energía efectivos, modificando solamente:
`system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.
Se mantienen sin cambio geometría, malla de entrada, materiales, condiciones de frontera, pasos de tiempo, presión, modelos y demás configuración.

## Integridad de evidencia
Al crear esta variante el 5 de octubre, también se copiaron y versionaron `logs/`, `postProcessing/` y `log.*` del caso padre B11. La serie `postProcessing/metal/temperatureProbe/0/T` tenía exactamente el mismo SHA de blob Git (8e5b4c39dade992897df864f8d4f3dce135dcf24) en ambos directorios.

Esas salidas **no son una ejecución de B11_energy2_test**. La auditoría del 2026-10-08 retiró del árbol versionado de esta variante las salidas heredadas, conservando intacta toda la evidencia original en el caso padre.

## Estado y cierre pendiente
- [x] Inputs comparados mediante hashes Git contra B11: solo difiere `system/fvSolution`.
- [x] Eliminadas del tracking de esta variante las salidas heredadas.
- [ ] Ejecutar la variante realmente con OpenFOAM Foundation 14 en la PC local.
- [ ] Verificar `latestTime=10`, fin normal, ausencia de errores FATAL y seis series `h_0..h_5` y `e_0..e_5`.
- [ ] Comparar T, U, alphaL, `metalTop` cara por cara, residuales, continuidad, Courant y tiempo contra B11; publicar métricas y decisión.

No afirmar RUN-VERIFIED ni ANALYSIS-VERIFIED hasta concluir esos pasos. El resultado ya verificado de C11_energy2 es independiente de esta prueba B11.
