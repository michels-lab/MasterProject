# FS-C06 — VOF + cambio de fase, sin contracción todavía


> **20-11-2026 — Lector de monitores corregido:** tras el PASS nativo `10/10`, el comando manual de inspección buscó erróneamente carpetas directas `postProcessing/FS_C06_* ` que no existen en el caso; el gate sí había localizado diez `.dat` con búsqueda recursiva. Use [`read_native_monitors.sh`](read_native_monitors.sh) para leer **la segunda corrida ya guardada** sin reejecutar CFD, imprimir rutas reales/cabeceras/filas y hashes. `bash .../read_native_monitors.sh ~/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091`. Archivo probado sintéticamente, **sin resultados físicos adicionales todavía**.



> **20-11-2026 — Segunda corrida real (HEAD `608332778`):** `foamMultiRun` y `checkMesh fluid/mold` PASS; ahora **10/10 `.dat`** de los function objects de Foundation14 detectados en nueva copia `FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091`. El traslado a `system/functions` quedó **verificado en WSL para escritura de archivos**, no sus contenidos numéricos. Falta leer las series originales antes de certificar flujos de masa/calor; las métricas `f_s=0` descritas más abajo pertenecen a la **primera** corrida. **SIN contracción ni alimentación implementadas.** [Bitácora de ambas corridas](../../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md).



> **20-11-2026 | RESULTADO REAL DE FS-C06 + CORRECCIÓN FOUNDATION14:** en los dos pasos nativos (`1e-7`, `2e-7 s`) `V_metal=4.801191628e-5 m³`, `V_sólido=0`, `f_s=0`, `T.metal=1499.9970068→1499.9965641 K`, `ΔVOF=0`. Cuatro monitores buscados en `postProcessing` devolvieron cero archivos. Causa identificada: en Foundation 14 los **function objects se leen desde `system/functions`**, pero FS-C06 los había colocado dentro del `controlDict` (sintaxis histórica). Los diez monitores (3 volumen, 5 flujo de masa, 2 flujo térmico) se trasladaron a [`native/system/functions`](native/system/functions), el stager los copia y valida, y el gate ahora **rechaza** PASS si no se escriben sus diez archivos `.dat`. **Corrección en Git no verificada aún con un segundo arranque WSL; sin contracción ni alimentación física.** [Bitácora con tabla de resultados](../../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). Las descripciones anteriores de monitores en `controlDict` son históricas y no describen la configuración actual.



> **20-11-2026 | GATE NATIVO WSL SUPERADO (salida de consola del investigador):** `foamMultiRun` completó dos pasos Foundation14; `run_native_gate.sh` anunció `FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE` y `checkMesh` aprobó `fluid` y `mold`. Copia aislada `FS_C06_VOF_SOLID_SMOKE_20261121T031743Z_200ccb63` (ejecución HEAD `99dfe9cc1`). **No se han recuperado los archivos originales para verificar métricas/hashes; no se acreditan contracción, alimentación, solidificación positiva ni balances de masa/energía.** [Bitácora y siguiente fase](../../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). Los apartados históricos que dicen «no ejecutado» describen estados anteriores y quedan reemplazados por esta actualización.


## 20-11-2026 — Corrección de dos `fvModels` nativos en Foundation 14

La revisión de la transición FS-C05→FS-C06 encontró un defecto del caso **OpenFOAM**: el generador original reescribía completamente `constant/fluid/fvModels` con una única fuente `VoFSolidificationMelting`, eliminando el modelo de amortiguamiento `compressible::VoFTurbulenceDamping` que FS-C05 usaba junto a `RAS kEpsilon`. El efecto era **cambiar silenciosamente las ecuaciones turbulentas de la superficie libre**, incluso si se lograban escribir campos `alpha.metal.solid`.

Se corrigió la composición del **diccionario nativo**, no sus valores de materiales: ahora se conserva textualmente el `fvModels` heredado de FS-C05 (incluidos `turbulenceDamping`, `delta 1e-4` y cabecera `constant/fluid`) y se agrega **una sola vez** el bloque nuevo `FS_C06_vof_phase_change` de tipo `VoFSolidificationMelting`. El generador rechaza el modelo ausente, duplicado, una cabecera/región incorrecta o una fuente de cambio de fase preexistente. La trazabilidad del reporte incluye SHA-256 de la fuente heredada y del archivo generado. Las regresiones en `test_stage_fs_c06_vof_solidification.py` cubren preservación, presencia de ambos términos y contraejemplos negativos.

