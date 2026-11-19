# FS-C04 — Piloto 3D, región `fluid` hierro+aire y región sólida `mold` (solo mallado)

**Estado:** entrada de `blockMesh`, auditoría estática y ejecutor de mallado Foundation14 implementados en rama `research/fs-c02-metal-air-vof-20261117`. **La malla FS-C04 NO se ha ejecutado todavía en OpenFOAM nativo**, y ningún CFD/VOF/CHT se ha arrancado. El FS-C03 de tres regiones **sí pasó su ejecución nativa** el 18-11-2026, pero es un piloto independiente e intacto.

## Por qué se requiere esta partición

La malla FS-C03 validó la topología de tres materiales separados: `metal`, `mold`, `air`. Para transportar una superficie libre por VOF con `alpha.metal`, el hierro líquido y el gas deben ocupar **un único dominio fluido**; por el contrario, la arena debe permanecer como **región sólida distinta**, con acoplamiento de calor conjugado en la interfaz.

En FS-C04 mantenemos **los 84 vértices, 53 bloques, geometría y subdivisiones idénticas a FS-C03**, pero relabelamos exclusivamente los 3 bloques inicialmente metálicos y los 29 de aire como `fluid`. Los 21 bloques `mold` permanecen iguales. Se preservan los parches abiertos `atmosphereTop`, `atmosphereSides`, `atmosphereLowerSides` sobre el **aire lejano**, y la región fluida cubre tanto el metal superior como la arena superior y sus cuatro costados. Las superficies exteriores físicas de arena seguirán siendo interfaces sólido–fluido, no paredes atmosféricas ficticias.

| Zona de mallado (no fracción de fase) | Celdas previstas | Bloques |
| --- | ---: | ---: |
| `fluid` (metal inicial + aire) | **34,368** (=2368+32000) | **32** (=3+29) |
| `mold` (arena) | **7,680** | **21** |
| **Total** | **42,048** | **53** |

**Nota:** para la simulación futura, `fluid` no significa que todas sus celdas sean metal: habrá que inicializar `alpha.metal=1` en la parte metálica y `alpha.metal=0` en el aire, conservando un único campo T fluido donde corresponda. **Ese campo `alpha.metal` no existe todavía**; los números anteriores son solamente una partición geométrica de OpenFOAM, no volúmenes de fase comprobados ni un resultado térmico.

## Comprobaciones implementadas

`analysis_tools/audit_fs_c04_fluid_mold.py` compara cada vértice, hexaedro, tamaño de bloque, zona y cara exterior con la referencia inmutable FS-C03. **No permite ningún cambio geométrico**: las únicas diferencias son las etiquetas `metal/air → fluid`. Acepta los 32 bloques fluidos y 21 bloques sólidos solo si ambos grupos están conectados por caras. El frente inicial metal–aire deja de ser un `wall` o `mappedWall` geométrico y pasa a ser una **cara interna entre celdas fluidas** (la posición real del frente requerirá el campo `alpha.metal`).

Se esperan **37 caras topológicas fluido–arena**, equivalentes a `13 metal–arena + 24 aire–arena`, y **3,136 caras discretizadas** a cada lado de `mappedWall` `fluid_to_mold` ↔ `mold_to_fluid` después de `splitMeshRegions`. Las caras fluidas externas deben conservar `atmosphereTop` (448), `atmosphereSides` (3,040) y `atmosphereLowerSides` (256) como tipo `patch`. Todos estos conteos **son expectativas de auditoría para FS-C04**, no valores ya medidos por ejecución nativa.

`analysis_tools/run_fs_c04_mesh.py` por defecto solo copia los archivos a una carpeta nueva sin sobrescribir nada. Con `--native`, bajo OpenFOAM Foundation 14, ejecuta en esa copia `blockMesh`, `checkMesh` del padre, `splitMeshRegions -cellZones 'fluid mold' -noFields`, `checkMesh` por zona y una verificación recíproca `mappedWall`/celdas/atmósfera. Si algo falla, deja los logs y el estado `REJECTED_NATIVE_MESH`, **sin arrancar ningún solver**.

### Comprobación estática (sin OpenFOAM)

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/audit_fs_c04_fluid_mold.py
python3 -m unittest discover -s analysis_tools -p 'test_*fs_c04*.py' -v
```

### Mallado nativo seguro, sin CFD

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/run_fs_c04_mesh.py --native
```

