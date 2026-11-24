# Caso A C3D04: auditoría de la malla activa tras fallos de cellZone en _03

**24-nov-2026 · Etapa 7/10; 6/10 hitos, 60 %.** Esta auditoría no valida física ni balance energético.

## Evidencia real de WSL

El investigador ejecutó la inspección read-only de la copia de postprocesamiento C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_03. El origen y la copia tienen hashes coherentes para el log del solver, y los seis registros nativos están presentes. No se ejecutó nuevamente OpenFOAM en esta inspección.

Cuatro grupos, core, energy, flow y momentum, acumularon **100 eventos FOAM FATAL IO ERROR cada uno**. Causa declarada por F14: **Cannot find cellZone metal; Available cellZones: 0()**, en constant/metal/fvModels!phaseChangeSource/cellZone. Los cuatro están FALLIDOS aunque su exit code del sistema sea 0.

Phase y profiles no muestran FOAM FATAL. La media nativa de fracción líquida al t10 = **0.897245**. Los perfiles horizontales a y=10,20,30 mm tienen **80 puntos finitos** cada uno, pero el perfil vertical x=20mm tiene sólo **27 puntos**; falta su validación. Las tres tablas native metalTopEnergyPower, metalMoldEnergyPower y metalBoundaryEnergyPower contienen exactamente **una fila, t=0**, por lo que NO hay curva energética de 100/101 puntos ni conservación verificable.

La reparación materializada de la zona funcionó en un caso CI sintético 27+27 celdas de F14 pero no ha funcionado en el V4/T02 real. Este es un hecho; la causa adicional no se conoce. En particular, no se debe afirmar que los 100 FATAL se solucionaron con la primera reparación.

## Nueva herramienta de solo lectura

Archivo: cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/audit_c14_stage07_active_cellzone.py

La herramienta:

1. Verifica SHA original y copia para el log del solver de 10s, la identidad del informe final de seis grupos y los SHA de los logs nativos.
2. Lee la propiedad metal_cellZone_copy_only_recovery del reporte real original de la copia, no visible en el resumen del usuario.
3. Audita el archivo cellZones en constant/metal/polyMesh de CFD original y copia, verificando una zona metal que cubre exactamente las **8960 celdas**; también confronta hashes de points, faces, owner, neighbour y boundary.
4. Enumera directorios numéricos de malla, como 0/metal/polyMesh y 0.1/metal/polyMesh, si existen. Una instancia temporal sin la zona completa es **posible** causa de desajuste, no prueba de cuál instancia cargó F14.
5. Reporta cuatro conteos de errores fatales, coberturas de tablas y perfiles reales. Nunca altera malla ni genera otra copia.

### Una ejecución en WSL

Tras fusionar el nuevo código en main, usar exclusivamente worktree A:

~~~bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/audit_c14_stage07_active_cellzone.py"
~~~

No ejecutar otra vez el posprocesamiento completo, ni borrar _03, ni crear _04 por inercia. Esta inspección NO llama foamPostProcess, foamMultiRun, checkMesh, bloqueMesh ni modifica archivos. Cuando los datos indiquen qué zona y qué instancia está activa, se podrá construir una prueba nativa selectiva latestTime en otro destino aislado, sin recalcular CFD 10s.

**Situación científica:** CFD original de 10s y 101 estados preservados; fase alpha1 y promedios térmicos ya publicados sin validación QuickCup; energía nativa metal/molde, derivadas de 0.001s y conservación siguen abiertas. **Etapa 7/10, 6/10 hitos (60 %).**