Evidencia: se trata de **configuración de solver corregida en Git, pendiente de ejecución nativa**. CI sintética verifica la composición de los dos modelos; solo un **ensayo aislado real Foundation 14 con `foamMultiRun`** puede verificar su carga efectiva y escritura `alpha.metal.solid`. Todavía **no se ha implementado** `rho_l(T)`, `rho_s(T,f_s)`, contracción por continuidad, alimentación ni validación QuickCup. No modificar ni reutilizar resultados viejos FS-C05 como si se hubieran ejecutado con los dos modelos nuevos.

Fuente oficial de tipos Foundation14: https://cpp.openfoam.org/v14/classFoam_1_1fv_1_1compressible_1_1VoFTurbulenceDamping.html y https://cpp.openfoam.org/v14/classFoam_1_1fv_1_1VoFSolidificationMelting.html.


**20-11-2026 | Candidato de compatibilidad Foundation 14.** Se desarrolló un
stager independiente para activar el modelo real
`Foam::fv::VoFSolidificationMelting` sobre una copia nueva del caso **FS-C05**
previamente auditado. El modelo **no altera** C14, B14, C3D-04, C3D-05 ni
resultados FS-C05.

## Por qué este modelo

El código fuente **Foundation 14**, no OpenCFD ni otra edición, contiene
`applications/modules/compressibleVoF/fvModels/VoFSolidificationMelting`.
Esta clase consulta `compressibleTwoPhaseVoFMixture`, modifica energía de
fase metal mediante calor latente y momento de mezcla mediante Darcy, y
genera automáticamente `alpha.metal.solid` (AUTO_WRITE) a partir de
`alpha.metal` y una curva `alphaSolidT(T)`.

Documentación oficial:
- https://cpp.openfoam.org/v14/classFoam_1_1fv_1_1VoFSolidificationMelting.html
- https://cpp.openfoam.org/v14/VoFSolidificationMelting_8C_source.html
- https://cpp.openfoam.org/v14/VoFSolidificationMelting_8H_source.html

**Significados que no pueden confundirse**:
- `alpha.metal`: VOF **metal frente al aire**, 0–1.
- `alpha.metal.solid`: fracción **absoluta de volumen del metal sólido en la
  celda**, 0 ≤ `alpha.metal.solid` ≤ `alpha.metal`. La fracción sólida
  *condicional dentro del metal* sería `alpha.metal.solid/alpha.metal` solo
  donde hay metal; no dividir en celdas gaseosas.
- `alpha.metal - alpha.metal.solid`: fracción volumétrica líquida en la celda
  en esta representación, **no una ecuación de pérdida de volumen**.

## Contrato numérico, sin hacer pasar C14 por datos físicos

El generador **lee**, no copia sin comprobar, el archivo C14
`cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/metal/fvModels`
y guarda su SHA-256. Usa `Tsol=1423 K`, `Tliq=1473 K`,
`L=2.286×10⁵ J/kg`, `relax=0.1`, `Cu=10⁵ s⁻¹`,
`q=0.001` como **referencia numérica**; interpola linealmente
`alphaSolidT` entre sólido=1 a 1423 K y sólido=0 a 1473 K.

**NO se transfiere** el parámetro C14 `alpha1e`: no forma parte de la
interfaz nativa del modelo VOF. No se cambian las propiedades hierro/arena
ni densidades del FS-C05. Se mantiene el metal inicialmente a 1500 K,
por encima del liquidus: los primeros dos pasos son **solo un smoke test
de carga de modelo y escritura de fracción**, NO evidencia de que
la solidificación haya empezado en ese tiempo físico.

## Ejecución aislada

Solo cuando se decida comprobar el módulo nativo en WSL, una única orden,
sin repetir tests del desarrollador por pieza:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE &&
git fetch origin research/fs-c02-metal-air-vof-20261117 &&
git switch --detach FETCH_HEAD &&
python3 analysis_tools/stage_fs_c06_vof_solidification.py \
  --source ~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e \
  --native