Requiere OpenFOAM Foundation 14 activo; crea un directorio **nuevo** bajo `~/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_<UTC>_<id>`. El éxito esperado sería `NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD`. Hasta que aparezca ese resultado, **no declarar aprobado el mallado FS-C04**.

## Condiciones pendientes para CFD real y tesis

1. **Fidelidad CAD:** el piloto hereda la aproximación por bloques de C3D-03, no sigue exactamente las superficies CAD STL v2. Las áreas y volúmenes del hierro y arena deben compararse con CAD antes de usarlos para la interpretación térmica.
2. **Identificar celdas metálicas iniciales:** construir un mapa de celdas fluido con `alpha.metal=1` en metal y `0` en gas sin confundir zonas con fases. Verificar volumen metálico inicial contra CAD y contra una malla de referencia.
3. **Transferencia térmica:** definir materiales y BC compatibles con CHT fluid–mold, no solo tener parches `mappedWall` de mallado. Verificar conservación de flujo de calor en ambos lados.
4. **Base del molde:** resolver contacto con soporte y exposición real del hueco inferior. La arena exterior lateral y superior sí está expuesta, la base queda pendiente.
5. **Física de la superficie libre:** incorporar VOF y comprobar advección de `alpha.metal`, movimiento de interfaz, aire abierto, conservación de volumen/masa, propiedades, turbulencia y energía **antes** de introducir solidificación, calor latente, grafitización y contracción.

**Archivos originales protegidos:** las corridas FS-C02, el FS-C03 nativo `FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90`, B14, FS-C01 y C3D-02 no se cambian ni se sobrescriben. El PR #51 sigue en modo draft hasta validar física y malla CAD.

## 18-11-2026 — Gate nativo real aprobado en OpenFOAM Foundation 14

**Confirmación reportada por el investigador desde Ubuntu (commit `8b4adaf19`):** `python3 analysis_tools/audit_fs_c04_fluid_mold.py` produjo `STATIC_2_ZONE_TOPOLOGY_CONSISTENT_NOT_NATIVE_CHECKMESH`; después `python3 -m unittest discover -s analysis_tools -p 'test_*fs_c04*.py' -v` reportó **11 pruebas correctas**, incluida una prueba negativa esperada por versión errónea de OpenFOAM (no es un fallo del caso). Finalmente, `python3 analysis_tools/run_fs_c04_mesh.py --native` produjo:

```text
OpenFOAM: 14
FS-C04 2-zone mesh-only pilot staged: /home/michel/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_20261118T204433Z_7fa8dc47
FS-C04 status: NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD
NO CFD. Alpha metal initial field, real CAD fit and mold support unresolved.
```

El ejecutor solo imprime `NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD` después de ejecutar `blockMesh`, `checkMesh` en el caso completo y en las dos regiones, `splitMeshRegions`, comprobar `mappedWall` recíprocos y las fronteras atmosféricas abiertas. **El gate nativo de malla FS-C04 está aprobado.** La evidencia no incluye aquí los logs completos ni valores detallados de skewness/nonorthogonality; no inventarlos.

**Alcance no demostrado:** no existe todavía campo `alpha.metal` inicial, validación de volúmenes/áreas del CAD original, tratamiento del apoyo inferior, acoplamiento CHT ni corrida VOF/solidificación; no confundir éxito de geometría con validación física. El caso FS-C04 validado se conserva inmutable. La siguiente etapa debe preparar en una NUEVA carpeta una asignación reproducible de las 2368 celdas inicialmente metálicas dentro de la región fluida (`34,368` celdas), con auditoría de integridad y volumen antes de resolver CFD.

## 18-11-2026 — Auditoría de preparación de `alpha.metal`: tres bloques metálicos, todavía SIN campo

Se añadió `analysis_tools/audit_fs_c04_metal_seed.py` (solo lectura) y seis pruebas asociadas. El script extrae los **tres bloques originales metal** `[9, 14, 19]` de la fuente FS-C03 y confirma que su geometría y subdivisiones no cambiaron al convertirse en celdas de la zona `fluid` de FS-C04. Se deriva analíticamente su volumen como suma de secciones cuadrangulares con interpolación lineal de vértices e integración de Simpson exacta para sección cuadrática.

| Metal original | Altura vertical en el piloto (mm) | Celdas previstas | Volumen analítico (mm³) |
| --- | --- | ---: | ---: |
| Bloque 9 | -40 a -38 | 128 | 1888.632224 |
| Bloque 14 | -38 a -20 | 960 | 20732.540616 |
| Bloque 19 | -20 a 0 | 1280 | 25390.743440 |
| **Total** | **-40 a 0** | **2368** | **48011.916280** |

