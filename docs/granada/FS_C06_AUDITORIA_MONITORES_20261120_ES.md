# FS-C06 — auditoría de monitores nativos: segunda corrida WSL (20/11/2026, zona Saltillo)

## Identificación y nivel de evidencia

- Caso aislado leído: `/home/michel/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091`.
- Commit **ejecutado** por el investigador: `608332778` de `research/fs-c02-metal-air-vof-20261117`.
- Ejecutor: OpenFOAM Foundation 14, `foamMultiRun` con regiones `fluid` y `mold`; dos pasos `1e-7 s` y `2e-7 s`.
- Evidencia: transcripción íntegra de la salida de `read_native_monitors.sh` que el investigador pegó en la conversación. Los `.dat` de WSL **no se han transferido a GitHub**, sus SHA-256 se **copian del lector en su laptop** y no han sido recomputados externamente.
- Estado: `FS_C06_NATIVE_MONITOR_NUMBERS_REVIEWED_NO_GLOBAL_BALANCE_OR_SHRINKAGE`. La geometría y los campos del modelo pasaron el gate anteriormente. Esta auditoría lee números, **no** representa una nueva corrida CFD.
- La primera corrida (`...031743Z_200ccb63`) y sus campos no deben confundirse con esta segunda.

## Evidencia original de los 10 archivos

Las rutas nativas incluyen la región; **no** corresponden a directorios directos bajo `postProcessing`.

| Monitor | Ruta bajo postProcessing | SHA-256 reportado por WSL |
|---|---|---|
| `FS_C06_metalVoFVolume` | `fluid/FS_C06_metalVoFVolume/0/volFieldValue.dat` | `75c1dfd0b8eaa04dd29c883e3f44654a94f8fc0df7930491e4897a894ff7a59d` |
| `FS_C06_solidMetalVolume` | `fluid/FS_C06_solidMetalVolume/0/volFieldValue.dat` | `99b60bf2e072f0c5898959ab732a570ea87a02ebe8cd4187ba8889722de6a06b` |
| `FS_C06_mixtureMass` | `fluid/FS_C06_mixtureMass/0/volFieldValue.dat` | `59290b065b187345e217294eb2a1d5b819a05ba1db71a663e88bbf5e69ee43c6` |
| `FS_C06_atmosphereMassFlux` | `fluid/FS_C06_atmosphereMassFlux/0/surfaceFieldValue.dat` | `66bcd6c16ed54c1c77885b22905f6c34cc71366a67d16be423e99846b6591c28` |
| `FS_C06_atmosphereTopMassFlux` | `fluid/FS_C06_atmosphereTopMassFlux/0/surfaceFieldValue.dat` | `15878c2d8cfb47bb4ffbd54545afa38dd9828c71611e79e7ec4a842d7d3961f9` |
| `FS_C06_atmosphereSidesMassFlux` | `fluid/FS_C06_atmosphereSidesMassFlux/0/surfaceFieldValue.dat` | `da08e59788801f60235efde34f962de61774c323eda904df2c7f10ca2480562d` |
| `FS_C06_atmosphereLowerSidesMassFlux` | `fluid/FS_C06_atmosphereLowerSidesMassFlux/0/surfaceFieldValue.dat` | `fd249cfbe1471813e3261d29e6985debb84989f02d649c1499855ec63f1ed65f` |
| `FS_C06_fluidToMoldMassFlux` | `fluid/FS_C06_fluidToMoldMassFlux/0/surfaceFieldValue.dat` | `23016fadac92eac60d2f5ed77a56984d0355175631cc3369a664440bcb021e07` |
| `FS_C06_wallHeatFluxFluid` | `fluid/FS_C06_wallHeatFluxFluid/0/wallHeatFlux.dat` | `c95d7ba2821ec02d721fe8f52f2b4500cc59f476f2170e8312d321f24aff322c` |
| `FS_C06_wallHeatFluxMold` | `mold/FS_C06_wallHeatFluxMold/0/wallHeatFlux.dat` | `d8d45616a93fb61f4354825bca2d07bed5e8de7cbfc701251effc50159e35145` |

## Campos de fase y volumen

El monitor `volIntegrate(alpha.metal)` registra, para `t=[0,1e-7,2e-7] s`, **exactamente** `4.801191628000e-05 m³` (`48.01191628 cm³`). El `volIntegrate(alpha.metal.solid)` reporta `0.0 m³` en los tres instantes. El volumen de la región `fluid` impreso por OpenFOAM es `1.709592152146e-03 m³` (`34368` celdas); no debe confundirse con el volumen de metal.

El modelo `VoFSolidificationMelting` registró un campo sólido nativo, pero **en esta segunda corrida no produjo solidificación mensurable ni cambio de volumen metálico**. No es una simulación física de contracción ni de alimentación. El campo `alpha.metal.solid` no es por sí mismo una ley de densidad o fuente de contracción.

## Calor conjugado fluido ↔ arena

Los monitores nativos de `wallHeatFlux` devuelven `Q [W]` con signo asociado a las normales y regiones. Se calcula el residuo `R_Q=Q_fluid+Q_mold` y el residuo relativo `|R_Q| / ((|Q_fluid|+|Q_mold|)/2)` cuando ambos lados se han evaluado.

