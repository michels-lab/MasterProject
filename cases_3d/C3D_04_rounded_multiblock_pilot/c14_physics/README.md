## 20-11-2026 — C14 original 10 s nativo en 3D: CI verificada y ejecutor protegido

[PR #60 integrado](https://github.com/michels-lab/MasterProject/pull/60) mediante [commit d3b1f86](https://github.com/michels-lab/MasterProject/commit/d3b1f865076f2527976ae0db481bc6a5aaec5bbd). En [CI Foundation14 #44860515973](https://github.com/michels-lab/MasterProject/actions/runs/44860515973) se prepararon **DOS candidatos independientes de la misma geometría sintética 3D** (27 metal + 27 arena):

- **Modelo de investigación preparado, NO ejecutado:** `endTime=10 s`, `deltaT=0.001 s`, `writeInterval=100`; el `system/controlDict` mantiene **identidad byte por byte** con C14, así como los archivos termofísicos, `fvModels`, `fvSchemes` y `momentumTransport`. Los **22 diccionarios** se analizaron con `foamDictionary` de OpenFOAM Foundation 14, con copia completa de malla verificada por SHA. Esta evidencia **NO** significa CFD de 10 segundos.
- **Ensayo separado SÍ ejecutado:** `endTime=0.002 s` en carpeta diagnóstica y sin alterar material ni modelo; dos pasos reales `foamMultiRun` con `metal=fluid`, `mold=solid`, `h/e/U/p_rgh` y `solidificationMeltingSource`. NO es V4/T02, y el inicio de solidificación no se observó.

Para ejecutar una **única corrida nativa completa de los 10 s originales** sobre una **copia aislada de V4/T02** en WSL, desde la raíz de un `MasterProject` actualizado:

```bash
bash cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_native_milestone.sh --run-full
```

El script utiliza la malla aceptada **solo en lectura** bajo `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02`; verifica evidencia, regiones, parches, celdas metálicas, `cellZone` y referencia numérica de presión; crea el caso **solo si el destino está vacío** en `~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01`, y confirma antes de lanzar `foamMultiRun` que el `controlDict` se conserva *exactamente* como en C14. Si el solver falla, quedan los logs y el informe del directorio aislado. Si termina, requiere `End`, tiempo 10 s, selección del solver, resolución de `h/e/p_rgh` y campos finales nativos. Una ejecución completa todavía requiere comprobar **conservación, estabilidad, evolución de fracción líquida, independencia de malla y QuickCup** antes de declarar validez física.

**No se ha ejecutado todavía esta orden en WSL/V4-T02.** El estado permanece **etapa 6/10, 5/10 hitos completados = 50 % operativo**; el estado histórico no cuenta como validación física y el ensayo sintético no cierra el hito 06.


## 20-11-2026 — FOUNDATION14: CFD nativo real del C14 original PASÓ en malla sintética 3D

[**GitHub Actions run #44859479359, SUCCESS**](https://github.com/michels-lab/MasterProject/actions/runs/44859479359) y [**artifact original #14689152079**](https://github.com/michels-lab/MasterProject/actions/runs/44859479359/artifacts/14689152079). Se ejecutaron **dos pasos nativos foamMultiRun a 0.001 y 0.002 s** de las regiones sintéticas **metal fluido de 27 celdas y arena sólida de 27 celdas**, con los archivos fuente C14 intactos. El log demuestra explícitamente:

- `Selecting solver fluid` (metal), `Selecting solver solid` (mold) y **`Selecting solidificationMeltingSource with name phaseChangeSource`**. No se sustituyó `heRhoThermo/Cp/sensibleEnthalpy` por `heSolidThermo/Cv`.
- Se resolvieron `h` en el metal, `e` en la arena y **`p_rgh` con GAMG**; se escribieron `U,T,p,p_rgh,rho,phi,phaseChangeSource:alpha1`.
- A 0.002 s, `T.metal` cubrió **1499.92–1499.98 K**, `T.mold` **300–300.238 K**, `p_rgh` aproximadamente **100000–100002 Pa**. `alpha1` seguía en **1**, coherente con T inicial 1500 K > liquidus 1473 K. **No demuestra evolución de sólido ni liberación de calor latente**.
- El archivo de evidencia se preservó **dentro de un ZIP nativo** porque el proveedor GitHub Actions no permite subir directamente nombres que incluyen dos puntos, como `phaseChangeSource:alpha1`. Las condiciones originales y nombres de campo sí están intactos dentro del ZIP.
- El primer ensayo de una celda por región falló por diagonal de presión cero en un dominio sintético degenerado. Se sustituyó **sólo la discretización del fixture sintético** por 3×3×3 celdas y se mantuvieron todos los parámetros físicos y numéricos de C14.

**Límite científico estricto:** el pase de CI es un **CFD de un caso sintético aislado**, NO el CFD sobre la V4/T02 de 8960+12352 celdas en la laptop del investigador. Esa corrida, la conservación de energía 3D, la independencia de malla, el inicio de solidificación y QuickCup están pendientes. **Etapa 06/10, 5/10 hitos=50% operativa.** El bloque siguiente consiste en una **sola ejecución WSL** del [runner C14 nativo](run_c14_native_milestone.sh) contra la malla preservada.

## 20-11-2026 — Preparador nativo para V4/T02 (modelo FÍSICO C14, hierro fluido)

El bloque `stage_c14_3d_case_a.py` materializa por primera vez el **modelo completo del C14 fluido–sólido** sobre la malla aceptada V4/T02 sin tocar el original: copia la geometría de las regiones verificadas, comprueba SHA-256 de los cinco archivos de malla por región, conserva los 14 diccionarios heredados del C14 salvo una adaptación geométrica necesaria en `fvSolution`, genera los ocho campos 3D desde parámetros C14 y añade exclusivamente la zona de celdas `metal` a la **copia** de `polyMesh` cuando la malla fuente no contiene ya una zona completa verificable. Si existe una zona `metal` original que no selecciona todas las celdas, se detiene en lugar de reemplazarla silenciosamente.

La geometría real tiene **8960 celdas metálicas y 12352 celdas de arena** según los logs nativos previamente aprobados; el nuevo script exige contarlas **de nuevo de las listas de etiquetas originales owner/neighbour**, para que no haya un número de zona inventado. El antiguo `pRefPoint (0.02 0.04 0.005)` de C14 es una coordenada 2D que no sirve para la zona geométrica 3D, por lo que se transforma en **`pRefCell 0`**, un índice que pertenece al rango real de celdas verificado. Se conserva **`pRefValue 1e5`**, como en C14. Cambiar la ubicación del dato de presión sin cambiar su magnitud es una adaptación numérica/de referencia, no una nueva propiedad de material; su efecto sobre el resultado deberá comprobarse. El código fuente oficial de Foundation 14 valida que `pRefCell` esté dentro de [0,nCells): https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-14/master/src/finiteVolume/cfdTools/general/findRefCell/findRefCell.C

**No se alteran** el modelo `heRhoThermo` con entalpía h y Cp, la arena `heSolidThermo` con energía e y Cv, los parámetros `Tsol,Tliq,L,alpha1e,beta,rhoRef,relax,Cu,q`, la gravedad y ecuaciones de presión-momento, las condiciones térmicas y sus valores, ni el C14 archivado. Las BC 3D sustituyen la condición `empty` exclusiva del 2D. Para reproducir fielmente la fuente se mantiene el tiempo base **0–10 s con deltaT 0.001 s** en `--materialize`; sólo el ensayo `--smoke` en su carpeta nueva modifica **endTime 0.002 s y writeInterval 1** para registrar dos pasos nativos, conservando el mismo deltaT.

**ÚNICA orden de trabajo WSL cuando CI esté verde** (desde un worktree de MasterProject con estos cambios):
```bash
bash cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_native_milestone.sh --smoke
```
El runner comprueba identidad de fuentes y propiedades originales, configura Foundation14 una sola vez, aplica las puertas de malla V4/T02 aceptada y copia en forma aislada a `~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_SMOKE_01`. Si un diccionario se rechaza **antes** de finalizar la publicación, no deja salida final incompleta. Si el solver falla después de comenzar, conserva los registros originales para el diagnóstico. Nunca lanzar `blockMesh` o `checkMesh` sobre el T02 aceptado. Para preparar la versión completa de 10 s **sin ejecutar CFD**, el mismo runner acepta `--materialize` y crea un segundo directorio separado.

**CI [workflow C14 nativo](../../../.github/workflows/c3d04-a-c14-native-fluid-solid.yml)**: prueba dos cubos 3D de una celda con hierro `fluid`, arena `solid` y **solidificationMeltingSource original**, verificando lectura del modelo, no resolución térmica/metalúrgica en la geometría auténtica. Esta prueba por sí sola nunca cierra la etapa 06 ni demuestra latencia/solidificación (T0=1500 K > Tliq=1473 K). El Caso A de investigación **sigue pendiente de su primera corrida nativa en V4/T02**, verificación de conservación e independencia de malla. Etapa 6/10, 5/10 hitos operativos = 50 %, sin cierre científico.


# Caso 3D-A C3D-04 — física fuente exacta de C14

**Decisión del investigador (20 de noviembre de 2026):** el Caso A debe usar **las variables, el modelo termofísico, la formulación del solver y el cambio de fase del C14 2D original**, ajustando sólo la dimensionalidad/topología y la sintaxis mínima que requiere OpenFOAM Foundation 14. **No** sustituir el hierro fluido por dos sólidos, añadir constantes escogidas sin fuente, copiar física VOF de FS-C06, o atribuir validación al T0 auxiliar.

## Fuente científica y parámetros: no escogidos por el asistente

Archivo base: `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/`. Contrato legible por máquina: [C14_3D_PHYSICS_CONTRACT.json](C14_3D_PHYSICS_CONTRACT.json). La fidelidad se compara directamente contra los archivos fuente originales, incluidos ocho Git blob SHA-1 previamente fijados, por el [auditor y ensamblador](c14_source_fidelity.py). **Los originales no se modifican.**

| Magnitud/modelo | C14 exacto | Qué debe hacer la versión 3D-A |
|---|---|---|
| Regiones | metal = `fluid`; mold = `solid` | Conservar; metal no es `solid` |
| Termofísica hierro | `heRhoThermo / hConst / sensibleEnthalpy` | Conservar Cp, energía `h` |
| Termofísica arena | `heSolidThermo / eConst / sensibleInternalEnergy` | Conservar Cv, energía `e` |
| Densidad metal / arena | 6820 / 1500 kg/m³ | Conservar las constantes originales |
| Capacidad calorífica | Cp hierro 827 / Cv arena 700 J/(kg K) | **No hacer Cp→Cv en metal** |
| Transporte metal | mu 5.5×10⁻³ Pa·s, Pr 0.14 | Conservar `const`, no inventar k(T) |
| Conductividad arena | 2 W/(m K) | Conservar |
| Iniciales | metal 1500 K, arena 300 K; U=(0 0 0), p=p_rgh=1e5 Pa | Conservar, llevar a geometría 3D |
| Cambio de fase | `solidificationMeltingSource`, `energy h` | No reemplazar por un modelo distinto |
| Solidus / liquidus | 1423 K / 1473 K | Conservar |
| Calor latente / alpha1e | 228600 J/kg / 0.8 | Conservar ambos |
| Enthalpy–porosity | relax 0.1, Cu 1e5, q 0.001 | Conservar |
| Flotación del modelo | beta 1.13×10⁻⁴ K⁻¹, rhoRef 6820 kg/m³ | Conservar |
| Gravedad / momento | g=(0,-9.81,0) m/s²; laminar | Conservar |
| U en tapa/contacto | slip / noSlip | Conservar topología física impermeable de C14 |
| p_rgh en tapa/contacto | fixedFluxPressure | Conservar |
| Calor exterior | h=10 W/(m²K), Ta=300 K, emissivity metal .3 / arena .5 | Conservar; sólo usar sintaxis F14 `externalTemperature` con `h uniform 10` |
| Contacto | coupledTemperature, 0.0002 m / 0.1 W/(m K) | Conservar resistencia original |
| Tiempo | deltaT 0.001 s; fin 10 s; write cada 100 | Conservar controles base originales; reducción futura sólo para ensayo aislado y explícito |
| Configuración | maxCo .25, adjustTimeStep=no, PIMPLE root 3/2/1 | Conservar; **.25 no es Courant observado** |
| `nEnergyCorrectors` | 2 escrito regionalmente, 1 efectivo según bitácora/logs C14 | **No** promocionarlo erróneamente como 2 efectivos |

## Diferencias 2D→3D que requieren evidencia, no parámetros arbitrarios

1. `frontAndBack empty` es exclusivo de la representación 2D original; en C3D-04 hay que imponer BC a **todos** los parches físicos no vacíos de V4/T02. La fuente tiene `metalTop`, `metal_to_mold`, `moldTop`, `moldExterior`, `moldBottom`, `moldRecessWall`, `moldRecessRoof`.
2. `system/metal/fvSolution` trae `pRefPoint (0.02 0.04 0.005)` de la geometría 2D. No es seguro reutilizarlo en el nuevo dominio y; no elegir una coordenada 3D sin verificar su pertenencia a una celda metálica real. Conservar `pRefValue=1e5`.
3. `constant/metal/fvModels` apunta a `cellZone metal`. Antes de arrancar, exigir una selección **verificada** de todas las celdas reales de metal en la región 3D; si el zone local no existe, no saltar ni desactivar el cambio de fase.
4. **No se ha materializado ni ejecutado** el modelo fluido–sólido sobre V4/T02. El auditor genera en memoria ocho campos de arranque y ensambla en memoria **22 entradas** (14 archivos originales C14 sin transformación y ocho campos iniciales con BC 3D adaptadas). Ésta es una comprobación de proveniencia y cobertura, **no un nuevo CFD**.

## Relación con el T0 anterior

El T0 de **dos sólidos** sigue siendo una prueba numérica separada de arranque/acoplamiento térmico, no representa la física principal del Caso A exigida aquí. Las pruebas 3D sintéticas anteriores con `foamMultiRun` sólo demostraron que dos regiones sólidas podían iniciar y transferir calor. **No** justifican usar `heSolidThermo` para el hierro de C14 ni desactivar `U,p_rgh,alpha1e,L,beta`.

**Estado canónico del plan operativo anterior:** etapa **6/10**, **5/10 hitos = 50 %**, que mide hitos de geometría/preparación incluyendo T0 auxiliar. **Avance físico de la transferencia C14 fluido–sólido:** aún sin corrida 3D ni validación. El siguiente bloque real es resolver la referencia de presión/cellZone sobre malla V4/T02 preservada y materializar/ejecutar el modelo original adaptado sin otros parámetros.