El volumen de metal CAD v2 documentado es **47 987.697 mm³**, diferencia del piloto `+24.21928 mm³` o **+0.05047 % en volumen**. Ese ajuste volumétrico cercano NO valida superficie, redondeos, conicidad, volumen de arena ni intercambio térmico. En la futura región fluida única habría **2368 celdas con `alpha.metal=1`** y **32000 de aire con `alpha.metal=0`** si el mapeo de celdas de `blockMesh` coincide exactamente. Son objetivos **geométricos**, no resultados experimentales ni campos resueltos.

**ADVERTENCIA:** los índices `[9,14,19]` son números de *bloque hexaédrico*, NO índices de celda en el `polyMesh` ni la malla dividida; **no** escribir `alpha.metal` por suposición de orden. El script no modifica la carpeta nativa FS-C04 que el investigador ya comprobó, no crea campos ni ejecuta solver. Antes de escribir `0/fluid/alpha.metal`, verificar correspondencia entre celdas nativas del FS-C03 con zona metal y la malla FS-C04, respetar `splitMeshRegions`, demostrar el volumen del campo y que las celdas del sólido tengan 0 volumen de fase metálica. No llamar a `alpha.metal` *fracción sólida*.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/audit_fs_c04_metal_seed.py
python3 -m unittest discover -s analysis_tools -p test_audit_fs_c04_metal_seed.py -v
```

Este análisis **no necesita correr `blockMesh` de nuevo**. El resultado esperado es `ANALYTIC_METAL_SEED_IDENTIFIED_NO_FIELD_WRITTEN`, no `alpha` inicializado.

## Siguiente gate implementado — identidad de las celdas nativas, sin crear campos

Se añadió `analysis_tools/audit_fs_c04_native_metal_mapping.py` (SOLO LECTURA) para comparar las **dos corridas nativas ya terminadas** del mismo día:

- FS-C03 de tres `cellZones`: `~/OpenFOAM/FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90`
- FS-C04 de dos `cellZones`: `~/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_20261118T204433Z_7fa8dc47`

El nuevo auditor **NO ejecuta ninguna utilidad de OpenFOAM**. Valida estado nativo exitoso, manifiestos de los 53 bloques idénticos, hashes exactos de los cuatro archivos `constant/polyMesh/{points,faces,owner,neighbour}` en los padres originales, y partición de los 42,048 índices de celda dentro de `constant/polyMesh/cellZones` ASCII. Compara el conjunto de 2,368 índices `metal` del FS-C03 con el `fluid` del FS-C04 y exige `metal ∪ air = fluid` y que las celdas `mold` sean exactamente las mismas. Cualquier discrepancia bloquea el análisis, sin modificar las mallas, según principio fail-closed. Los archivos `cellZones` binarios no se aceptan automáticamente sin un exportador comprobado.

**Esta auditoría prueba solo la identidad de índices de celdas en la malla PADRE**, no el direccionamiento después de `splitMeshRegions` dentro de `constant/fluid/polyMesh`. **Sigue prohibido inicializar `0/fluid/alpha.metal` a partir de índices de bloque o índices de la malla padre sin verificar el mapeo del `fluid` dividido.** No se ha escrito ninguna fracción de fase ni arrancado CFD.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/audit_fs_c04_native_metal_mapping.py \
  --fs-c03 ~/OpenFOAM/FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90 \
  --fs-c04 ~/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_20261118T204433Z_7fa8dc47
```

Éxito esperado, pendiente de ejecución local: `PARENT_MESH_METAL_CELL_LABELS_MATCH_NO_FIELD_WRITTEN`. Si aparece `BLOCKED`, conservar la carpeta original y revisar el error: **no saltarse el gate ni generar un campo `alpha` sintético**.

## 18-11-2026 — Éxito REAL de identidad de celdas en la malla PADRE

El investigador ejecutó `audit_fs_c04_native_metal_mapping.py` (no ejecutó OpenFOAM ni modificó archivos) sobre las carpetas nativas FS-C03 `20261118T202905Z_6ef0cd90` y FS-C04 `20261118T204433Z_7fa8dc47`. Resultado real:

```text
status: PARENT_MESH_METAL_CELL_LABELS_MATCH_NO_FIELD_WRITTEN
points:   91ed714789ca3b4efe216d9361e75daf6288494a182cd1786fa5fa3d2b31da01
faces:    66714d76a1cc1f2949dbfd74d600c1c3a62aa73ce01dad431a7742fa7a446ad4
owner:    22c9b04b1f5901a215ef503f15ed42d92e9a6216e7819806f973fe3a468dcc81
neighbour:873757fa25c064582e1e6e2c5c7ae946302191b6a54c1b4ac9ed3066c0cd8d1a
metal: 2368 parent cells
air:   32000 parent cells
mold:  7680 parent cells
metal + air == fluid: TRUE
mold cell identity: TRUE
parent metal label span: 2944 .. 7487 (NOT a contiguous cell range!)
analytic metal volume: 48011.91627999999 mm3
split-fluid cell mapping: NOT YET VERIFIED
native metal cell volumes: NOT YET INTEGRATED
alpha.metal field written: FALSE
CFD/CHT executed: FALSE
```

Las mallas PADRE FS-C03 y FS-C04 son **byte por byte idénticas** en puntos, caras y direccionamiento `owner/neighbour`; sólo se relabelan los grupos metal y aire como `fluid`. El conjunto metálico real comprende 2368 índices no necesariamente contiguos en el intervalo 2944–7487. **NO utilizar ese intervalo como `alpha.metal=1`.** Antes de inicializar un campo fluido hay que comparar por geometría la malla de la región `constant/fluid/polyMesh` resultante de `splitMeshRegions`, que puede numerar las celdas de otra manera, y verificar el volumen `sum(alpha*V)` con volúmenes geométricos de las celdas. Mantener ambas carpetas históricas estrictamente de solo lectura.

## Nuevo gate — mapa geométrico de celdas de la región `fluid` separada (PENDIENTE DE EJECUCIÓN REAL)

Se añadió el auditor **`analysis_tools/audit_fs_c04_split_cells.py`**. Parte de la identidad padre FS-C03/FS-C04 ya comprobada y lee los `polyMesh` de **tres mallas**: padre FS-C04, `constant/fluid/polyMesh` y `constant/mold/polyMesh` divididas. NO depende de que `splitMeshRegions` mantenga el orden de las celdas: reconstruye cada celda hexaédrica mediante sus **ocho coordenadas vértice únicas**, exige una biyección exacta sin duplicación hacia la zona padre correspondiente y verifica que ningún hexaedro de arena se clasifique como gas/hierro.

Las coordenadas ASCII se comparan a precisión de 1 nm (los elementos previstos son de orden milimétrico). Rechaza archivos binarios no soportados, campos incompletos, degeneraciones, colisiones geométricas y cambios de topología o direccionamiento. La verificación tiene tests sintéticos que fuerzan renumeración de puntos y de celdas, incluidas condiciones corruptas. No escribe sobre ninguna carpeta nativa.

Con el mapeo validado, se sumará el volumen geométrico de los **2,368 hexaedros metálicos** del `polyMesh` fluido, triangulando sus caras y comparándolo con los **48,011.91628 mm³** analíticos del piloto. Esto es una reconstrucción geométrica independiente, **no el volumen de salida de `volFieldValue` OpenFOAM**. El criterio de discrepancia relativa de malla a geometría es 0.2 %, sin relajar automáticamente si no se cumple.

Ejecutar desde el worktree FS-C02 actualizado:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/audit_fs_c04_split_cells.py \
  --fs-c03 ~/OpenFOAM/FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90 \
  --fs-c04 ~/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_20261118T204433Z_7fa8dc47