| t (s) | Q fluid [W] | Q mold [W] | R_Q [W] | residuo relativo |
|---:|---:|---:|---:|---:|
| 0 | −519822.1753686 | 0 | −519822.1753686 | **inicialización: no aceptable como pareja recíproca** |
| 1e-7 | −16232.10986685 | +16232.15236226 | +0.04249541 | 2.617981e-6 (0.0002617981 %) |
| 2e-7 | −16232.10729669 | +16232.15056037 | +0.04326368 | 2.665312e-6 (0.0002665312 %) |

**Diagnóstico:** excelente reciprocidad de potencia interfacial en los dos instantes finales **en este smoke de 2e-7 s**. `t=0` revela un fuerte desajuste de inicialización (un lado tiene `−5.198e5 W`, el otro cero); no borrarlo ni usarlo para un cierre energético global. Reciprocidad de `Q` en una interfaz **no prueba conservación total de energía**, ni precisión del flujo durante un tiempo de enfriamiento significativo.

## Masa de mezcla y fronteras

El monitor `volIntegrate(rho)` del dominio fluido, incluye metal **y aire**:

| t (s) | M mezcla [kg] |
|---:|---:|
| 0 | 0.3293664140972 |
| 1e-7 | 0.3293664140983 |
| 2e-7 | 0.3293664141024 |

`ΔM(0→1e-7)=+1.1e-12 kg`, `ΔM(1e-7→2e-7)=+4.1e-12 kg`, `ΔM(total)=+5.2e-12 kg`, equivalente a `1.57879e-11` de la masa inicial. Es una variación diminuta en términos relativos, **no aún un balance cerrado con flujos integrados**.

Los monitores de frontera muestran tres columnas `sum(alphaRhoPhi.metal)`, `sum(alphaRhoPhi.air)`, `sum(rhoPhi)` (unidades de flujo másico `kg/s`). A `t=0` y `t=1e-7`, los flujos reportados son cero. A `t=2e-7 s`:

| Frontera | metal [kg/s] | aire = mezcla [kg/s] |
|---|---:|---:|
| atmosphereTop | 0 | −1.135668241514e-6 |
| atmosphereSides | 0 | −3.238316048521e-7 |
| atmosphereLowerSides | 0 | +1.298668418258e-6 |
| atmosphereCombined | 0 | −1.608314281086e-7 |
| fluid_to_mold | 0 | −4.353783088173e-41 |

La suma de los tres flujos atmosféricos individuales es `−1.608314281081e-7 kg/s`: discrepancia de redondeo frente al monitor agregado `+5e-19 kg/s`. La columna de metal es cero en todos los monitores e instantes: **no se ha medido escape de metal**.

**Advertencia de continuidad:** si se aproximase la masa aportada por la atmósfera en el segundo intervalo mediante trapecios entre su flujo 0 al inicio y −1.608314e-7 kg/s al final, resultaría `+8.04157e-15 kg` de entrada, mientras el inventario `volIntegrate(rho)` cambia `+4.1e-12 kg`. No es correcto reclamar igualdad exacta: falta incluir la formulación conservativa temporal real, otras contribuciones, discretización, cambios termodinámicos y el tratamiento de frontera. La diferencia es una señal para **investigar con criterio**, no un diagnóstico concluyente de violación de masa.

## Decisión y siguiente fase física

1. `FS-C06` **cerrado como puerta de compatibilidad nativa y escritura/lectura de 10 monitores**, en el sentido limitado de este smoke. No declarar transición térmica, alimentación ni contracción.
2. `checkMesh fluid/mold` ya superado; no repetir esta corrida únicamente para mirar valores.
3. Gate siguiente: **transitorio térmico que atraviese el liquidus**, con `T.min`, `T.mean`, `f_s(t)`, `M(t)`, `Q(t)` y curvas de enfriamiento. No extrapolar a segundos reales los 2 × 1e-7 s.
4. Modelo de contracción conservativa requiere ley termofísica trazable `rho_l(T)`, `rho_s(T,f_s)`, coherencia de las ecuaciones fase-metal y total con `alphaRhoPhi`, nivel libre VOF y alimentación, y tratamiento explícito de posible expansión de grafito. No imponer `massSource` neto ficticio por «solidificar».
5. Para aceptación científica: comparación contra QuickCup, cierre de masa por fase y global con fronteras, energía sensible+latente y convergencia temporal/espacial. Los coeficientes C14 usados por compatibilidad siguen siendo **numéricos de referencia** y no valores experimentales validados del hierro de la tesis.

### Referencias técnicas del software

- OpenFOAM Foundation 14 `compressibleVoF`: https://cpp.openfoam.org/v14/classFoam_1_1solvers_1_1compressibleVoF.html
- Modelo `VoFSolidificationMelting`: https://cpp.openfoam.org/v12/classFoam_1_1fv_1_1VoFSolidificationMelting.html
- `massSource` añade masa a la ecuación de continuidad y no equivale automáticamente a contracción interna conservativa: https://cpp.openfoam.org/v14/classFoam_1_1fv_1_1massSource.html
