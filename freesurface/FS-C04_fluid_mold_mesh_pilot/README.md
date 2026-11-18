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