```

**Estado esperado (AÚN NO DEMOSTRADO):** `SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN`. Aun con el gate aprobado, crear `alpha.metal` solo **sobre una COPIA NUEVA, nunca sobre las corridas ya aprobadas**, con una auditoría posterior de `alpha` e integral geométrica por celda antes de aceptar un nuevo caso VOF. El campo no existe actualmente, no se ejecutó CFD.

## 18-11-2026 — SPLIT FLUID MAPPING APROBADO, campo `alpha.metal` ahora preparado en herramienta (aún SIN EJECUTAR)

**Salida real aportada por investigador:** `audit_fs_c04_split_cells.py` mostró `SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN`; nueve pruebas sintéticas aprobaron. La biyección exacta por ocho vértices entre malla madre y dos mallas divididas abarca **42,048** celdas sin pérdidas. Dentro de `constant/fluid/polyMesh` se identifican **2368** celdas de metal (IDs mínimo 0, máximo 2367, por mapeo demostrable y no por suposición), **32000** aire, y las **7680** de arena permanecen en región `mold`. El volumen geométrico sumado de las celdas metálicas divididas es **4.801191628e-05 m³** (`48011.91628 mm³`), prácticamente idéntico al valor geométrico analítico del piloto; ambos difieren del CAD nominal `47987.697 mm³` en ~**0.0505%**. Es validación de geometría y numeración, **no validación física ni CFD**.

Hashes comprobados en ejecución: las cuatro piezas de malla padre (`points`, `faces`, `owner`, `neighbour`) de FS-C03/FS-C04 coinciden, y las mallas separadas también se auditaron con sus propios SHA-256. No escribir nunca en las carpetas originales.

### Nuevo paso: copiar FS-C04 y generar SOLAMENTE `0/fluid/alpha.metal`

Se creó `analysis_tools/stage_fs_c04_initial_alpha.py` (pendiente de ejecución local) que:
- **Vuelve a correr todos los gates de asignación de metal**, incluida comparación de celdas por geometría y SHA-256, sin confiar en la salida del chat.
- Rechaza copias antiguas con `polyMesh` modificado, cualquier symlink/archivo no fiable, salidas preexistentes y parches atmósfera/térmico incompatibles.
- Copia el directorio nativo aprobado FS-C04 en una carpeta NUEVA e independiente bajo `~/OpenFOAM/FS_C04_ALPHA_RUNS/FS_C04_ALPHA_STAGE_<UTC>_<id>/`; preserva intocadas todas las corridas FS-C03/FS-C04/FS-C02, B14, C3D-02.
- Escribe **solamente un campo de fases inicial** `0/fluid/alpha.metal`, 34,368 valores explícitos: metal `1` en las 2368 celdas mapeadas, gas `0` en las otras 32000. No se crea `alpha` en arena sólida. La interfaz metal–aire es interna al fluido; no se agrega pared ficticia.
- Declara `alpha.metal` adimensional (`[0 0 0 0 0 0 0]`); `fluid_to_mold` con `zeroGradient`; en `atmosphereTop`, `atmosphereSides` y `atmosphereLowerSides`, `inletOutlet` con reentrada `alpha.metal=0` (aire), permitiendo salida metal/gas según evolución posterior. El tratamiento final de BC/flux debe verificarse al integrar el solver.
- Lee otra vez el campo escrito, exige EXACTAMENTE las mismas 2368 celdas metal y verifica `sum(alpha*V)` mediante geometría de celdas, con SHA-256 y manifiesto `FS_C04_ALPHA_INITIALIZATION.json`.
- **No ejecuta CFD, no resuelve CHT, no demuestra lectura nativa del campo por OpenFOAM ni ejecuta `volFieldValue`**. Son gates futuros y no se deben presentar como realizados.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_stage_fs_c04_initial_alpha.py -v && \
python3 analysis_tools/stage_fs_c04_initial_alpha.py \
  --fs-c03 ~/OpenFOAM/FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90 \
  --fs-c04 ~/OpenFOAM/FS_C04_FLUID_MOLD_TOPOLOGY_20261118T204433Z_7fa8dc47
```

**Estado esperado, NO SE HA EJECUTADO:** `INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD`. Si el script falla, conservar evidencia y revisar; no correr `foamRun` ni ignorar errores de lectura de malla. El molde real y su apoyo, propiedades térmicas dependientes de T, balance energético metal–aire–arena, turbulencia y tratamiento térmico de interfaz siguen pendientes.

## 2026-11-18 — Resultado local real: campo `alpha.metal` aislado creado y auditado

El investigador ejecutó `test_stage_fs_c04_initial_alpha.py` desde commit `4e0696e5c`: **`Ran 10 tests in 0.105s / OK`**. Después ejecutó `stage_fs_c04_initial_alpha.py` sobre las dos mallas nativas aprobadas. Salida:

```text
FS-C04 ALPHA: INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD
New isolated copy: /home/michel/OpenFOAM/FS_C04_ALPHA_RUNS/FS_C04_ALPHA_STAGE_20261118T214929Z_8d780c53
metal cells: 2368 air: 32000
geometric sum(alpha*V) m3: 4.801191628e-05
alpha field SHA256: f37f6668510b471bbf123567514664cd47aeba5fa19502da87133b6a3389079d
NO CFD. Native field/volume acceptance not yet tested.
```

