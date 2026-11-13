## 12-11-2026 — surfaceCheck en Foundation 14 sin suponer opción outputThreshold

**Resultado cuantitativo del ensayo:** `snappyHexMesh` había creado 568,135 celdas tras la etapa de baffles y seleccionó **568,134** para conservar. Retiró solo **una**; el exterior nunca quedó aislado. Repetir con otro `insidePoint` ya se probó sin cambios.

La instalación local **no anunció las dos opciones** que nuestro script anterior exigía simultáneamente, y por eso no ejecutó `surfaceCheck`. El diagnóstico corregido usa `-checkSelfIntersection` **solo si `surfaceCheck -help` la anuncia**, o ejecuta la comprobación topológica básica si no. El programa puede escribir `selfInterPoints.obj`, `badFaces` o `problemFaces` en algunas versiones; por eso se llama desde un **directorio temporal, nunca dentro del caso fuente**.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/inspect_mold_leak.sh
```

Ninguna malla nueva ni solver. Esperar a la salida de `surfaceCheck` antes de decidir si el STL requiere reparación o hay otra causa del recorte. Referencia de sintaxis/capacidades: código fuente de `surfaceCheck` de la rama Foundation y documentación: https://cpp.openfoam.org/v13/surfaceCheck_8C_source.html .

---

## 12-11-2026 — Lección: una superficie cerrada no garantiza la separación de volúmenes en snappyHexMesh

**Hecho comprobado:** el ensayo mold-only con nuevo punto interior fuera de cara de `blockMesh` **repitió exactamente el fallo previo** (568,134 celdas, 242.142 cm³, `outerBox` 15,164 caras, 2 checks fallidos). Un `insidePoint` es la semilla del componente que se conservará; si existe una conectividad no deseada a través de la superficie discretizada, la selección puede retener el exterior. Un STL cerrado topológicamente no descarta autointersecciones ni fugas de discretización. **No seguir cambiando semillas, sin resultados discriminantes.** La documentación de Foundation 14 requiere una superficie que encierre completamente los componentes deseados durante la eliminación de celdas: https://doc.cfd.direct/openfoam/user-guide/snappyhexmesh.

**Inspección sin volver a generar mallas (comando único):**

```bash
source /opt/openfoam14/etc/bashrc
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/inspect_mold_leak.sh
```

La utilidad lee logs `mold` y `mold_offface_01`, compara selección de celdas, volumen y fallos, muestra contexto de selección de `snappyHexMesh` y, si están disponibles las opciones Foundation 14 `-checkSelfIntersection` y `-outputThreshold`, ejecuta `surfaceCheck` sobre STL reparado sin escribir reparaciones ni generar malla. **No se cambia ningún archivo fuente, STL ni caso CFD.** Reportar la salida para determinar la estrategia siguiente.

---

## 12-11-2026 — insidePoint SOBRE cara de blockMesh: corrección localizada del molde

**Hallazgo a partir de la salida real del investigador:** `metal` tiene volumen 47.9621 cm³ (≈47.9875 CAD), `outerBox=0`, pero 2,422 celdas cóncavas. `mold` conserva exterior (242.142 cm³ frente a 102.8431 cm³; `outerBox=15164` caras), 13,367 celdas cóncavas y 10 face-tets malos. **Ni una de las dos mallas está aprobada.**

**Regla Foundation 14 (manual `snappyHexMesh`):** el `insidePoint` no debe caer sobre ninguna cara de celda antes ni durante el refinamiento. Con x min = −3 mm y 29 celdas sobre 58 mm, las caras del mallado inicial están en x=−3,−1,1,**3**,5,… mm. Se había usado **`x=3 mm`**, precisamente una cara, aunque el punto era interior al STL. La prueba corregida propone `(4.3,-20.7,25.9)` mm = `(0.0043 -0.0207 0.0259)` m; se comprobó mediante geometría STL que cae dentro del molde. No está demostrado todavía que ese cambio corrija toda la fuga exterior.

**Comando único, solo arena y sin sobrescribir hierro ni mold originales:**

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/try_mold_offface.sh
```

Se creará únicamente `~/OpenFOAM/C3D02_materials/mold_offface_01` si no existe, con `blockMesh`, `snappyHexMesh` y `checkMesh -allGeometry -allTopology`. Las salidas separan selección de celdas, calidad, volumen y `outerBox`. Si no pasa, **no repetir al azar**. Los otros subcasos conservan sus logs `retry1` sin cambios. No ejecutar solver.

---

## 2026-11-12 — Error por falta de allowFreeStandingZoneFaces en snappyHexMesh (Foundation 14)

**Error comprobado en dos materiales:** `FOAM FATAL IO ERROR: keyword allowFreeStandingZoneFaces is undefined in castellatedMeshControls`. La opción es requerida por el lector de diccionario de la instalación Foundation 14. En el caso `C3D_02_metal_sand_clean`, incluir en `system/materialSingle/snappyHexMeshDict.template`:

```cpp
castellatedMeshControls
{
    // Otras opciones conservadas...
    insidePoint (0.0259 -0.0200 0.0259);  // Ejemplo: solo metal
    allowFreeStandingZoneFaces false;
}
```

**No lanzar `run_material_meshes.sh` nuevamente:** ahora existe `~/OpenFOAM/C3D02_materials`. La corrección está versionada, y el comando seguro de continuación es:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/resume_material_meshes.sh
```

Comprueba el error exacto y las dos mallas de fondo existentes; preserva logs anteriores, reescribe únicamente los diccionarios derivados de la plantilla nueva, ejecuta `snappyHexMesh -overwrite` y `checkMesh -allGeometry -allTopology` en cada subcaso. Si alguna precondición no se cumple, aborta. **Sin CFD, sin `subsetMesh`, sin remallar `blockMesh`, sin suponer interfaces CHT.** [Evidencia](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

---

## 2026-11-12 — Dos mallas físicas independientes, un comando (C3D-02, PENDIENTE DE EJECUTAR)

Después de comprobar que `insidePoints` conservó la caja exterior (589,701 celdas, 242.130 cm³), se definió un método nuevo: **un solo STL y un `insidePoint` por malla de material**, dentro de un solo workspace. Sin `subsetMesh`, `topoSet` ni `splitMeshRegions` y sin modificar los casos anteriores.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/run_material_meshes.sh
```

