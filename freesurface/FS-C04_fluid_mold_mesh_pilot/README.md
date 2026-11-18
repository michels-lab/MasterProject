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