**Hecho demostrado:** hay una copia nueva con `0/fluid/alpha.metal` adimensional y 34,368 valores exactos; ninguna celda del molde recibió fracción VOF, todos los límites atmosféricos admiten reentrada de aire `alpha.metal=0`, y se verificó geométricamente la integral `sum(alpha V)` de las celdas líquidas. La carpeta original FS-C04 y FS-C03 queda intacta. **No afirmar que OpenFOAM cargó nativamente el volScalarField ni integró el volumen hasta completar la etapa siguiente.**

### Nuevo control preparado: `foamPostProcess` nativo (SIN CFD)

Se implementó `analysis_tools/verify_fs_c04_native_alpha.py`. Emplea la plantilla oficial de OpenFOAM Foundation 14 `volIntegrate(alpha.metal)` para ejecutar `foamPostProcess -region fluid -time 0` sobre **OTRA COPIA NUEVA** del caso alpha, nunca en las fuentes originales. Antes de ejecutar recalcula las pruebas de identidad de malla padre y región fluida, los hashes SHA-256, asignación exacta 2368 metal/32000 aire, BC de atmósfera, ausencia de `alpha` en arena, integridad del manifold de malla y volumen geométrico. Después exige un resultado real de `postProcessing/**/volFieldValue.dat` de `t=0` para la función `volIntegrate(alpha.metal)`, compara con **4.801191628e-05 m³** con umbral máximo de **0.2 %**, y registra el resultado y los hashes en `FS_C04_NATIVE_ALPHA_ACCEPTANCE.json`. Sin archivo/función/hora válidos, se marca `NATIVE_ALPHA_INTEGRAL_REJECTED_NO_CFD`, sin declarar éxito ficticio.

**Comando de prueba, después de actualizar FS_C02_WORKTREE:**

```bash
python3 -m unittest discover -s analysis_tools -p test_verify_fs_c04_native_alpha.py -v && \
python3 analysis_tools/verify_fs_c04_native_alpha.py \
  --stage ~/OpenFOAM/FS_C04_ALPHA_RUNS/FS_C04_ALPHA_STAGE_20261118T214929Z_8d780c53
```

**Resultado esperado — AÚN NO CONFIRMADO POR UBUNTU:** `NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD`, junto con volumen medido. La ejecución no usa `foamRun`, no arranca térmica/CHT, ni cambia la carpeta ya aprobada. Si Foundation 14 requiere alguna adaptación de formato de salida o configuración de `foamPostProcess`, atender el error y los logs, sin saltarse el gate ni tolerar valores falsos. El archivo escrito **aún no acredita** una simulación física válida: faltan las propiedades térmicas, `U/p/T`, solución de la convección, contacto real molde–metal, CHT, solidificación, grafitización y contracción.

## 18 de noviembre de 2026 (hora local); resultado nativo exitoso, `alpha.metal` plenamente leído e integrado

**Ejecución REAL confirmada por el investigador en Ubuntu, OpenFOAM Foundation 14 (commit `7ce79841d`):** `python3 -m unittest discover -s analysis_tools -p test_verify_fs_c04_native_alpha.py -v` finalizó con **14/14 pruebas correctas**. A continuación, `verify_fs_c04_native_alpha.py` verificó una **tercera copia aislada** de FS-C04 mediante `foamPostProcess -region fluid -time 0 -func 'volIntegrate(alpha.metal)'`.

```text
FS-C04: NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD
New verified-copy path: /home/michel/OpenFOAM/FS_C04_ALPHA_NATIVE_CHECKS/FS_C04_ALPHA_NATIVE_CHECK_20261119T045227Z_50756897
OpenFOAM native volume m3: 4.801191628e-05
NO CFD / no CHT / no solidification / no shrinkage.
```

Por lo tanto, **`0/fluid/alpha.metal` está comprobado con lector y postprocesamiento nativos**: 2368 celdas inicialmente metálicas, 32000 de gas, 7680 de arena en otra región, y **`∫alpha.metal dV=4.801191628×10⁻⁵ m³=48.01191628 cm³`**. La coincidencia con la integral geométrica es exacta a la precisión presentada; la diferencia con el volumen CAD declarado de 47.987697 cm³ es ~0.0505 %, pero la coincidencia de volúmenes no demuestra fidelidad de superficies STL.

**Estado actualizado:** la etapa de *malla topológica + mapeo de fase + volumen nativo inicial* está APROBADA. Todavía NO existe un solver VOF+CHT acoplado, ni una física de gas exterior validada, ni modelos de solidificación/contracción. No confundir `alpha.metal` (VOF metal–aire) con fracción sólida.