```

Sin `--native` solo copia/prepara la entrada; con `--native` ejecuta
2 pasos a Δt=10⁻⁷ s únicamente en
`~/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_<id>`.
Escribe `FS_C06_REPORT.json`, log nativo y verifica `alpha.metal.solid`
real en dos instantes. El código está **por verificar en WSL Foundation 14**:
CI sintética, aun verde, NO acredita carga real de `fvModel`.

## Puertas físicas pendientes antes de decir 'contracción'

1. Verificar en WSL la carga nativa del modelo, campos de fracción y
   correcta contribución a entalpía y momento con un ensayo térmico
   que realmente atraviese liquidus (no se ha hecho).
2. Incorporar una ley respaldada de `rho_s(T,f_s)` y `rho_l(T)`,
   reconciliar la continuidad y los flujos de masa con `alpha.metal`.
3. Observar desplazamiento de superficie libre asociado a densidad y
   alimentación líquida, no inferirlo solo de `alpha.solid`.
4. Separar potencia metal–arena de aire–arena, y cerrar masa/entalpía
   por atmósfera abierta (FS-C05 solo verificó reciprocidad térmica total).
5. Incluir expansión por grafitización cuando sea física pertinente,
   propiedades JMatPro trazables, geometría de taza real, malla/Δt,
   y curvas QuickCup para validación experimental.

**Estado canónico de FS-C06: CODE_PREPARED, NO_NATIVE_RUN, NO_SHRINKAGE,
NO_FEEDING, NO_EXPERIMENTAL_VALIDATION.**

## Auditoría geométrica añadida a FS-C06 (20-11-2026)

Cuando una ejecución **nativa y aceptada** produzca los dos snapshots
`1e-7` y `2e-7`, el mismo stager ahora calcula directamente desde
`constant/fluid/polyMesh` los volúmenes *ponderados por volumen de celda*
`Σ(V_i·alpha.metal_i)` (metal VOF),
`Σ(V_i·alpha.metal.solid_i)` (metal sólido absoluto) y
`Σ[V_i·(alpha.metal_i-alpha.metal.solid_i)]` (metal líquido).
Incluye `f_s=V_s/V_m`, promedio de temperatura del metal, proporción de
metal a T≤1473 K (referencia numérica C14), cambio relativo de volumen
VOF contra t=0 y hashes de los campos realmente leídos. El campo
`alpha.metal.solid` **no** se interpreta como contracción; fracción sólida
volumétrica no equivale a pérdida de volumen.

Estas mediciones requieren **campos reales escritos por Foundation14**.
Las pruebas Python son puramente sintéticas: no demuestran que el
modelo se cargue ni que haya pasado el liquidus. No se dispone todavía
de densidades de sólido/líquido termodinámicamente sustentadas,
flujos másicos por atmósfera ni balance global: `mass_conservation_verified=false`
y `volumetric_shrinkage_or_feeding_verified=false` incluso si las
mediciones geométricas son positivas. El estado canónico continúa
siendo **CODE_PREPARED_NOT_NATIVE_VERIFIED**.

## Correccion del lector nativo de FS-C06 (20-11-2026)

El postproceso presentaba un bloqueo: intentaba leer el campo `alpha.metal.solid` con
`read_alpha()`, una funcion que solo acepta el objeto `alpha.metal`.
Por tanto, un campo nativo valido se habria rechazado aunque OpenFOAM 14 lo escribiera.

Se incorporo `read_native_solid_fraction()` con identificacion estricta de
`volScalarField`, `object alpha.metal.solid`, formato ASCII, campo interno
uniforme/no uniforme, cantidad de celdas y comprobacion de valores finitos.
El lector original de `alpha.metal` permanece intacto.
Pruebas nuevas cubren casos validos, objeto equivocado, conteos inconsistentes,
datos truncados, binarios, no finitos y campo ausente.

La correccion no constituye una corrida nativa ni demuestra solidificacion o
contraccion volumetrica. FS-C06 sigue `CODE_PREPARED_NOT_NATIVE_VERIFIED`.
El siguiente paso sigue siendo la ejecucion aislada en WSL Foundation 14
para comprobar los archivos `alpha.metal.solid` y la carga del fvModel.
El ensayo de dos pasos parte de 1500 K, sobre el liquidus numerico C14:
NO se deben presentar dos campos escritos como evidencia de cambio de fase real.

### Campo de temperatura correcto del modelo nativo

El metodo `VoFSolidificationMelting::correct()` de Foundation 14
evalua `thermo1().T()` para la curva `alphaSolidT`.
En este caso la fase 1 es `metal`: el dato que debe auditarse es
el campo nativo `T.metal`, **no** el campo de mezcla `T`.
El lector FS-C06 ahora valida por separado ambos objetos nativos
`alpha.metal.solid` y `T.metal` sin cambiar los lectores historicos.
Todos los promedios termicos y la fraccion metal por debajo del
liquidus C14 en el reporte FS-C06 provienen de `T.metal`.
Se registran los SHA-256 de ambos archivos observados.
El uso de `T.metal` tampoco acredita, por si mismo, solidificacion:
la prueba nativa debe mostrar descenso de temperatura y solidificacion
durante una corrida fisicamente suficiente.
Referencia oficial: https://cpp.openfoam.org/v14/VoFSolidificationMelting_8C_source.html

## Pantalla de densidades trazables (FS-C06 — Operación Granada)

Se añadió `analysis_tools/screen_fs_c06_density_contraction.py` junto con
regresiones numéricas. **No es un solver de contracción**: lee exclusivamente un
informe nativo aceptado `FS_C06_REPORT.json`, calcula una hipótesis de masa
inicial fija con densidades constantes expresamente proporcionadas por el
investigador, y escribe un resultado separado. No toca el caso, ni ejecuta
OpenFOAM, ni se habilita por sí solo en las simulaciones.

Entrada material obligatoria (JSON externo, NO se inventa ni versiona ninguna
densidad de hierro real):

```json
{
  "schema": "masterproject-fs-c06-density-input-v1",
  "material_id": "composicion-y-condicion-metalurgica-verificada",
  "source_kind": "jmatpro_export",
  "source_reference": "identificador-de-la-fuente",
  "source_file_sha256": "SHA256_DE_64_HEX_DIGITOS_DEL_ARCHIVO_ORIGINAL",
  "rho_liquid_kg_m3": 0,
  "rho_solid_kg_m3": 0,
  "density_reference_temperature_K": 0,
  "graphitization_handling": "not_modelled"
}
```

**Los ceros del ejemplo son marcadores deliberadamente inválidos**, no datos
para usar. Deben sustituirse por valores físicos trazables y comprobar el
SHA-256 del archivo original de JMatPro/medición. Para un ensayo posterior
al nativo (no ejecutar mientras no haya densidades), el comando es:

```bash
python3 analysis_tools/screen_fs_c06_density_contraction.py \
  --native-report /ruta/FS_C06_REPORT.json \
  --density-json /ruta/density.json \
  --density-source /ruta/exportacion_original \
  --out /ruta/NUEVA_FS_C06_DENSITY_SCREEN.json
