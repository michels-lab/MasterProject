# FS-C06 — VOF + cambio de fase, sin contracción todavía

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
