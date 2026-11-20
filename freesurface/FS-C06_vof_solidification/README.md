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
