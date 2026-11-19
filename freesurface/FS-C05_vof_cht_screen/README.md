# FS-C05 — Primer candidato físico de VOF + transferencia térmica conjugada 3D (OpenFOAM Foundation 14)

**Estado:** herramienta de preparación disponible en el PR #51. **NO se ha creado ni ejecutado el caso FS-C05 en la laptop**, ni se ha comprobado su lectura por los solvers nativos. Los ensayos de FS-C03, FS-C04, `alpha`, `T` e interfaces ya completados permanecen INTACTOS y no se deben volver a ejecutar como sustitutos de avanzar en física.

## Qué aporta realmente

El tutorial **oficial de OpenFOAM Foundation 14**, `$FOAM_TUTORIALS/multiRegion/CHT/VoFcoolingCylinder2D`, utiliza el ejecutable `foamMultiRun` con los módulos `fluid compressibleVoF` y `solid solid`. Fuente directa: `https://github.com/OpenFOAM/OpenFOAM-14/tree/master/tutorials/multiRegion/CHT/VoFcoolingCylinder2D`. Por tanto, **sí existe una arquitectura oficial que puede acoplar VOF + CHT**. Para el QuickCup se adapta el nombre de regiones a `fluid` y `mold`: el fluido único contiene metal líquido y aire, mientras que arena sigue siendo sólido.

```foam
regionSolvers
{
    fluid           compressibleVoF;
    mold            solid;
}
```

El script `analysis_tools/stage_fs_c05_vof_cht.py` toma **la copia FS-C04 con dos campos de T inicial** y exige la aceptación nativa del postprocesamiento de ambas regiones. Comprueba de nuevo el `alpha.metal` (2368 hierro, 32000 aire), los 3136 pares de contacto arena–fluido y la identidad de `T`. Luego copia todo a un **nuevo directorio** `~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_<UTC>_<id>` y agrega, *solo sobre la copia*, los diccionarios y campos del tutorial oficial adaptados.

**El caso físico propuesto contiene:**
- `0/fluid/{alpha.metal,T,T.air,T.metal,p,p_rgh,U,k,epsilon,nut,alphat}`, `0/mold/T`.
- `constant/fluid/{phaseProperties,physicalProperties.metal,physicalProperties.air,momentumTransport,fvModels,g}`; `constant/mold/{physicalProperties,fvModels}`.
- `system/{controlDict,fvSolution,fluid/fvSchemes,fluid/fvSolution,mold/fvSchemes,mold/fvSolution}` derivados de Foundation14.
- Interfaces **`fluid_to_mold` y `mold_to_fluid` con `coupledTemperature`**, en lugar de los `calculated` anteriores. Aire abierto por `atmosphereTop`, `atmosphereSides` y `atmosphereLowerSides`; `T` del aire reentrante provisional 300 K; `p_rgh` `prghTotalPressure`; `U` `pressureInletOutletVelocity`.
- RAS `kEpsilon` + `compressible::VoFTurbulenceDamping` heredados de FS-C01 (se mantiene la intención investigativa de turbulencia, **sin calibración metalúrgica**). El tutorial oficial usa configuración laminar de referencia, que no se importa como modelo final.
- `endTime=5e-6 s`, `deltaT=1e-7 s`, `maxCo=0.1`, `maxAlphaCo=0.1`, `nEnergyCorrectors=2`: **solo una propuesta inicial de estabilidad, NO parámetros validados**.

## Propiedades provisionales y límites

| Material | Valores de prueba que se instalarán | Estado |
|---|---|---|
| Metal | `rho=6820 kg/m³`, `Cv=827 J/(kg·K)`, `mu=0.0055 Pa·s`, `Pr=0.14`, `sigma=1.0 N/m` | Heredados del ensayo FS-C02; **no** JMatPro ni curvas validadas |
| Aire | `perfectGas`, `Cp=1007 J/(kg·K)`, `Pr=0.7` | Propiedades provisionales del ensayo FS-C01 |
| Arena | `rho=1500 kg/m³`, `Cv=700 J/(kg·K)`, `k=2 W/(m·K)` | **Constantes provisionales**, no medidas para el molde |
| Temperaturas iniciales | Metal 1500 K; aire y arena 300 K | Valores de cribado, NO termopares experimentales |

