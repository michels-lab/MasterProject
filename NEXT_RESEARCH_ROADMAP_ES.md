# Plan de investigación QuickCup — acuerdos tras reunión con el director
Fecha: 2026-10-08 · Estado: hoja de ruta, no validación de resultados · OpenFOAM Foundation v14

## Prioridades y genealogía

```text
                           FASE COMÚN DE SENSIBILIDAD (2D)
B14 ──┬──> B15  adaptive timestep ─────┐
      └──> B16  relax fase = 0.25 ──────┤
                                       ├──> CIERRE V15/V16 ──> RUTA B
C14 ──┬──> C15  adaptive timestep ─────┤                       aire–metal,
      └──> C16  relax fase = 0.25 ──────┘                       shrinkage/feeding
                                                └─────────────> RUTA C
                                                                  modelo 3D
```

**Secuencia acordada:** V15 y V16 se ejecutan **en ambas familias B y C**, como pruebas de sensibilidad paralelas. **Después de cerrar V16** arrancan **dos rutas científicas diferentes**: C evoluciona a un modelo 3D desde la referencia C14 (o una configuración posterior justificada por evidencia), y B evoluciona a un modelo de superficie libre aire-metal y contracción/feeding. La transición de etapa es cronológica: **NO implica que C3D sea un clon de C16 ni que B-FS sea un clon de B16**. Se decide el padre físico según el análisis de V15/V16, manteniendo B14/C14 congelados. Ningún caso se ejecuta desde GitHub.

**Comparaciones pareadas**:
- V15: `B15 vs B14` y `C15 vs C14` (adaptativo), después diferencias de sensibilidad B/C.
- V16: `B16 vs B14` y `C16 vs C14` (relajación), después diferencias de sensibilidad B/C.
- El avance a 3D y superficie libre **solo se inicia tras disponer de los resultados V16 y revisar ambos grupos**; no se asume que las alteraciones numéricas resuelvan la discrepancia de continuidad B14.

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

### B15_adaptiveDt_fromB14 — PREPARED_NOT_RUN
- Versión paralela directa de B14, con los **mismos tres ajustes** de `system/controlDict` que C15 frente a C14: `adjustTimeStep=yes`, `writeControl=adjustableRunTime`, `writeInterval=0.1` s.
- Permanecen `maxCo=0.25`, `maxDeltaT=0.1` s, `deltaT` inicial 0.001 s, `relax=0.1`, EOS `rho(T)` de B14, mismas condiciones de frontera y top `slip+fixedFluxPressure`.
- **Investigar** estabilidad, Courant, errores de continuidad, T/U/alphaL, energía, frente de fase y costo vs B14, con series alineadas por tiempo físico. Comprobar analogías/divergencias de sensibilidad con C15 vs C14.
- La prueba adaptativa **no arregla** por sí misma la incompatibilidad de densidad variable en volumen rígido cerrado.

### B16_phaseRelax025_fromB14 — PREPARED_NOT_RUN
- Versión paralela directa de B14. Solo cambia `constant/metal/fvModels/phaseChangeSource/relax` `0.1 -> 0.25`, manteniendo `adjustTimeStep=no` y `deltaT=0.001` s fijo.
- `maxCo=0.25` y `relaxationFactors=1.0` son diferentes al `relax` de solidificationMeltingSource; no tocarlos.
- **Investigar** respuesta de fracción líquida, latente, T/U, residual, continuidad y costo vs B14; contrastar `B16-B14` vs `C16-C14`.
- Separar resultado de relajación del diseño posterior de superficie libre/contracción. No declarar que `relax=0.25` valide la física de B.

## C3D-01 — expansión geométrica desde C14, fase siguiente

**Esta ruta 3D empieza después de concluir V16 para las dos familias.**

**C14 real NO es 3D**: `system/blockMeshDict` representa 40×40×10 mm en metal, con **80×80×1 celdas** y parches `frontAndBack` de tipo `empty`. Es un plano 2D extruido para mallado; hay que rediseñar geometría, mallado, parches y referencias.

**Pendiente del investigador/director**: determinar la geometría del QuickCup real (idealmente sección circular/anillo o dimensiones del molde medido), profundidad, volumen de metal, espesores y ubicación/posición 3D de termopar. Sin esos datos no proponer una malla realista arbitraria.

Plan gradual:
1. Congelar referencia 2D C14; replicar parámetros físicos y condiciones reales en un **caso nuevo** C3D-01.
2. Construir malla genuinamente 3D metal+molde; retirar `empty` solo cuando existan paredes/caras físicas correctas; corregir zonas/interfaces y controles térmicos, radiación/convección lateral y metalTop según geometría.
3. Verificar `checkMesh`, topología, normales de patches, volúmenes/áreas, conexión térmica metal–molde, balance de energía, punto de presión `pRefPoint`, malla/timestep; el probe 2D (0.02,0.02,0.005) no se reusa sin verificar.
4. Elegir comparación 2D↔3D en observables físicos medibles (T del termopar, masa y áreas de intercambio, frentes de solidificación, flujos), sin asumir que un cambio de geometría equivale a un cambio de discretización solamente.
5. Afinar malla y validar después con curvas de enfriamiento y datos JMatPro (puerta J0 sigue abierta).