**Siguiente control térmico de interfaz:** auditar en forma **read-only** las 3136 caras `fluid_to_mold` / `mold_to_fluid`, incluyendo concordancia de áreas y normales recíprocas, separación por `alpha.metal` de las superficies inicialmente metal–arena (1248 caras) y aire–arena (1888), y la clasificación de las caras superiores/laterales de la arena. No aplicar de momento valores heredados de `h=10`, `T=300` sobre arena–aire como BC impuesta de la frontera: en la futura formulación conjugada, el **aire circundante se debe resolver explícitamente**, y esas paredes son interfaces sólido–fluido, no parches externos. La base y el hueco inferior necesitan condiciones fieles al montaje. Materiales de C14/C3D-02 son *candidatos de procedencia*, no propiedades de la mezcla gas/metal validadas.

## Nuevo control de contacto térmico — área y normal de interfaz fluido–arena (todavía SIN EJECUTAR localmente)

Se implementó `analysis_tools/audit_fs_c04_thermal_interfaces.py`, auditor **read-only**, para verificar que la futura transferencia de calor conjugada tiene superficies geométricas reales y recíprocas. Toma exclusivamente la copia cuya lectura e integral de `alpha.metal` fueron aprobadas con Foundation 14:

```text
/home/michel/OpenFOAM/FS_C04_ALPHA_NATIVE_CHECKS/FS_C04_ALPHA_NATIVE_CHECK_20261119T045227Z_50756897
```

Antes de analizarla, vuelve a comprobar el manifiesto de aceptación `NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD`, el resultado nativo de `volIntegrate(alpha.metal)`, los SHA de la malla, el campo `alpha` y los originales FS-C03/FS-C04, sin ejecutar ninguna utilidad de OpenFOAM ni modificar ningún caso. Luego reconstruye las caras nativas desde `polyMesh/points,faces,owner` y verifica:

- `fluid_to_mold` y `mold_to_fluid` `mappedWall` recíprocos, con **3,136 caras** cada uno.
- Para cada cara fluido–arena: mismos cuatro vértices geométricos en ambas regiones, área igual con tolerancia de `1e-12 m²`, normales salientes opuestas, sin duplicados ni caras huérfanas.
- Clasificación inicial por `alpha.metal` **de la celda fluida propietaria**: **1,248 caras** metal–arena y **1,888 caras** aire–arena; estas últimas deben incluir **128 caras superiores** del molde (en y=0) y **1,760 laterales**.
- Integración geométrica de las áreas reales de las caras, reportadas en m²/cm²: área metal–arena, aire–arena superior, aire–arena lateral y total. **No inventar áreas hasta leer la malla nativa y comprobarlas**.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_audit_fs_c04_thermal_interfaces.py -v &&
python3 analysis_tools/audit_fs_c04_thermal_interfaces.py \
  --accepted ~/OpenFOAM/FS_C04_ALPHA_NATIVE_CHECKS/FS_C04_ALPHA_NATIVE_CHECK_20261119T045227Z_50756897