La `alpha.metal` representa fracción VOF metal/gas, **NO fracción sólida**. No hay calor latente, cambio de fase, grafitización, presión de contracción, feeding ni geometría STL fiel. En el molde, `moldBottom` y las caras del hueco inferior se ponen **adiabáticas provisionalmente** con `zeroGradient`; esto NO es la condición física final y puede afectar radicalmente la curva de enfriamiento. Se deberá resolver el contacto con soporte y la exposición real al aire bajo la arena. No extrapolar el pequeño ensayo de 5 microsegundos a curvas QuickCup.

**El script NO invoca `foamMultiRun`, `foamRun`, `blockMesh` ni crea resultados físicos.** Su manifiesto deja `VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD`, `solver_executed=false`, `VOF_CHT_energy_balance_validated=false`. Antes de autorizar el ensayo nativo hay que validar sintaxis/modelos de Foundation14 y revisar flujos de calor en ambos lados de la interfaz, presión del aire y conservación de masa. Este paso de generación de entradas NO se confunde con un solver exitoso.

## Cómo preparar el candidato aislado

Primero, **verificar en Ubuntu que el estado nativo FS-C04 T ya es verde**. Directorios conocidos del investigador:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_stage_fs_c05_vof_cht.py -v &&
python3 analysis_tools/stage_fs_c05_vof_cht.py \
  --source ~/OpenFOAM/FS_C04_T_INITIAL_RUNS/FS_C04_T_INITIAL_STAGE_20261119T054751Z_b2a08cb7 \
  --native-T-accepted ~/OpenFOAM/FS_C04_T_NATIVE_CHECKS/FS_C04_T_NATIVE_CHECK_20261119T055532Z_7145a68b
```

Opcional `--tutorial <ruta>` para instalaciones cuyo `$FOAM_TUTORIALS` no apunte a la ruta estándar. El script exige que el tutorial **real instalado** contenga `compressibleVoF` y `solid`, y verifica que los archivos críticos estén disponibles. Mantiene el FS-C04 original en modo de solo lectura y rechaza destinos existentes. `FS_C05_PHYSICS_CANDIDATE.json` guarda procedencia, propiedades y banderas de validación.

**No ejecutar directamente `foamMultiRun` sobre este candidato sin pasar una auditoría de entrada de Foundation14.** Aún no se ha comprobado que las constantes heredadas, BC turbulentas, esquema energético y geometría aproximada produzcan una solución estable; podría fallar incluso al cargar los diccionarios. Hay que inspeccionar errores reales y corregir el modelo sin esconderlos.

## Qué constituye avance físico verificable

1. **Gate de lectura/arranque nativo** de ambos módulos y BC, sin trucar campos o relajar errores.
2. **Ensayo CHT de duración corta** con `foamMultiRun` únicamente en copia aislada; confirmar que hay intercambio real (q_{m metalightarrow arena}) y (q_{m arenaightarrow aire}), con continuidad del flujo térmico en interfaces ((q_{m fluid}+q_{m mold}approx0)).
3. **Masa/energía y malla**: conservar `∫ alpha.metal dV` dentro de tolerancias; revisar (T_{m metal}), arena superior/lateral, `Co`, `maxDeltaT`, `p_rgh`, flujos por las fronteras abiertas y sensibilidad en distancia del contorno.
4. **Prueba de CAD y soporte**: no interpretar temperaturas como experimentales antes de usar STL exactos y condiciones reales de apoyo. Después propiedades (ho(T), C_p(T), k(T)) de aleaciones y arena; por último solidificación y contracción.

**Referencia externa de arquitectura (OpenFOAM 14, sin copiar archivos al repo):** tutorial oficial `VoFcoolingCylinder2D` de Foundation14; `foamMultiRun`, `compressibleVoF`, `solid` y `coupledTemperature`. Documentación de Foundation14: `https://doc.cfd.direct/openfoam/user-guide-v14/thermal-boundary-conditions`.