Se crean `~/OpenFOAM/C3D02_materials/metal` y `~/OpenFOAM/C3D02_materials/mold` (si el directorio raíz no existía). Cada subcaso escribe `log.blockMesh`, `log.snappyHexMesh`, `log.checkMesh.full`; compara contra 47.9875 y 102.8431 cm³ respectivamente, comprueba que `outerBox` no conserve caras y rechaza defectos de `checkMesh`. Este control **no prueba contacto térmico entre mallas independientes** ni ejecuta solver. [Guía detallada](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

---

## 12-11-2026 — C3D-02: diagnóstico sin remallado después del primer fallo

**Resultado real de `run_mesh_only.sh`:** 589,701 celdas, **242.130 cm³**, 1 región conectada, 2 fallos exhaustivos (`face-tets 10`, `concaveCells 14,586`). El volumen hierro+arena nominal es 150.831 cm³. Se conserva exterior; no declarar `snappyHexMesh` aprobado.

Comando **de solo lectura** (NO ejecutar de nuevo `run_mesh_only.sh`):

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/diagnose_mesh_readonly.sh
```

La salida registra selección de regiones, remoción de celdas, parches y zonas y usa logs existentes en `~/OpenFOAM/C3D02_mesh`. Si no existen los logs, aborta sin crear otra carpeta. `insidePoints` en Foundation 14 está orientado a conservar regiones desconectadas; **no separa dos materiales por sí solo**. [Bitácora del fallo](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

---

## 2026-11-12 — Primer mallado C3D-02 SIN reutilizar mallas previas

Un único comando desde el caso nuevo, respaldado en GitHub:

```bash
source /opt/openfoam14/etc/bashrc
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/run_mesh_only.sh
```

- `snappyHexMeshDict` de Foundation 14: `insidePoints` selecciona el interior del metal y el de la arena; el STL se escala desde mm mediante `geometry.*.units [mm]`.
- La carpeta de trabajo **única** es `~/OpenFOAM/C3D02_mesh`; si existe, el script no la sobrescribe.
- Se ejecutan `foamDictionary`, `blockMesh`, `snappyHexMesh -overwrite`, `checkMesh -allGeometry -allTopology` y un filtro inicial por volumen físico (~150.8306 cm³). No se ejecutan `topoSet`, `subsetMesh`, `splitMeshRegions` ni solver.
- La malla no está aceptada hasta comprobar ausencia de aire, calidad, `cellZones`, parches recíprocos y áreas CHT. **No atribuir éxito al código sin log real.**

[Guía C3D-02 completa](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

---

## Adenda práctica actualizada — 12 de noviembre de 2026 (OpenFOAM Foundation 14)

**Inicio recomendado:** [lecciones detalladas de los ensayos C3D, comandos, opciones y errores reales](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md). [Decisión científica y nuevo caso](docs/C3D_REINICIO_20261112_ES.md). Los capítulos siguientes documentan el historial; el nuevo caso fuente es `cases_3d/C3D_02_metal_sand_clean`, que **no se ha ejecutado**.

### Secuencia segura de trabajo

```bash
source /opt/openfoam14/etc/bashrc
cd ~/OpenFOAM/MasterProject
git status --short
# Desde el nuevo caso, comprobar que existe el controlDict:
test -f cases_3d/C3D_02_metal_sand_clean/system/controlDict
# Ayuda real de los comandos en tu instalación:
checkMesh -help
subsetMesh -help
splitMeshRegions -help
```

### Errores de sintaxis probados (NO repetir)
| Incorrecto / condición | Correcto / solución |
|---|---|
| `foamDictionary -entry castellatedMeshControls.insidePoints` | `-entry castellatedMeshControls/insidePoints` |
| `checkMesh -writeSets vtk` | `checkMesh -writeSets -setFormat vtk` (y `-writeSurfaces -surfaceFormat vtk`) |
| `subsetMesh keepMaterials -case ...` | `subsetMesh -cellSet keepMaterials -case ... -noFields` |
| caso `topoSet` sin `system/controlDict` | copiar/proporcionar `controlDict` antes de lanzar la utilidad |
| repetir `subsetMesh` sobre malla ya recortada | **No repetir**: los IDs del `cellSet` dejan de referir a esa malla; reconstruir en una copia de malla base |
| `splitMeshRegions -disconnected` implicaría una interfaz térmica | falso: apareció `No interfaces to add` |
| `checkMesh` básico `Mesh OK` significa validación | falso: `-allGeometry -allTopology` sigue detectando defectos |
| 5,334 `mappedWall` metal–surrounding = metal–arena | falso: `surrounding` contenía también exterior |

`topoSet` advierte deprecación hacia `createZones` en Foundation 14; **el aviso no fue causa del fallo**. Mantener `0/metal` y `0/mold`, `system/metal` y `system/mold`, `constant/metal/materials/castIron` y `constant/mold/materials/silica` como arquitectura del caso multi-región. Las BC 2D `frontAndBack type empty` **no se copian tal cual** al 3D. No usar `foamMultiRun` hasta validar geometría e interfaz.

---

# Manual práctico de comandos OpenFOAM — MasterProject / QuickCup

**Idioma:** 🇪🇸 Español | [🇬🇧 English](./OPENFOAM_COMMAND_MANUAL_EN.md) | [↩ Selector de idioma](./OPENFOAM_COMMAND_MANUAL.md)

> Manual operativo de uso rápido para el proyecto de tesis.
>
> **Objetivo:** encontrar una tarea, copiar el comando desde el bloque de código y pegarlo en la terminal sin tener que reconstruir la sintaxis cada vez.
>
> Este manual se mantiene **en paralelo** con `PROJECT_AUDIT_LOG.md`:
> - **Audit Log:** qué se hizo, por qué, evidencia, resultados y decisiones.
> - **Command Manual:** cómo repetir la acción paso a paso.

---

## Índice rápido

1. [Ir a la carpeta principal del proyecto](#1-ir-a-la-carpeta-principal-del-proyecto)
2. [Saber en qué carpeta estoy](#2-saber-en-qué-carpeta-estoy)
3. [Ver qué archivos y carpetas hay](#3-ver-qué-archivos-y-carpetas-hay)
4. [Entrar a un caso](#4-entrar-a-un-caso)
5. [Correr un caso con Allrun](#5-correr-un-caso-con-allrun)
6. [Limpiar un caso con Allclean](#6-limpiar-un-caso-con-allclean)
7. [Limpiar y volver a correr un caso](#7-limpiar-y-volver-a-correr-un-caso)
8. [Correr varios casos secuencialmente](#8-correr-varios-casos-secuencialmente)
9. [Ver el log mientras corre un caso](#9-ver-el-log-mientras-corre-un-caso)
10. [Ver las últimas líneas de un log](#10-ver-las-últimas-líneas-de-un-log)
11. [Comprobar si una corrida llegó a End](#11-comprobar-si-una-corrida-llegó-a-end)
12. [Buscar errores graves en el log](#12-buscar-errores-graves-en-el-log)
13. [Ver tamaño y fecha de un log](#13-ver-tamaño-y-fecha-de-un-log)
14. [Regenerar los logs de foamLog](#14-regenerar-los-logs-de-foamlog)
15. [Revisar timestep y control temporal](#15-revisar-timestep-y-control-temporal)
16. [Revisar correctores PIMPLE](#16-revisar-correctores-pimple)
17. [Recetas específicas: casos 6 y 7](#17-recetas-específicas-casos-6-y-7)
18. [Qué hace Ctrl+C](#18-qué-hace-ctrlc)
19. [Reglas para no contaminar comparaciones](#19-reglas-para-no-contaminar-comparaciones)
20. [Abrir un caso en ParaView](#20-abrir-un-caso-en-paraview)
21. [Perfiles lineales velocidad-temperatura — sugerencia del doctor](#21-perfiles-lineales-velocidad-temperatura--sugerencia-del-doctor)
22. [Buscar un archivo dentro del proyecto](#22-buscar-un-archivo-dentro-del-proyecto)
23. [Comprobar por qué Git ignora un archivo](#23-comprobar-por-qué-git-ignora-un-archivo)
24. [Actualizar y subir cambios del repositorio](#24-actualizar-y-subir-cambios-del-repositorio)
25. [Agregar deliberadamente un archivo ignorado por Git](#25-agregar-deliberadamente-un-archivo-ignorado-por-git)
26. [Flujo histórico B2/C2](#26-flujo-histórico-b2c2)
27. [MAZAPÁN — subir carpetas completas de casos](#27-mazapán--subir-carpetas-completas-de-casos)

---

## 1. Ir a la carpeta principal del proyecto

### Para qué sirve
`cd` significa **change directory**. Este comando te lleva directamente a la carpeta raíz del proyecto, sin importar dónde estés en la terminal.

### Comando

```bash
cd ~/OpenFOAM/MasterProject
```

### Ir directamente a los casos controlados de buoyancy

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy
```

---

## 2. Saber en qué carpeta estoy

### Para qué sirve
`pwd` significa **print working directory**. Imprime la ruta completa de la carpeta actual.

### Comando

```bash
pwd
```

Ejemplo esperado dentro de los casos controlados:

```text
/home/michel/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
```

---

## 3. Ver qué archivos y carpetas hay

### Para qué sirve
`ls` lista el contenido de la carpeta actual.

### Comando simple

```bash
ls
```

### Lista con tamaño y detalles

```bash
ls -lh
```

- `-l`: formato detallado.
- `-h`: muestra tamaños fáciles de leer, como KB o MB.

---

## 4. Entrar a un caso

Primero colócate en:

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy
```

### B6 — adaptive timestep

```bash
cd B6_adaptiveDt
```

### C6 — adaptive timestep

```bash
cd C6_adaptiveDt
```

### B7 — four outer correctors

```bash
cd B7_outer4
```

### C7 — four outer correctors

```bash
cd C7_outer4
```

### Volver una carpeta atrás

```bash
cd ..
```

---

## 5. Correr un caso con Allrun

### Para qué sirve
`./Allrun` ejecuta el script `Allrun` del caso actual.

En los casos controlados actuales, el script ejecuta:

1. `blockMesh`
2. `splitMeshRegions -cellZones all`
3. `foamMultiRun`
4. elimina los `logs/` derivados anteriores
5. `foamLog log.foamMultiRun`
6. crea `buoyant.foam` para postproceso

### Comando

```bash
./Allrun
```

**Importante:** ejecútalo desde dentro de la carpeta del caso correcto.

---

## 6. Limpiar un caso con Allclean

### Para qué sirve
`./Allclean` elimina resultados generados por una corrida anterior y devuelve el caso a un estado limpio para volver a ejecutarlo.

### Comando

```bash
./Allclean
```

### Cuándo usarlo
Úsalo antes de una corrida que quieras considerar **nueva y reproducible**.

### Precaución
No lo ejecutes si necesitas conservar resultados locales que todavía no hayas respaldado.

---

## 7. Limpiar y volver a correr un caso

### Para qué sirve
El operador `&&` ejecuta el segundo comando **solo si el primero terminó correctamente**.

### Comando

```bash
./Allclean && ./Allrun
```

Esto significa:

1. limpia;
2. si la limpieza termina bien;
3. corre el caso.

---

## 8. Correr varios casos secuencialmente

### Para qué sirve
Los paréntesis crean un **subshell**. Cada caso entra a su propia carpeta, corre allí y al terminar vuelve automáticamente a la carpeta desde donde se lanzó el bloque.

Por eso, si empiezas en `cases_controlled_buoyancy`, **NO debes usar `../C6_adaptiveDt` para el segundo caso**. Al terminar el primer subshell ya estás otra vez en `cases_controlled_buoyancy`.

### Ir primero a la carpeta correcta

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy
```

### Correr B6 → C6 → B7 → C7

```bash
(cd B6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

### Si B6 ya terminó y faltan C6, B7 y C7

```bash
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

### Por qué secuencial y no paralelo
Para las comparaciones del proyecto es preferible que los casos no compitan simultáneamente por CPU, RAM o I/O. Esto reduce una fuente innecesaria de variación en el tiempo de cómputo.

---

## 9. Ver el log mientras corre un caso

### Para qué sirve
`tail -f` muestra las últimas líneas de un archivo y continúa mostrando nuevas líneas conforme se escriben.

Es especialmente útil desde **una segunda terminal** mientras el solver sigue ejecutándose en la primera.

### Ejemplo: observar B6

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy/B6_adaptiveDt
tail -f log.foamMultiRun
```

### Salir de la vista en vivo
Pulsa:

```text
Ctrl+C
```

Si `tail -f` corre en una segunda terminal, esto cierra **solo tail**, no el solver que está ejecutándose en la primera terminal.

---

## 10. Ver las últimas líneas de un log

### Para qué sirve
`tail -n 30` muestra únicamente las últimas 30 líneas del archivo y termina inmediatamente.

### Comando

```bash
tail -n 30 log.foamMultiRun
```

Puedes cambiar `30` por otra cantidad.

---

## 11. Comprobar si una corrida llegó a End

### Método rápido

```bash
tail -n 20 log.foamMultiRun
```

Una corrida completa normalmente debe mostrar `End` al final.

### Buscar explícitamente End

`grep` busca líneas que contengan un patrón de texto. `-n` también muestra el número de línea.

```bash
grep -n "^End" log.foamMultiRun
```

Si no aparece nada, no asumas automáticamente que el caso terminó correctamente: revisa las últimas líneas y errores.

---

## 12. Buscar errores graves en el log

### Para qué sirve
`grep -E` permite buscar varios patrones a la vez usando una expresión extendida.

### Comando

```bash
grep -nE "FOAM FATAL|Segmentation fault|Floating point|Killed" log.foamMultiRun
```

Si no devuelve líneas, ninguno de esos textos fue encontrado.

### Buscar warnings

```bash
grep -ni "warning" log.foamMultiRun
```

- `-i`: ignora mayúsculas/minúsculas.

---

## 13. Ver tamaño y fecha de un log

### Para qué sirve
Sirve para comprobar que estás mirando el archivo correcto y distinguir una corrida nueva de un log antiguo.

### Comando

```bash
ls -lh --time-style=long-iso log.foamMultiRun
```

Muestra:

- permisos;
- tamaño;
- fecha;
- hora;
- nombre del archivo.

---

## 14. Regenerar los logs de foamLog

### Para qué sirve
`foamLog` extrae series del `log.foamMultiRun` para postproceso: residuals, Courant number, continuidad, iteraciones, tiempos, etc.

Antes de regenerarlos conviene borrar la carpeta `logs/` anterior para evitar mezclar datos viejos.

### Comando seguro desde dentro del caso

```bash
rm -rf logs
foamLog log.foamMultiRun
```

### En una sola línea

```bash
rm -rf logs && foamLog log.foamMultiRun
```

### Qué hace `rm -rf logs`
- `rm`: elimina.
- `-r`: elimina una carpeta y su contenido.
- `-f`: no pide confirmación.

**Precaución:** verifica con `pwd` que estás dentro del caso correcto antes de usar `rm -rf`.

---

## 15. Revisar timestep y control temporal

### Para qué sirve
Permite ver rápidamente los parámetros temporales más importantes de `system/controlDict` sin abrir el archivo entero.

### Comando

```bash
grep -E "^[[:space:]]*(endTime|deltaT|adjustTimeStep|maxCo|maxDeltaT)" system/controlDict
```

Para B6/C6 actualmente se espera algo equivalente a:

```text
endTime         10;
deltaT          0.001;
adjustTimeStep  yes;
maxCo           0.25;
maxDeltaT       0.1;
```

---

## 16. Revisar correctores PIMPLE

### Para qué sirve
Muestra rápidamente los correctores relevantes configurados en `system/fvSolution`.

### Comando

```bash
grep -E "nOuterCorrectors|nCorrectors|nNonOrthogonalCorrectors|nEnergyCorrectors" system/fvSolution
```

Configuraciones actualmente estudiadas:

- B3/C3: `nOuterCorrectors 2`
- B4/C4: `nEnergyCorrectors 2`
- B5/C5: `nOuterCorrectors 3`
- B6/C6: base de B5/C5 + `adjustTimeStep yes`
- B7/C7: `nOuterCorrectors 4`, timestep fijo

---

## 17. Recetas específicas: casos 6 y 7

### Correr solo B6

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy/B6_adaptiveDt
./Allclean && ./Allrun
```

### Correr solo C6

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy/C6_adaptiveDt
./Allclean && ./Allrun
```

### Correr solo B7

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy/B7_outer4
./Allclean && ./Allrun
```

### Correr solo C7

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy/C7_outer4
./Allclean && ./Allrun
```

### Correr C6, B7 y C7 después de que B6 ya terminó

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

---

## 18. Qué hace Ctrl+C

`Ctrl+C` envía una interrupción al proceso que está corriendo en **esa terminal**.

### Si el solver corre en esa terminal
Puede detener la simulación.

### Si solo estás viendo `tail -f` en una segunda terminal
Detiene únicamente la visualización en vivo de `tail`.

**Regla práctica:** antes de pulsar `Ctrl+C`, mira qué proceso está activo en esa ventana.

---

## 19. Reglas para no contaminar comparaciones

1. Limpiar el caso antes de una corrida que vaya a usarse en la comparación.
2. No reutilizar `logs/` antiguos después de generar un nuevo `log.foamMultiRun`.
3. Verificar fecha y tamaño del `log.foamMultiRun` cuando exista duda.
4. Confirmar que el solver llegó a `End`.
5. Buscar `FOAM FATAL`, segmentation faults, floating point exceptions y procesos killed.
6. Para comparar costo computacional, evitar correr los casos comparados al mismo tiempo.
7. Cambiar una variable numérica principal por prueba siempre que sea posible.
8. Registrar cada cambio relevante también en `PROJECT_AUDIT_LOG.md`.

---


## 20. Abrir un caso en ParaView

### Origen
Este comando ya se había usado en los casos históricos B2/C2 del proyecto.

### Para qué sirve
`paraFoam -builtin` prepara/abre el caso de OpenFOAM en ParaView usando el lector incorporado. El `&` deja ParaView ejecutándose en segundo plano y devuelve el control de la terminal.

### Comando

```bash
paraFoam -builtin &
```

En los casos anteriores este flujo podía crear un archivo `.foam`, por ejemplo `C2_test.foam`.

---

## 21. Perfiles lineales velocidad-temperatura — sugerencia del doctor

### Contexto
El doctor comentó obtener perfiles de **velocidad–temperatura** en OpenFOAM, referido en la conversación como “plotline”. El flujo de postproceso trabajado para esa indicación usa muestreo lineal sobre la región metálica.

### Ejecutar postproceso sobre el último tiempo

```bash
foamPostProcess -region metal -solver fluid -latestTime
```

### Qué significa
- `-region metal`: trabaja sobre la región `metal`.
- `-solver fluid`: usa el contexto de solver fluido para el postproceso.
- `-latestTime`: procesa únicamente el último tiempo disponible.

### Elementos del muestreo que ya habíamos considerado
Para construir los perfiles se trabajó con conceptos/configuraciones como:

```text
lineUniform
graphUniform
graphCell
fields (U T phaseChangeSource:alpha1);
```

Estos últimos son elementos de configuración de muestreo, **no comandos de terminal independientes**. La receta completa se irá conservando aquí conforme quede fijado el diccionario definitivo del proyecto.

---

## 22. Buscar un archivo dentro del proyecto

### Para qué sirve
`find` recorre carpetas y subcarpetas buscando nombres que coincidan.

### Comando histórico usado

```bash
find . -name "openfoam-solidification.agent.md"
```

### Qué significa
- `.`: empieza a buscar desde la carpeta actual.
- `-name`: busca por nombre exacto.

---

## 23. Comprobar por qué Git ignora un archivo

### Para qué sirve
`git check-ignore -v` indica si una ruta está siendo ignorada y muestra qué regla del `.gitignore` lo provoca.

### Comando histórico usado

```bash
git check-ignore -v cases_buoyancy/B2_test/10
```

Es especialmente útil cuando un resultado existe en tu computadora pero no aparece para hacer commit.

---

## 24. Actualizar y subir cambios del repositorio

### Descargar primero los cambios remotos

```bash
cd ~/OpenFOAM/MasterProject
git pull
```

### Ver qué cambió

```bash
git status
```

### Preparar todos los cambios

```bash
git add -A
```

### Crear el commit

```bash
git commit -m "Describe aquí el cambio"
```

### Subir a GitHub

```bash
git push origin main
```

### Flujo completo

```bash
cd ~/OpenFOAM/MasterProject
git pull
git status
git add -A
git commit -m "Describe aquí el cambio"
git push origin main
```

**Importante:** revisa `git status` antes de `git add -A` para no subir resultados pesados o archivos que no quieras versionar.

---

## 25. Agregar deliberadamente un archivo ignorado por Git

### Para qué sirve
`git add -f` fuerza la incorporación de una ruta aunque una regla de `.gitignore` normalmente la excluya.

### Plantilla

```bash
git add -f cases_controlled_buoyancy/<CASO>/postProcessing/<RUTA>
```

Sustituye `<CASO>` y `<RUTA>` por la ruta real.

### Precaución
Úsalo solo cuando **deliberadamente** quieras versionar ese resultado. No conviene forzar carpetas completas de resultados sin revisar su tamaño y utilidad.

---

## 26. Flujo histórico B2/C2

Estos comandos aparecieron en las primeras pruebas de los casos de buoyancy y siguen siendo útiles como receta básica.

### Ejemplo C2

```bash
cd ~/OpenFOAM/MasterProject/cases_buoyancy/C2_test
./Allclean
./Allrun
paraFoam -builtin &
```

### Ejemplo B2

```bash
cd ~/OpenFOAM/MasterProject/cases_buoyancy/B2_test
./Allclean
./Allrun
paraFoam -builtin &
```

### Error histórico útil
Si haces `cd ..` y después ejecutas:

```bash
./Allclean
```

desde una carpeta que no contiene ese script, Bash responderá `No such file or directory`. Usa `pwd` y `ls` antes de ejecutar scripts cuando tengas duda sobre tu ubicación.

---

## Próximas secciones que se añadirán conforme avance el proyecto

Este manual crecerá con los comandos que realmente usemos en la tesis, entre ellos:

- extracción y comparación de residuals;
- seguimiento de subiteraciones PIMPLE;
- Courant number y timestep adaptativo;
- muestreo de temperatura y fracción líquida;
- comparación B vs C;
- postproceso;
- ParaView;
- probes;
- perfiles espaciales;
- creación y clonación segura de nuevos casos;
- validación de malla;
- comandos Git específicos del proyecto cuando sean necesarios para reproducibilidad.

La regla será: **si durante el proyecto usamos un comando útil y reutilizable, se documenta aquí con explicación y bloque listo para copiar.**


---

## Flujo NARANJA — sincronizar resultados locales antes de documentar

**NARANJA** es el flujo de seguridad usado cuando la computadora local contiene resultados de simulación más recientes que GitHub.

Orden obligatorio:

1. **Local/PC primero.** Preservar y versionar los resultados válidos que ya existen en la computadora.
2. **GitHub después.** Integrar cualquier cambio remoto sin hacer `force push`.
3. **Análisis.** Usar el repositorio ya sincronizado como fuente de verdad para extraer métricas.
4. **Documentación al final.** Actualizar Audit Log, README y Command Manual solo después de que los resultados reales estén en GitHub.

Flujo estándar desde la raíz del repositorio:

```bash
git add -A
git commit -m "results: sync local simulation outputs"
git pull --rebase origin main
git push origin main
```

Si `git commit` responde `nothing to commit`, continuar con `git pull --rebase origin main` y `git push origin main`.

### Importante sobre `.gitignore`

`git add -A` **no añade archivos nuevos ignorados**. En este proyecto, directorios de tiempos calculados y la mayor parte de `postProcessing/` se ignoran deliberadamente para evitar inflar el repositorio.

Si un output ignorado debe conservarse científicamente, primero decidir qué subconjunto es útil y pequeño; luego añadir solo ese path de forma deliberada (por ejemplo con una excepción de `.gitignore` o, de forma puntual, `git add -f <path>`). No forzar automáticamente todos los time directories.

### No usar

No usar `git push --force` para resolver un rechazo por non-fast-forward cuando existen resultados locales válidos. Preferir `git pull --rebase` después de haber hecho commit de los cambios locales.


## Sincronización de resultados finales con Git (flujo NARANJA)

Cuando una tanda de OpenFOAM se ejecuta en la estación local y los resultados versionables deben convertirse en la nueva fuente de verdad:

1. Preservar primero los resultados locales válidos.
2. Añadir y confirmar los logs/resultados versionables.
3. Integrar después los commits remotos con `git pull --rebase`.
4. Subir con `git push`.
5. Solo después actualizar bitácoras, manuales o conclusiones de análisis.

Ejemplo:

```bash
git add -A
git commit -m "results: sync remaining local controlled-case data"
git pull --rebase origin main
git push origin main
```

No usar `force push` para resolver un remoto adelantado. Este flujo evita que documentación remota más reciente sustituya o confunda resultados que todavía existen únicamente en la máquina local.


---

## Validar el diagnóstico de `solidificationMeltingSource`

El bloque `solidificationMeltingMomentumDiagnostics` forma parte de `system/researchDiagnostics` en los casos controlados V3–V7. No cambia la física del caso; solo escribe campos derivados durante el solver.

Después de sincronizar:

```bash
cd ~/OpenFOAM/MasterProject
git pull origin main
```

Antes de correr toda la matriz, validar primero B7 y C7.

Comprobar que el bloque existe:

```bash
grep -n "solidificationMeltingMomentumDiagnostics" \
  cases_controlled_buoyancy/B7_outer4/system/researchDiagnostics

grep -n "solidificationMeltingMomentumDiagnostics" \
  cases_controlled_buoyancy/C7_outer4/system/researchDiagnostics
```

Durante la corrida, buscar en el log:

```bash
grep "solidificationMelting diagnostics" log.foamMultiRun
```

Después de una escritura válida, los directorios de tiempo de la región `metal` deben contener, entre otros:

```text
phaseChangeDarcyCoeff
phaseChangeDarcyAcceleration
phaseChangeBuoyancyAcceleration
pRghAcceleration
phaseChangeDragToBuoyancy
phaseChangeDragToPressure
```

### Interpretación rápida

- `phaseChangeDarcyCoeff` [1/s]: intensidad local del amortiguamiento de zona pastosa.
- `magPhaseChangeDarcyAcceleration` [m/s²]: magnitud de la desaceleración Darcy.
- `magPhaseChangeBuoyancyAcceleration` [m/s²]: escala local de flotación del modelo.
- `magPRghAcceleration` [m/s²]: escala de aceleración asociada al gradiente de `p_rgh`.
- `phaseChangeDragToBuoyancy`: razón entre amortiguamiento Darcy y flotación.
- `phaseChangeDragToPressure`: razón entre amortiguamiento Darcy y gradiente de presión.

No interpretar una razón grande cerca de denominadores casi nulos como evidencia física por sí sola; revisar también las magnitudes absolutas y la fracción líquida.


### Error de compilación `fvCFD.H` en coded function objects

Si aparece:

```text
fatal error: fvCFD.H: No such file or directory
Failed wmake "dynamicCode/..."
```

no interpretar esto como fallo del solver. Es un error de compilación del código dinámico. En este proyecto se corrigió reemplazando el include agregado `fvCFD.H` por headers específicos compatibles con OpenFOAM Foundation v14.

Después de sincronizar la corrección, limpiar y relanzar B7:

```bash
cd ~/OpenFOAM/MasterProject
git pull origin main
cd cases_controlled_buoyancy/B7_outer4
./Allclean
./Allrun
```


### Errores `timeName()` y `gMax(...).value()` en Foundation v14

Si el compilador muestra:

```text
no matching function for call to Foam::Time::timeName() const
request for member 'value' ... gMax ... non-class type 'double'
```

usar la API compatible empleada actualmente en el proyecto:

```cpp
m.time().timeName(m.time().timeOutputValue())
gMax(field)
```

y no:

```cpp
m.time().timeName()
gMax(field).value()
```


### `timeOutputValue()` no existe en OpenFOAM Foundation v14

Si aparece:

```text
const class Foam::Time has no member named timeOutputValue
```

usar:

```cpp
m.time().timeName(m.time().value())
```

La interfaz de `Time` de OpenFOAM 14 define `timeName(const scalar, ...)`; no usar `timeOutputValue()` en este proyecto.


## Postprocesar diagnósticos de momento sin rerun

Los casos controlados B3–B7/C3–C7 incluyen `system/momentumPostProcessing`. Si los directorios de tiempo ya existen, no es necesario repetir la simulación para generar las tablas y perfiles compactos:

```bash
cd <caso>
foamPostProcess \
    -region metal \
    -dict system/momentumPostProcessing \
    -time '0:' \
    -fields '(phaseChangeSolidFraction phaseChangeDarcyCoeff phaseChangeModelDeltaT phaseChangeDarcyAcceleration phaseChangeBuoyancyAcceleration pRghAcceleration magPhaseChangeDarcyAcceleration magPhaseChangeBuoyancyAcceleration magPRghAcceleration phaseChangeDragToBuoyancy phaseChangeDragToPressure)'
```

Las salidas aparecen en `postProcessing/` y sí se versionan con Git.

En corridas futuras, `Allrun` ejecuta este paso automáticamente después de `foamMultiRun` si el log alcanzó `End`.


Para regenerar este postproceso sobre todos los casos controlados existentes sin repetir CFD:

```bash
cd ~/OpenFOAM/MasterProject/cases_controlled_buoyancy
sh postprocess_momentum_all.sh
```

Cada caso escribe su salida de consola en `log.momentumPostProcess`.


Nota para casos multirregión: los function objects usados con `foamPostProcess` deben declarar explícitamente `region metal;`; no basta con pasar `-region metal` en la línea de comandos si el objeto intenta resolver la región por defecto `region0`.


---

## 27. MAZAPÁN — cierre completo de una corrida OpenFOAM

**MAZAPÁN** es el protocolo completo de cierre científico y documental de una o varias corridas del proyecto Quick-Cup. **No termina en el `git push`.**

Cuando Michel diga **“MAZAPÁN”** o **“haz MAZAPÁN”**, se debe ejecutar este flujo completo:

1. **Confirmar la corrida local**
   - comprobar `latestTime`;
   - comprobar `End`;
   - buscar `FOAM FATAL`, segmentation fault, floating point exception o procesos killed;
   - registrar el código de retorno cuando exista un runner.

2. **Sincronizar las carpetas completas de los casos**
   - añadir cada carpeta completa con `git add cases_controlled_buoyancy/<CASO>`;
   - dejar que `.gitignore` filtre automáticamente tiempos calculados, mallas generadas, archivos ParaView, imágenes, ZIP y demás outputs no versionables;
   - no enumerar manualmente `logs/`, `postProcessing/`, etc.;
   - no usar `git add -f` salvo una excepción explícita.

3. **Preservar primero los resultados locales**
   - commit local de resultados;
   - `git pull --rebase origin main`;
   - `git push origin main`;
   - nunca usar `force push` para resolver un remoto adelantado con resultados locales válidos.

4. **Verificar lo que realmente quedó en GitHub**
   - confirmar el commit;
   - confirmar que `logs/`, `postProcessing/` y demás evidencia científica necesaria sí quedaron versionados;
   - comprobar que outputs pesados/temporales no quedaron trackeados accidentalmente.

5. **Limpiar tracking accidental**
   - recordar que `.gitignore` no deja de rastrear archivos que ya estaban versionados;
   - si un tiempo calculado u otro output ignorado sigue trackeado, retirarlo del árbol/índice de Git **sin confundirlo con borrar el resultado local**;
   - verificar después que la ruta ya no esté trackeada.

6. **Auditar científicamente los resultados**
   Como mínimo, cuando existan:
   - flujo de masa en fronteras relevantes, incluido `metalTopPhiSum`;
   - energía advectiva y heat/energy flux;
   - residuos iniciales/finales de `p_rgh`;
   - contracción entre outer correctors;
   - continuidad;
   - Courant;
   - T, U, rho y fracción líquida;
   - balances y magnitudes integradas;
   - comparación contra el caso padre/baseline y contra la familia equivalente;
   - cualquier diagnóstico específico de la hipótesis probada.

7. **Separar estados de evidencia**
   - `RUN-VERIFIED`: terminó limpiamente;
   - `ANALYSIS-VERIFIED`: los resultados fueron auditados;
   - una corrida que da PASS **no** se declara físicamente válida solo por haber terminado.

8. **Crear o actualizar el registro de análisis**
   - guardar resumen reproducible en `analysis_results/` cuando el análisis lo amerite;
   - guardar métricas/tablas derivadas que permitan reconstruir la conclusión.

9. **Actualizar la bitácora global**
   - `PROJECT_AUDIT_LOG_ES.md`;
   - registrar qué se corrió, resultados, interpretación, decisión y nueva pregunta técnica.

10. **Actualizar las notas de CADA caso afectado**
    - `CASE_NOTES.md`: estado actual, resultados medidos, interpretación, advertencias y decisión;
    - `CASE_VARIANT.md`: propósito de la variante y conclusión posterior a la corrida;
    - no dejar una nota en modo “qué pretendemos probar” después de que el caso ya fue ejecutado y analizado.

11. **Actualizar documentación de comparación**
    Según lo que cambie:
    - README de la familia/prueba;
    - `VALIDATION_MATRIX_ES.md`;
    - documentación de baseline/casos canónicos.

12. **Actualizar las guías de aprendizaje**
    Si el resultado cambia o fortalece cómo entendemos el modelo:
    - `CASE_GUIDE_ES.md`;
    - `CASE_GUIDE_INTERACTIVE_ES.html`;
    - incorporar qué opción se probó, qué ocurrió realmente, qué opción queda como baseline y cómo defender la decisión oralmente.

13. **Actualizar el manual de comandos cuando aparezca un procedimiento reutilizable**
    - `OPENFOAM_COMMAND_MANUAL_ES.md`;
    - documentar comandos nuevos o corregidos que deban repetirse en futuras corridas.

14. **Reevaluar explícitamente la baseline**
    - decidir si la evidencia mantiene, reemplaza o limita la baseline vigente;
    - si la baseline cambia o queda reafirmada, reflejarlo en las notas de la baseline y de las variantes comparadas.

15. **Cerrar con verificación de consistencia documental**
    - ninguna guía debe llamar “pendiente” a una corrida ya analizada;
    - ninguna nota debe llamar “baseline” a una variante descartada;
    - los números de las notas deben coincidir con `analysis_results/`;
    - Git debe quedar sin outputs generados accidentalmente trackeados.

### Flujo Git de MAZAPÁN

```bash
cd ~/OpenFOAM/MasterProject

git add \
cases_controlled_buoyancy/<CASO_1> \
cases_controlled_buoyancy/<CASO_2>

git commit -m "results: add simulation outputs"
git pull --rebase origin main
git push origin main
```

### Regla corta

> **MAZAPÁN = sincronizar + auditar + decidir + documentar + limpiar + verificar consistencia.**

El `git push` es solo la mitad del flujo.


---

## 28. Agentes activos de investigación y diagnóstico del postprocesamiento (2026-10-08)

**Responsabilidades:** Michel ejecuta todas las simulaciones en su laptop con OpenFOAM Foundation 14. Después hace `git push` con los resultados. **GitHub no debe instalar ni ejecutar OpenFOAM, iniciar `Allrun`, `foamMultiRun`, `blockMesh` o repetir simulaciones.**

Una vez que los resultados están versionados, el workflow `.github/workflows/quickcup-research-audit.yml` intenta auditar los archivos: `log.foamMultiRun`, `logs/`, `postProcessing/`, `system/functions` y estado del inventario. Esto es una revisión de evidencia documental y numérica ya generada; no sustituye la interpretación física ni MAZAPÁN.

Para revisar manualmente desde la raíz del repositorio, el siguiente comando ejecuta **solo el auditor de resultados existentes**, sin ejecutar OpenFOAM:

```bash
python3 analysis_tools/audit_pushed_results.py --all
```

- `python3`: ejecuta el script Python de auditoría.
- `--all`: revisa todos los casos controlados presentes, no solamente los cambiados por el último push.
- Salidas: `analysis_results/agent_checks/post_push/report.md` y `report.json` (archivos locales de análisis; los reportes de Actions se entregan como artefactos, no se suben solos al repositorio).

El auditor identifica presencia de perfiles, termopares, series de foamLog, resultados de flujo y energía en `metalTop`, el último tiempo de sonda disponible y discrepancias con el registro. Que aparezca una carpeta no demuestra que el postproceso haya funcionado; que falte un archivo en Git **no demuestra que la corrida no se hizo** en la laptop. La interpretación de residuos, flujos por cara, balances y cambio de fase se conserva como revisión científica posterior.

La verificación estática de definición y cobertura de los `functionObjects` es:

```bash
python3 analysis_tools/audit_postprocessing_config.py --strict
```

Los cuatro perfiles especializados bajo `.github/agents/` son instrucciones para agentes, no procesos de IA autónomos por sí solos. La automatización real es el workflow y los scripts de verificación, que requieren una ejecución exitosa en GitHub Actions. Si falla, no declararlo activo.

**Después del push y su auditoría:** actualizar notas de caso, bitácoras ES/EN, manuales afectados, guía de postprocesamiento, matriz y consolidado histórico cuando corresponda. Nunca inventar datos no subidos.


---

## Anexo operativo — C3D-01 / Plan D (10 de noviembre de 2026)

**Estado y fuente:** [registro completo con SHA y límites](docs/C3D_01_ESTADO_REAL_20261110_ES.md). La prueba local `C3D01_snappy_NTC8Dj` produjo **1,505,847 celdas** y dos fallos de calidad; **no** está aprobada como malla metal–arena ni como simulación de solidificación.

### A. Comprobar STL versionados sin alterarlos (OpenFOAM Foundation 14)

```bash
source /opt/openfoam14/etc/bashrc
cd ~/OpenFOAM/MasterProject/cases_3d/C3D_01_metal_mold
sha256sum constant/geometry/{metal,mold,mold_repaired}.stl
surfaceCheck -checkSelfIntersection constant/geometry/metal.stl
surfaceCheck -checkSelfIntersection constant/geometry/mold_repaired.stl
```

Los **originales y la reparación ya están en GitHub**: no repetir `surfacePointMerge` ni convertir los originales. Si quieres diagnósticos y `problemFaces` sin mezclar archivos, ejecutar desde carpetas separadas, por ejemplo `surfaceCheck_outputs/metal/` o `surfaceCheck_outputs/mold_repair_trial/` con rutas absolutas.

### B. Evaluar la prueba local ya generada sin rehacerla

```bash
source /opt/openfoam14/etc/bashrc
TRIAL="$HOME/OpenFOAM/C3D01_snappy_NTC8Dj"
foamDictionary "$TRIAL/system/snappyHexMeshDict" -entry geometry
foamDictionary "$TRIAL/system/snappyHexMeshDict" -entry castellatedMeshControls/refinementSurfaces
foamDictionary "$TRIAL/system/snappyHexMeshDict" -entry castellatedMeshControls/refinementRegions
grep -Ei 'cells:|face tets|concave cells|Failed|non-orthogonality|skewness' "$TRIAL/log.checkMesh.final"
```

La malla de prueba generada por `snappyHexMeshConfig` tenía `cellZone metal` con 383,788 celdas, pero **no demuestra** volumen correcto, `cellZone mold`, interfaz conjugada ni exclusión de aire exterior. El volumen global reportado, 242.201 cm³, corresponde prácticamente a toda la caja de fondo.

### C. Qué comandos NO usar sin revisión

- `snappyHexMeshConfig -case ...` es **inválido** en la Foundation 14 instalada. Entrar antes al directorio del caso y llamar `snappyHexMeshConfig ...` allí.
- No colocar `set -u` antes del `source /opt/openfoam14/etc/bashrc` (error observado `ZSH_NAME: unbound variable`).
- `surfaceTransformPoints` se utilizó **solo en una prueba aislada**, sobre copias escaladas. **Para el siguiente caso se prefiere STL original en mm y `units [mm];` por geometría del `snappyHexMeshDict`**, sin convertir ni escalar dos veces. Esta variante **ya se ejecutó** en el segundo ensayo `C3D01_castellated_7X7rLt` (sin `snap` ni capas): 1,505,826 celdas, no ortogonalidad máxima 25.2394°, skewness 0.333333, `Face tets OK`, **21,353 celdas cóncavas** y **1 fallo `checkMesh`**. **No es una malla CFD aprobada.** Véase el registro C3D.
- No ejecutar `splitMeshRegions` ni el solver mientras no se validen zonas física metal/arena, interfaz y los 23 face tets / 6,974 concave cells.
- No sobreescribir `constant/polyMesh`, `log.*` ni usar `Allclean` sobre la campaña histórica. Crear carpeta de prueba nueva.

**Git:** El commit `e391f7591` incorporó los STL originales; el reparado y sus logs se incorporaron mediante `06426781f` tras rebase. Los logs completos de la prueba local `snappyHexMesh` no fueron subidos. Las comprobaciones estáticas de GitHub **no ejecutan** OpenFOAM.

### D. Recorte de material mediante subsetMesh (Foundation 14)

**Error real detectado 2026-11-10:** en Foundation 14, `subsetMesh materialVolume -case ...` produce `Wrong number of arguments, expected 0 found 1`. La opción **obligatoria** para seleccionar el conjunto es `-cellSet materialVolume`; `-overwrite` ya es el comportamiento predeterminado y el programa la marca como obsoleta.

```bash
source /opt/openfoam14/etc/bashrc
CASE="$HOME/OpenFOAM/C3D01_materials_H0qgJN"
subsetMesh -case "$CASE" -cellSet materialVolume -noFields > "$CASE/log.subsetMesh" 2>&1
checkMesh -case "$CASE" -allGeometry -allTopology -writeSets > "$CASE/log.checkMesh" 2>&1 || true
grep -Ei 'cells:|Number of regions:|non-orthogonality|skewness|face tets|concave cells|Failed|Mesh OK' "$CASE/log.checkMesh"
```

Este recorte **solo es diagnóstico**, no garantiza interfaz CHT ni malla aprobada.

## E. Historial ejecutado de comandos C3D-01 (10-11-2026)

Esta sección complementa **todos los comandos históricos de casos B/C** (partes 1–28) con el trabajo 3D de metal y arena. Cada estado distingue **EJECUTADO** de **PROPUESTO**. La fuente de cantidades es la salida de terminal del investigador, registrada en [bitácora C3D-01](docs/C3D_01_ESTADO_REAL_20261110_ES.md). **Los logs y mallas de las carpetas de prueba siguen en laptop, no en GitHub.**

| Utilidad | Uso que hemos realizado | Estado y precaución |
|---|---|---|
| `source /opt/openfoam14/etc/bashrc` | Cargar OpenFOAM Foundation 14 antes de ejecutar utilidades | **EJECUTADO**; si usas `set -u`, cargar OpenFOAM antes |
| `surfaceCheck`, `surfacePointMerge`, `surfaceInertia` | Comprobar/cerrar molde y medir volúmenes STL | **EJECUTADO**; conservar CAD original inalterado |
| `foamDictionary` | Leer `geometry`, `refinementSurfaces`, `refinementRegions`, `insidePoints`, `snapControls`; ajustar `snap` y `addLayers` de la copia | **EJECUTADO** |
| `blockMesh` | Malla de fondo 2 mm nominal | **EJECUTADO** en ensayo local |
| `snappyHexMesh` | Primera malla con snap; segunda castellated con `units [mm];`, `snap false` | **EJECUTADO**; ninguna fue aceptada |
| `checkMesh` | Calidad general; `-writeSurfaces -surfaceFormat vtk -writeSets` para exportar defectos; `-region` por malla | **EJECUTADO** |
| `topoSet` | `boxToCell` para AABB, `surfaceToCell` para interiores STL, `zoneToCell` para zone metal, `cellToCell` para combinar materiales | **EJECUTADO** |
| `subsetMesh -cellSet materialVolume -noFields` | Recorte diagnóstico de metal+molde | **EJECUTADO**; la forma posicional `subsetMesh materialVolume` **NO funciona** en Foundation 14 |
| `splitMeshRegions -disconnected -noFields` | Separación topológica del caso recortado | **EJECUTADO**; devuelve `No interfaces to add` |
| `splitMeshRegions -cellZones 'metal'` | Inspeccionar caras compartidas de zona metal en la malla original conectada | **PROPUESTO, aún NO ejecutado** |

### Comandos de consulta y exportación que sí utilizamos

```bash
source /opt/openfoam14/etc/bashrc
TRIAL="$HOME/OpenFOAM/C3D01_snappy_NTC8Dj"
DICT="$TRIAL/system/snappyHexMeshDict"
foamDictionary "$DICT" -entry geometry
foamDictionary "$DICT" -entry castellatedMeshControls/refinementSurfaces
foamDictionary "$DICT" -entry castellatedMeshControls/refinementRegions
foamDictionary "$DICT" -entry castellatedMeshControls/insidePoints
foamDictionary "$DICT" -entry snapControls
# La calidad de esta prueba ya fue exportada y guardada localmente:
# checkMesh -case "$TRIAL" -allGeometry -allTopology -writeSurfaces -surfaceFormat vtk -writeSets
find "$TRIAL/postProcessing/checkMesh" -name '*.vtk' -print
```

### Consultar el recorte **ya realizado** (sin repetir operaciones destructivas)

```bash
source /opt/openfoam14/etc/bashrc
CASE="$HOME/OpenFOAM/C3D01_materials_H0qgJN"
grep -Ei 'cells:|Number of regions:|Total volume|face tets|small determinant|concave cells|Failed' "$CASE/log.checkMesh"
cat "$CASE/constant/polyMesh/boundary"
```

El recorte terminó con **1,209,777 celdas, 151.230 cm³, 15 celdas cóncavas, 8 caras con face-tets deficientes, 17 determinantes pequeños y 3 fallos de calidad**. El parche `oldInternalFaces` (8,384 caras) **no es interfaz térmica emparejada**. El `outerBox` quedó con 0 caras. **No repetir `subsetMesh` sobre el caso recortado**: crear una copia nueva si se desea otra variante.

### Consultar las dos regiones **ya creadas**

```bash
source /opt/openfoam14/etc/bashrc
CASE="$HOME/OpenFOAM/C3D01_regions_Xd1POM"
# splitMeshRegions -case "$CASE" -disconnected -noFields  # YA EJECUTADO; NO REEJECUTAR
for REGION in region1 region2; do
    grep -Ei 'cells:|Total volume|face tets|small determinant|concave cells|Failed' "$CASE/log.checkMesh.$REGION"
    cat "$CASE/constant/$REGION/polyMesh/boundary"
done
grep -Ei 'No interfaces to add|Region|nCells' "$CASE/log.splitMeshRegions"
```

**Resultados:** `region1` = probable arena, **825,994 celdas**, 103.256 cm³, 6 face-tets malos, 14 determinantes pequeños, 15 cóncavas, **3 comprobaciones fallidas**; `region2` = probable metal, **383,783 celdas**, 47.9735 cm³, 2 face-tets malos, 3 determinantes pequeños, **2 comprobaciones fallidas**. El programa comunicó **`No interfaces to add`**; no existe todavía interfaz CHT verificada. La futura alternativa de `-cellZones 'metal'` es una **hipótesis experimental**, no un logro.

**Estado científico al cierre de este día:** no hay malla aceptada, no se ha ejecutado solver 3D, C14 sigue baseline 2D, J0/G1 abiertas. Los informes estáticos GitHub no prueban ejecución en Ubuntu.