## B-FS y B-SH — programa paralelo de superficie libre y shrinkage

**Esta ruta B empieza después de concluir V16 en las dos familias; B15 y B16 son ensayos numéricos previos y no contienen todavía aire, superficie libre ni shrinkage.**

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

- Los nuevos casos B15/B16/C15/C16 son solo **PREPARED_NOT_RUN** hasta ejecución real en laptop y push de evidencia. Nunca prometer funcionamiento o estabilidad sin logs.
- Tras cada push, usar informes GitHub si Actions funciona; los agentes declarativos no son trabajadores autónomos. Actualizar inventario y bitácoras ES/EN, CASE_NOTES y análisis.
- La puerta **J0 (JMatPro)** y experimental **G1** permanecen abiertas. Trabajar en 3D no sustituye verificar propiedades/condiciones experimentales.
- No copiar postProcessing heredado como evidencia del nuevo caso, ni editar C14/B14.

## 2026-10-15 — Preflight reproducible previo a ejecutar V15/V16

El árbol Git de las cuatro variantes se comparó directamente con su padre (B14/C14): únicamente difieren `system/controlDict` para V15 y `constant/metal/fvModels` para V16; los demás archivos de entrada conservan el mismo blob. Se añadió `analysis_tools/preflight_sensitivity_cases.py` con pruebas sintéticas `analysis_tools/test_preflight_sensitivity.py` para detectar diferencias no controladas, valores activos fuera de hipótesis, entradas faltantes y evidencia heredada. Uso: `python3 analysis_tools/preflight_sensitivity_cases.py --strict`.

**Esto verifica la preparación de entradas, NO el resultado numérico.** Los cuatro casos siguen `PREPARED_NOT_RUN`, a la espera de ejecución en laptop y auditoría MAZAPÁN. Evidencia: [analysis_results/v15_v16_preflight/README.md](analysis_results/v15_v16_preflight/README.md). La bifurcación C3D/B-FS continúa bloqueada hasta cerrar V16 de B y C.

## 2026-10-15 — Estado tras subir resultados B11E2 / V15 / V16

Las cinco variantes tienen archivos versionados de solver y sonda hasta 10 s. No repetir inmediatamente `Allclean`/`Allrun`: primero auditar evidencia y confrontarla con los padres. La comparación térmica preliminar y el diagnóstico de Courant/continuidad constan en `analysis_results/v15_v16_postpush_20261015/README.md`. La carpeta de B conserva un desbalance de continuidad ≈ -0.031. B15/C15 superaron marginalmente `maxCo=0.25`; estudiar la implementación del control adaptativo y sus consecuencias. **No se abre automáticamente C3D ni B-FS ni se cierran J0/G1** hasta completar la auditoría de V16.


## 2026-10-19 — Avance de C3D-01 independiente de FoamLENS (malla PRELIMINAR)

Se recibieron los STEP originales individuales del molde y metal; un chequeo CAD con OCC confirmó un sólido válido en cada archivo, intersección volumétrica nula y contacto entre ambos. Se prepararon STL separados, ambos cerrados y orientados, con referencia **condicionada** a un molde de 51.8×65.5×51.8 mm (el export STEP presenta inconsistencia de unidades). El metal ocupa ~47.99 cm³, la arena ~102.84 cm³.

Se creó una barrera geométrica **solo lectura** en `analysis_tools/preflight_c3d_stl.py` con cuatro pruebas sintéticas y manifiesto versionado en [analysis_results/c3d_01_geometry](analysis_results/c3d_01_geometry/README.md). El paquete de malla se entrega localmente y no se publican los archivos CAD del investigador en GitHub. **No se ejecutó OpenFOAM**: `surfaceCheck`, `blockMesh`, `snappyHexMesh`, `splitMeshRegions`, `checkMesh` y balances físicos aún necesitan la laptop. Se conserva C14 intacto y J0/G1 abiertos; la ruta B de superficie libre es independiente.


### 2026-10-19 — Primer caso 3D en carpeta separada (C3D-01)

Se incorporó la **preparación geométrica y de malla de fondo** como experimento independiente en [`cases_3d/C3D_01_metal_mold`](cases_3d/C3D_01_metal_mold/README.md). Utiliza el molde y el metal corregidos/exportados desde SolidWorks (`QuickCup(1).STL`, `metal(1).STL`), no los STEP antiguos con la escala equivocada. Las nuevas piezas tienen dimensiones 51.8×65.5×51.8 mm y 36.5×40×36.5 mm. Para el fondo se propuso una caja de 58×72×58 mm con 29×36×29=30 276 celdas uniformes de 2 mm. Las caras del `blockMeshDict` se corrigieron a orientación exterior y se introdujeron pruebas geométricas estáticas. Los originales STL permanecen locales; el conversor controlado mm→m evita desplazamiento y doble escalado.

**Separar preparación de simulación:** los comandos `blockMesh` y `checkMesh` aún no se han ejecutado en Ubuntu; `snappyHexMesh`, interfaz CHT, solver CFD, J0 y G1 siguen pendientes. Este avance no da por cerrada la auditoría V15/V16 ni valida físicamente la ruta 3D. GitHub Actions jamás ejecuta CFD ni meshing.
