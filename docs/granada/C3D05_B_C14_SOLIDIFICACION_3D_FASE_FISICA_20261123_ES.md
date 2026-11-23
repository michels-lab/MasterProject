# Caso B C3D-05 — integración de física de solidificación C14 original en malla CAD→Gmsh→HEX8

**Preparado:** 23 de noviembre de 2026. **Estado:** código de materialización y de ejecución nativa publicado; **no se ha ejecutado aún el modelo fluido/sólido C14 real sobre la malla B en la WSL**. No inferir ejecución por commits, código, pruebas estáticas ni resultados de la etapa de conducción T0.  
**Caso B canónico:** etapa **3/7**, avance **2/7=29 % hitos técnicos**, G3/G4 físicos y G5 solidificación abiertos; no es porcentaje de tesis.

## 1. Qué resultado anterior queda preservado

**C3D05/B – T0 anterior:** malla CAD STEP–Gmsh Delaunay–subdivisión HEX8 de **270,788 celdas** (92,200 metal; 178,588 arena), 12,636 caras de contacto por región y 1,826 caras con no ortogonalidad >70°. El ensayo numérico C14 archivado de **dos sólidos**, propiedades constantes, sin solidificación ni flujo metálico, completó 0.1 s en `~/OpenFOAM/C3D05_T0_C14_SHK_01`. Su expediente de temperaturas, energía, flujos por pareja y q en 12 bandas se conserva. No es un QuickCup real ni se utilizará como si fuese solidificación.

## 2. Qué avanzamos ahora

Se añadió `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/` con:

- `stage_c14_3d_case_b.py`: preparador protegido que utiliza `c14_source_fidelity.py` y el ensamblaje original C14 del **Caso A**, preservando **14 diccionarios de fuente**, termofísica de hierro como **fluido** y termofísica del molde como **sólido**, con la misma física y valores que el C14 2D. No pasa furtivamente a dos sólidos, Cp como Cv ni propiedades JMatPro inexistentes.
- `run_case_b_c14_native.sh`: entrada única a OpenFOAM **Foundation 14**, con modos `--preflight` (solo verificar fuente), `--materialize` (preparar nuevo caso 3D), `--run-full` (preparar y ejecutar **una vez** los **10 s originales**).
- `tests/test_stage_c14_3d_case_b.py`: **8 pruebas de origen/contrato, mapeo de frontera, rechazo de zonas erróneas y no sobreescritura**. Son pruebas de código; no reemplazan ejecución de la malla real.
- `.github/workflows/c3d05-b-c14-3d-phase-source.yml`: QA de sintaxis, origen y fronteras. **No corre CFD**.

### Contrato físico preservado, sin nuevas constantes

El hierro recupera `heRhoThermo`, `hConst`, `sensibleEnthalpy`, `U`, `p`, `p_rgh`, campo `phaseChangeSource:alpha1` y `solidificationMeltingSource` con los `Tsol,Tliq,L,alpha1e,beta,rhoRef,relax,Cu,q` **exactos del C14 2D versionado**. El molde recupera `heSolidThermo`, `eConst`, `sensibleInternalEnergy`, `T` y su energía `e`. También conserva gravedad, presión, `fvSchemes`, `fvSolution`, parámetros de contacto `coupledTemperature` con capa C14, condiciones ambientales `externalTemperature` y todos los controles `controlDict` de C14 sin cambiar **`endTime=10 s`, `deltaT=0.001 s`, `writeInterval=100`**.

Las únicas transformaciones habilitadas son debidas a la geometría:

1. Las cinco fronteras exteriores del molde del diseño C3D04-A se unen en la frontera real **`moldOuterUnclassified` de B** solo si sus cinco definiciones térmicas originales son **literalmente idénticas** (misma `h`, `Ta`, emisividad, tipo y expresiones). Un cambio parcial bloquea la operación. La frontera `mold_to_metal` no cambia.
2. El `pRefPoint` de 2D se sustituye por el **`pRefCell 0`** interno verificado de la región de 92,200 celdas; conserva `pRefValue=1e5 Pa`. La selección de celda es una adaptación geométrica de presión, no validación de independencia respecto de esa referencia.
3. La zona `metal` de `solidificationMeltingSource` debe cubrir **exactamente los índices 0..92199**. Si la fuente no tiene `cellZones`, se crea en la copia; si está vacía, se reemplaza en la **copia aislada**; si contiene una zona distinta o parcial, **se bloquea**. El original nunca se modifica.

El preparador comprueba procedencia y registros aceptados del STEP/malla del Caso B, totales de celdas, volúmenes, interfase, no ortogonalidad documentada y SHA de los archivos `polyMesh` originales frente a la copia. Rechaza parches adicionales imprevistos. La malla de origen y todos sus resultados anteriores se tratan como **solo lectura**.

**Destino independiente:** `~/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01`. Ese directorio no es `C3D05_T0_C14_SHK_01` (T0 previo); no es el Caso A; no es la rama de contracción. Si existe, se preserva y **no se permite una segunda corrida automática**. Falla de preparación conserva una carpeta aislada de evidencia; falla del solver deja log/estado para diagnóstico.

## 3. Orden integral para la laptop WSL (cuando corresponda ejecutar el hito)

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_case_b_c14_native.sh --run-full
```

**No ejecutada en este turno:** crea la copia de la malla/entradas sólo tras validar todo y, si pasa, lanza el original `foamMultiRun` 10 s / 10,000 pasos. El éxito exige log final `End`, `Time = 10s`, ambos modelos regionales `fluid/solid`, selección de `solidificationMeltingSource`, solución de `h/e/p_rgh` y campos nativos finales `T/U/p_rgh/alpha1`. No se vuelve a correr el T0. Se estima más costosa que la corrida A por su mayor número de celdas; **no se promete tiempo ni estabilidad**. El parámetro `--materialize` sirve para preparar sin solver si se requiere inspección antes de una ejecución prolongada, pero no cierra G5.

## 4. Límites científicos y verificaciones pendientes

La geometría STEP y HEX8 es **real**, pero los coeficientes C14 son **un modelo de referencia físico-numérico heredado**, **no propiedades `ρ(T),Cp(T),k(T)` específicas de las ocho fundiciones**, ni una medición JMatPro, ni una calibración QuickCup. Se evita crear `alpha1` sintética o fijar un inicio ficticio de solidificación. El nuevo cálculo, aun si termina, requiere revisar `alpha1(t)`, `T(t)`, (L) y tasa de energía, además de distribución del frente, estabilidad, efecto de 1,826 caras no ortogonales, convergencia temporal/espacial y comparación con curvas reales. La evolución de `alpha1` no se marca observada simplemente porque el campo exista a t=10 s.

### Hitos

| Hito | Estado |
|---|---|
| G1 – CAD STEP y procedencia | CERRADO |
| G2 – HEX8 y contacto | CERRADO |
| G3 – T0 con propiedades físicas trazables | ABIERTO |
| G4 – T0 físico y balance validado | ABIERTO |
| G5 – cambio de fase/calor latente en B verificado | ABIERTO: **preparador C14 fuente publicado, CFD B NO ejecutado** |
| G6 – contracción y alimentación | ABIERTO |
| G7 – convergencia y curvas experimentales | ABIERTO |

**Observación importante:** preparar la física C14 en la malla B es un avance técnico hacia G5, **no reemplaza** los requisitos de G3/G4 con materiales reales. El avance 2/7=29% permanece sin cambio hasta evidencia de cierre de los hitos.
