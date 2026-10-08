# Plan de investigación QuickCup — acuerdos tras reunión con el director
Fecha: 2026-10-08 · Estado: hoja de ruta, no validación de resultados · OpenFOAM Foundation v14

## Prioridades y genealogía

```text
C14  [2D, dt fijo, relax=0.1] ──> C15 [2D, adaptive dt; salida cada 0.1 s]
    ├────────────────────────> C16 [2D, dt fijo, relax de fase=0.25]
    └────────────────────────> C3D-01 [3D base, sin superficie libre; caso futuro]
B14  [rho(T), cerrado, mismatch continuidad] ──> B-FS-01 [interfaz aire-metal]
                                      └────────> B-SH-01 [contracción/feeding con modelo conservativo]
```

**Regla de investigación**: C15 y C16 descienden individualmente de C14; sus diferencias se evalúan contra C14 por separado. No se aplican simultáneamente `adaptive` y `relax=0.25` sin un experimento factorial nuevo. C14 y B14 quedan preservados. Ningún experimento se ejecuta en GitHub: Michel corre en laptop y hace push; GitHub audita lo almacenado.

### C15_adaptiveDt_fromC14 — PREPARED_NOT_RUN
- Diferencia numérica: `system/controlDict/adjustTimeStep yes`.
- Instrumentación de escritura para tiempos físicos comparables: `writeControl adjustableRunTime`; `writeInterval 0.1` segundos.
- Sin cambio respecto a C14: `deltaT inicial=0.001`, `maxCo=0.25`, `maxDeltaT=0.1`, `relax=0.1`.
- Precedente de cautela: las familias adaptativas C6/C8 y B6/B8 no reprodujeron exactamente el patrón de solidificación con dt fijo pese a la reducción de tiempo CPU.
- **Verificar después del push**: evolución real de dt; Courant; T(t)/U(t)/alphaL(t) y perfiles alineados por tiempo físico; balances e interface; tiempo de reloj y medidas de sensibilidad, no solo End.

### C16_phaseRelax025_fromC14 — PREPARED_NOT_RUN
- Diferencia única: `constant/metal/fvModels/phaseChangeSource/relax=0.25` (C14=0.1).
- El `maxCo=0.25` y `relaxationFactors=1.0` son conceptos DIFERENTES y quedan intactos.
- Código real: `solidificationMelting.C` en https://cpp.openfoam.org/v14/solidificationMelting_8C_source.html utiliza `relax` en actualización de `alpha1` por timestep: este cambio puede afectar respuesta transitoria de fracción de fase y fuente latente, no solo residuales.
- **Verificar después del push**: alphaL, dAlphaLdt, calor latente, T(t), fronts y velocidad, estabilidad/residuos, conservación y coste.

## C3D-01 — expansión geométrica desde C14, fase siguiente

**C14 real NO es 3D**: `system/blockMeshDict` representa 40×40×10 mm en metal, con **80×80×1 celdas** y parches `frontAndBack` de tipo `empty`. Es un plano 2D extruido para mallado; hay que rediseñar geometría, mallado, parches y referencias.

**Pendiente del investigador/director**: determinar la geometría del QuickCup real (idealmente sección circular/anillo o dimensiones del molde medido), profundidad, volumen de metal, espesores y ubicación/posición 3D de termopar. Sin esos datos no proponer una malla realista arbitraria.

Plan gradual:
1. Congelar referencia 2D C14; replicar parámetros físicos y condiciones reales en un **caso nuevo** C3D-01.
2. Construir malla genuinamente 3D metal+molde; retirar `empty` solo cuando existan paredes/caras físicas correctas; corregir zonas/interfaces y controles térmicos, radiación/convección lateral y metalTop según geometría.
3. Verificar `checkMesh`, topología, normales de patches, volúmenes/áreas, conexión térmica metal–molde, balance de energía, punto de presión `pRefPoint`, malla/timestep; el probe 2D (0.02,0.02,0.005) no se reusa sin verificar.
4. Elegir comparación 2D↔3D en observables físicos medibles (T del termopar, masa y áreas de intercambio, frentes de solidificación, flujos), sin asumir que un cambio de geometría equivale a un cambio de discretización solamente.
5. Afinar malla y validar después con curvas de enfriamiento y datos JMatPro (puerta J0 sigue abierta).

## B-FS y B-SH — programa paralelo de superficie libre y shrinkage

**No descartar B14**: es un experimento útil de densidad variable, pero el dominio metálico impermeable y de volumen fijo exhibió continuidad acumulada ≈ -0.031. El resultado motiva explorar física de cambio de volumen, **no demuestra todavía** que incorporar aire o superficie libre resolverá exactamente ese residuo.

Distinción física: el metal fundido cambia densidad/volumen; la superficie metal-aire **desciende** si no hay alimentación, y el aire atmosférico ocupa el espacio expuesto. **No** representa que el aire se disuelva o entre a reemplazar masa dentro del metal. Si hay feeding, el balance de masa cambia; si hay contracción de solidificación, la porosidad o cavidades exigen física adicional.

Etapas **separadas**:
1. **B-FS-01 factibilidad numérica:** estudiar el módulo OpenFOAM Foundation v14 `twoPhaseVoFSolver` (captura VOF aire-metal) y/o otros módulos multiphase apropiados; confirmar integración real con energía metal-molde, `solidificationMelting`, propiedades de aire y metal, gravedad, tensión superficial y condición atmósfera. NO asumir que basta convertir la pared `metalTop` en `pressureInletOutletVelocity`.
2. **B-FS-02 interfaz sin solidificación:** un test simple y controlado de líquido/aire e hidráulica atmosférica, sin mezclar fuente latente ni shrinkage.
3. **B-SH-01 densidad dependiente de temperatura y fase:** representar `rho(T, alphaL)`, posible alimentación, desplazamiento de interfaz y cierre conservativo de masa; rastrear masa metálica, volumen y altura de superficie, densidad por fase, presiones y transporte de energía.
4. **B-SH-02 solidificación**: acoplar latente/Darcy y, si necesario, contracción de solidificación contra las leyes de mezcla; estudiar formación de porosidad únicamente si se incorpora un modelo que la represente, nunca inferirla solo del aire exterior.
5. Comparar B14 cerrado, B-FS, B-SH y familia C solo con geometría, propiedades, condiciones de frontera y magnitudes de interés equivalentes. Registrar costo numérico y conservación.

En Foundation v14 existen módulos `twoPhaseVoFSolver` y `multiphaseEuler`, pero su presencia **no garantiza** acoplamiento directo compatible con el fvModel del caso actual. Antes de codificar, revisar implementaciones y un tutorial representativo y decidir arquitectura/multirregión.

## Gates de prueba e integridad

- Las nuevas ramas C15/C16 son solo **PREPARED_NOT_RUN** hasta ejecución real en laptop y push de evidencia. Nunca prometer funcionamiento o estabilidad sin logs.
- Tras cada push, usar informes GitHub si Actions funciona; los agentes declarativos no son trabajadores autónomos. Actualizar inventario y bitácoras ES/EN, CASE_NOTES y análisis.
- La puerta **J0 (JMatPro)** y experimental **G1** permanecen abiertas. Trabajar en 3D no sustituye verificar propiedades/condiciones experimentales.
- No copiar postProcessing heredado como evidencia del nuevo caso, ni editar C14/B14.