```

El estado esperado es `RECIPROCAL_THERMAL_CONTACT_GEOMETRY_VERIFIED_NO_CHT`; **aún no está confirmado en la laptop**. Si no coincide alguna cara, área o normal, la herramienta debe rechazar el análisis sin reemplazar `mappedWall` ni ajustar arbitrariamente la tolerancia.

Esto **NO** es una condición de frontera térmica funcional ni transferencia de calor resuelta. Las paredes físicas arena–aire están destinadas a intercambio conjugado con el aire **modelado explícitamente**; no imponer sobre ellas `fixedValue T=300 K` ni un coeficiente externo heredado `h=10 W/(m²K)` como sustituto de esa convección. Las fuentes `C14` y `C3D-02` tienen modelos/materiales metal–arena con parámetros provisionales; **no deben copiarse de manera directa a una región VOF conjunta hierro+aire**, cuyos modelos termofísicos, ecuaciones y solvers compatibles con Foundation14 requieren una validación independiente. La base/hueco inferior del molde sigue sin resolver.

## Resultado real, 18 de noviembre de 2026 (hora de Monterrey): superficies conjugadas verificadas

El investigador ejecutó la auditoría `audit_fs_c04_thermal_interfaces.py` en Ubuntu con la copia nativa de `alpha.metal` ya aprobada desde commit `daf0b8eaa`. Resultado **real**: `Ran 11 tests in 0.008s / OK` y estado `RECIPROCAL_THERMAL_CONTACT_GEOMETRY_VERIFIED_NO_CHT`. Datos **medidos geométricamente en la malla**, no supuestos de transferencia térmica:

| Contacto inicial | Caras nativas por cada lado | Área m² | Área cm² |
|---|---:|---:|---:|
| Hierro líquido–arena | 1248 | 0.0064837952138918934 | 64.83795213891894 |
| Aire–arena superior | 128 | 0.001350989999999999 | 13.50989999999999 |
| Aire–arena lateral | 1760 | 0.012834497383364844 | 128.34497383364842 |
| **Total fluid–mold** | **3136** | **0.020669282597256734** | **206.69282597256733** |

El error máximo de área en la misma cara del lado fluido y sólido fue `2.879912020664621e-20 m²`; error máximo de oposición de normales unitarias `2.220446049250313e-16`; **3136 de 3136 caras emparejadas**. El aire está realmente conectado sobre la arena y a sus cuatro lados; las condiciones atmosféricas abiertas permanecen **en el exterior** del dominio, no en la pared real arena–aire.

**Significado:** la partición geométrica `fluid/mold`, los volúmenes iniciales y las superficies de contacto están validados para esta **malla piloto aproximada**, sin afirmar transferencia de calor conjugada resuelta. Las propiedades térmicas, temperatura, flujo, base/apoyo, superficies STL y solidificación todavía no se han validado.

### Nueva preparación independiente de temperatura inicial, SIN CFD

Se añadió `analysis_tools/stage_fs_c04_initial_temperature.py` y su suite de pruebas. Hace una **copia aislada** de la copia nativa validada `FS_C04_ALPHA_NATIVE_CHECK_20261119T045227Z_50756897`, pero solo después de volver a ejecutar la auditoría de **3136 caras, áreas, orientación y procedencia del campo `alpha.metal`**. Luego crea:
- `0/fluid/T`: valor **1500 K** solo donde `alpha.metal=1` inicialmente (2368 celdas) y **300 K** en el aire conectado (32000 celdas).
- `0/mold/T`: **300 K** inicial uniforme en las 7680 celdas de arena.
- Todos los parches de `T` reciben `type calculated; value uniform 300;` **solo como marcadores de lectura NO APTOS PARA CORRER UN SOLVER**; no se han implementado `coupledTemperature` ni las condiciones térmicas abiertas de un flujo gas–metal real. **PROHIBIDO usar `foamRun`/`foamMultiRun` sobre ese estado de preparación**.
- Se comprueban los 42,048 valores de T contra `alpha.metal`, el volumen/áreas preexistentes, el formato `volScalarField`, unidades Kelvin y que la arena no contenga un campo VOF. Los SHA de malla y `alpha` se verifican sin sobrescribir originales.

**Las temperaturas 1500 K y 300 K son hipótesis iniciales de cribado derivadas de C14/FS-C02, NO resultados medidos ni propiedades calibradas.** Los parámetros termofísicos de `C3D-02` (por ejemplo, `rho_iron=6820 kg/m³`, `Cp_iron=827 J/(kg K)`, `rho_sand=1500 kg/m³`, `Cv_sand=700 J/(kg K)`, `k_sand=2 W/(m K)`) están documentados allí, pero **NO están instalados automáticamente**: no representan por sí solos un modelo de mezcla metal–aire VOF dependiente de temperatura ni un balance energético validado. No sustituir el aire exterior por `externalWallHeatFluxTemperature(h=10, Ta=300)` en las paredes de arena.

Comandos SOLO para preparar T (aún no ejecutados en la laptop):

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_stage_fs_c04_initial_temperature.py -v &&
python3 analysis_tools/stage_fs_c04_initial_temperature.py \
  --accepted ~/OpenFOAM/FS_C04_ALPHA_NATIVE_CHECKS/FS_C04_ALPHA_NATIVE_CHECK_20261119T045227Z_50756897
```

Estado esperado, **NO CONFIRMADO LOCALMENTE**: `INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT`. Siguiente gate tras eso: `foamPostProcess` de T a `t=0` en otra copia, comprobando lectura de ambos `volScalarField` sin solver y cálculo ponderado por volumen. No confundir T inicial con predicción de enfriamiento o solidificación. La base del QuickCup y su abertura inferior siguen pendientes.
