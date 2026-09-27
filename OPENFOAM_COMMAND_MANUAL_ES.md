# Manual práctico de comandos OpenFOAM — QuickCup Solidification

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

---

## 1. Ir a la carpeta principal del proyecto

### Para qué sirve
`cd` significa **change directory**. Este comando te lleva directamente a la carpeta raíz del proyecto, sin importar dónde estés en la terminal.

### Comando

```bash
cd ~/OpenFOAM/QuickCup_Solidification
```

### Ir directamente a los casos controlados de buoyancy

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
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
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
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
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
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
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/B6_adaptiveDt
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
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/B6_adaptiveDt
./Allclean && ./Allrun
```

### Correr solo C6

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/C6_adaptiveDt
./Allclean && ./Allrun
```

### Correr solo B7

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/B7_outer4
./Allclean && ./Allrun
```

### Correr solo C7

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/C7_outer4
./Allclean && ./Allrun
```

### Correr C6, B7 y C7 después de que B6 ya terminó

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
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
cd ~/OpenFOAM/QuickCup_Solidification
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
cd ~/OpenFOAM/QuickCup_Solidification
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
cd ~/OpenFOAM/QuickCup_Solidification/cases_buoyancy/C2_test
./Allclean
./Allrun
paraFoam -builtin &
```

### Ejemplo B2

```bash
cd ~/OpenFOAM/QuickCup_Solidification/cases_buoyancy/B2_test
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
cd ~/OpenFOAM/QuickCup_Solidification
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
cd ~/OpenFOAM/QuickCup_Solidification
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
