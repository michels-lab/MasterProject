# OpenFOAM Practical Command Manual — QuickCup Solidification

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