```

Para cada instantánea calcula `M*=rho_s*V_s+rho_l*V_l` y
`V_cerrado*=M0/[rho_s*f_s,vol+rho_l*(1-f_s,vol)]`, donde
`M0=rho_l*V_metal(t0)`. El término `f_s,vol=V_s/V_metal` es **fracción
sólida volumétrica**, no másica. Un cambio de `V_cerrado*` con densidades
introducidas es solo **escenario hipotético de masa fija y sin alimentación**.
No debe confundirse con `alpha.metal` desplazándose en el solver real.
Densidades constantes no sustituyen `rho_l(T)`, `rho_s(T,f_s)` ni
expansión grafítica; si cambia su signo puede resultar expansión en vez de
contracción, sin que esto valide la grafitización.

El script bloquea archivos de salida preexistentes y reportes sin evidencia
nativa. Rechaza inventarios incompatibles o falta de huellas de campos
`alpha.metal`, `alpha.metal.solid`, `T.metal`. Sin flujo másico
metal/aire por contornos, sin balance global de entalpía y sin movimiento
de superficie medido: `mass_conservation_verified=false`,
`volumetric_shrinkage_verified=false`,
`feeding_verified=false` obligatoriamente.

### Integridad adicional del informe nativo (Granada)

Antes de calcular hipótesis de densidad, la herramienta **vuelve a leer** en
la carpeta original de ejecución aislada los campos `alpha.metal`,
`alpha.metal.solid` y `T.metal` de ambos instantes; sus SHA-256 deben
coincidir con `FS_C06_REPORT.json`. Un reporte JSON que se atribuya
un resultado nativo pero no incluya esos archivos se rechaza. Esto
verifica integridad de evidencia **guardada**, no demuestra de nuevo
convergencia, fase, cierre de masa ni validación experimental. El informe
de pantalla se guarda **fuera del directorio de la corrida** (creación
exclusiva, nunca sobrescritura). Las pruebas CI fabrican archivos
sintéticos y verifican alteraciones de SHA o rutas, no corren CFD.

## Política de desarrollo fijada por el investigador (20-11-2026)

**Este es un proyecto OpenFOAM Foundation 14, NO un proyecto Python.**
El entregable principal es un **caso CFD nativo funcional y científicamente
defendible**: malla y regiones, diccionarios `0/constant/system`,
`compressibleVoF` acoplado a arena, modelo de solidificación,
termofísica de hierro y aire, conservación de masa, densidades, evolución
física de superficie libre y, si el solver nativo no basta, extensión C++
identificada y verificada. Los scripts Python existentes son auxiliares;
una nueva pantalla o CI verde no equivale a avanzar el solver.

**Próxima Operación Granada:** priorizar trabajo real de modelo y archivos
OpenFOAM sobre nuevos auditores Python; documentar qué ecuaciones y fuentes
físicas están implementadas, cuáles no, y mostrar evidencia de ejecución
nativa solo cuando exista. El caso sigue sin contracción volumétrica
implementada. No introducir densidades o expansión grafítica ficticias.

## FS-C06: diccionarios ejecutables nativos Foundation 14 (Granada P, 20-11-2026)

La autoridad de la **configuración que OpenFOAM leerá** ya es un par de
diccionarios versionados y visibles, no un bloque de texto generado por Python:

- [`native/constant/fluid/fvModels`](native/constant/fluid/fvModels): conserva
  `compressible::VoFTurbulenceDamping` del FS-C05 y activa
  `VoFSolidificationMelting` en `cellZone all`, con coeficientes **de
  cribado numérico C14**, no termofísica calibrada. Dos modelos fv registrados;
  no se sobrescribe el amortiguamiento turbulento existente.
- [`native/system/controlDict`](native/system/controlDict): conserva los
  solvers `compressibleVoF` en `fluid` y `solid` en `mold`, ejecución
  corta aislada y escritura cada paso. Incluye **dos `volFieldValue` de OpenFOAM**
  para medir directamente `volIntegrate(alpha.metal)` y
  `volIntegrate(alpha.metal.solid)` sobre toda la región fluid, sin usar
  Python para efectuar estas integrales. `writeFields false` evita duplicar
  campos de la malla; el modelo escribe `alpha.metal.solid` automáticamente.

El orquestador **solo copia fielmente** los diccionarios nativos a una
copia nueva ya mallada del FS-C05 y verifica que no se aparten de las
fuentes C14/FS-C05. **No se ejecutan OpenFOAM o CFD en CI.** Se mantiene
el único comando de aceptación WSL indicado arriba; sus archivos
`constant/fluid/fvModels` y `system/controlDict` son copias exactas
de las fuentes nativas versionadas. Esto no altera ningún FS-C05 existente.

**Ecuaciones y alcance de esta etapa:** Foundation 14 añade al balance
de energía el término de calor latente mediante
`L*fvc::ddt(rho, alphaSolid)` y al momento una resistencia Darcy
regulada por `Cu`, `q` y fracción sólida. `alpha.metal.solid` se
actualiza desde `T.metal` multiplicando por `alpha.metal`. **Nada de
esto cambia por sí solo la ley de densidad de metal en la ecuación
de continuidad ni demuestra contracción o alimentación**.

**Condición inicial:** hierro a 1500 K (> liquidus de cribado 1473 K).
Dos pasos de 1e-7 s son un **test de carga/escritura**, no un transitorio
físico de solidificación. Siguiente ruta: una ejecución nativa aislada
confirmando los dos fvModels y los monitores, después un ensayo térmico
que atraviese el liquidus; solo luego continuidad con `rho_l(T)`,
`rho_s(T,f_s)`, flujo de masa por la atmósfera, desplazamiento de la
superficie y curva QuickCup real. No introducir coeficientes
inventados ni reivindicar una contracción sin un modelo conservativo.

## 20-11-2026 — Instrumentación de flujos MÁSICOS nativos del solver

Se amplió el `native/system/controlDict` **ejecutable por OpenFOAM 14**
con **cinco `surfaceFieldValue`**, además de los anteriores `volFieldValue`.
El cambio es en el caso OpenFOAM; no se creó un analizador Python nuevo.
Las superficies de aire incluyen `atmosphereTop`, `atmosphereSides`,
`atmosphereLowerSides` y se mide también `fluid_to_mold` para
detectar un flujo espurio a través de la interfaz térmica impermeable.

Cada monitor escribe `sum(alphaRhoPhi.metal)`,
`sum(alphaRhoPhi.air)` y `sum(rhoPhi)`, en kg/s según el modelo de
flujo compresible. Las dos primeras son los **flujos transportados de
masa por cada fase**, que Foundation 14 construye y actualiza en
`compressibleVoF.C` (`alphaRhoPhi1`, `alphaRhoPhi2`); no son
aproximaciones `alpha.metal*rhoPhi` inventadas. La suma firmada
en las fronteras es la base para el futuro balance de conservación
por fase. Se añadió un monitor `volIntegrate(rho)` para el
**inventario de masa de mezcla gas+metal** en la región fluida.

Estos monitores no atribuyen pérdida de volumen a solidificación:
`rhoPhi` y la masa de mezcla no distinguen sólido/líquido del metal,
y `alphaRhoPhi.metal` no contiene una ley `rho_s(T,f_s)`.
El sello `open_boundary_mass_balance_verified` permanece falso
hasta comparar **series NATIVAS reales** de inventario, flujo y
términos fuente. El test de 2×1e-7 s tampoco demuestra enfriamiento
a través del liquidus, contracción o alimentación.

Fuentes OpenFOAM Foundation 14:
- https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-14/master/applications/modules/compressibleVoF/compressibleVoF.C
- https://cpp.openfoam.org/v14/classFoam_1_1functionObjects_1_1fieldValues_1_1surfaceFieldValue.html

## FS-C06 — flujos térmicos conjugados en el MISMO caso nativo (20-11-2026)

El `system/controlDict` de FS-C06 contiene ahora **dos objetos OpenFOAM
`wallHeatFlux`**: `FS_C06_wallHeatFluxFluid` (`fluid_to_mold`) y
`FS_C06_wallHeatFluxMold` (`mold_to_fluid`), usando la sintaxis
Foundation14 probada previamente en el instrumento FS-C05. Los registros
de `Q` en W de ambas caras serán generados **por OpenFOAM** en la
misma única corrida FS-C06, junto con los integrales volumétricos de
VOF y masa y los flujos por fase en las tres fronteras atmosféricas.

**No se ha ejecutado FS-C06 nuevo**, y no se ha comprobado ni
reciprocidad térmica de FS-C06 ni conservación de masa. La validación
energética global requiere términos de entalpía, presión y atmósfera;
la implementación de densidad y contracción está pendiente. No
confundir la reciprocidad FS-C05 histórica con un resultado FS-C06.


## 20-11-2026 — Puerta GRANADA de aceptación nativa integrada en la rama activa

Se incorporó [`run_native_gate.sh`](run_native_gate.sh) a la rama de trabajo
`research/fs-c02-metal-air-vof-20261117` desde su desarrollo aislado, sin
modificar FS-C05 ni los casos C3D. Es un **único comando**, no una colección de
micropruebas manuales. Exige el entorno Foundation14, ejecuta el stager de
FS-C06 en una **copia nueva**, comprueba los dos modelos de `fvModels`,
que `system/controlDict` y `fvModels` son idénticos a los diccionarios nativos
versionados, que `foamMultiRun` finaliza dos pasos, y realiza `checkMesh
-allGeometry -allTopology` en **fluid y mold**. Conserva los logs y
`FS_C06_REPORT.json` en la copia independiente.

Desde Ubuntu/WSL con OpenFOAM Foundation 14 cargado:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE && \
git fetch origin research/fs-c02-metal-air-vof-20261117 && \
git switch --detach FETCH_HEAD && \
bash freesurface/FS-C06_vof_solidification/run_native_gate.sh \
  ~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e
```

Esta integración en Git **NO constituye una corrida FS-C06 efectuada**. El
`PASS` de esta puerta, cuando ocurra en WSL, solo acredita lectura del caso,
mallado y escritura nativa de `alpha.metal.solid`; no demuestra reducción
física de volumen, alimentación, conservación global o validación QuickCup.
Los primeros 2 × 1e-7 s, con T inicial de metal 1500 K, tampoco atraviesan
necesariamente el liquidus de referencia 1473 K. Siguiente bloque de física:
propiedades trazables `rho_l(T)` y `rho_s(T,f_s)`, modificación consistente
de la ecuación conservativa de masa, superficie libre y un transitorio que
realmente solidifique. No introducir densidades ficticias.
