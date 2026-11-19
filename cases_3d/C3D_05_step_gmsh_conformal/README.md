> **18-11-2026 — ATENCIÓN: ENSAYO FRONTAL REALMENTE FALLÓ ANTES DE MALLAR EN 3D:** ejecución WSL de `run_frontal_pilot.sh` confirmó que el binario Gmsh **requiere Netgen** para algoritmo 3D 4 (`Error: Frontal algorithm requires Netgen`), soporte que esta instalación no ofrece. **No existe malla 3D Frontal; es `BLOCKED_DEPENDENCY`, NO un rechazo de checkMesh.** Preservada `~/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01`, control Delaunay intacto. Nuevo ensayo independiente Gmsh **HXT=10** disponible, con [preflight in-memory](scripts/preflight_hxt.py) y [runner seguro de UNA sola orden](scripts/run_hxt_pilot.sh). Tras `git pull`: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh`. Si no soporta HXT se detiene antes del mallado QuickCup; si lo soporta, crea `C3D05_STEP_GMSH_HXT_01`, ejecuta los mismos gates estrictos, no sobrescribe y no hace CFD. **HXT aún no ejecutado**, éxito no garantizado (tetraedros de arista pueden repetir fallo). [Evidencia completa](../../docs/C3D_05_FRONTAL_NETGEN_BLOQUEO_HXT_20261118_ES.md).

> **18-11-2026 — C3D-05: RESULTADO NATIVO DE INTERFAZ Y ARISTAS; NUEVO ENSAYO FRONTAL PREPARADO:** metal 96/96 underdetermined con 2 caras internas/2 frontera (metalTop+metal_to_mold); arena 402/402 con 2 internas/2 frontera (96 exterior+interfaz, 306 exterior+exterior). **Contacto aprobado:** 16,218 caras por lado, área recíproca 6,348.106691699194 mm² y `contact_gate=true` (−0.0713 % frente STL); techo metal 1,326.5776804745685 mm² (−0.0232 %). El checkMesh original **sigue rechazado** por determinante, no CFD. Un solo bloque de terminal: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh`; produce un **ensayo NUEVO** en `~/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01`, deja intacta la malla original, altera únicamente `Mesh.Algorithm3D` 1 Delaunay→4 Frontal y ejecuta automáticamente comprobaciones nativas/área/diagnóstico. **Frontal preparado, aún NO EJECUTADO.** [Detalle de datos y método](../../docs/C3D_05_AREA_ARISTAS_Y_ENSAYO_FRONTAL_20261118_ES.md).

> **REGLA DEL INVESTIGADOR — UN SOLO COMANDO:** a partir de esta fecha NO separar `git pull`, pruebas, inspección topológica y auditoría de área en varias instrucciones. Ejecutar solo el orquestador de diagnóstico existente `scripts/run_full_diagnostics.sh`, que NO remalla ni ejecuta CFD y preserva los logs del intento Gmsh previo. Comando canónico: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_full_diagnostics.sh`. [Norma global para todo MasterProject](../../docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).

> **18-11-2026 — CAUSA EXACTA DEL RECHAZO IDENTIFICADA EN LOGS NATIVOS:** `checkMesh` Foundation 14 reportó **`***Cells with small determinant (< 0.001)`** como **único check fallido**: **306 celdas en malla conjunta**, **96 metal y 402 arena** tras `splitMeshRegions`. Volúmenes, conectividad, skewness, no ortogonalidad, caras tetraédricas y concavidad **OK**. La interfaz tiene **16,218 caras recíprocas `mappedWall`**, aún sin validación numérica de su área. El cambio de 306 a 498 celdas regionales requiere analizar la topología interna/frontera, no solo la geometría de tetraedros. Se agregó [`audit_underdetermined_topology.py`](scripts/audit_underdetermined_topology.py) (solo lectura de `cellSet`, `owner`, `neighbour`, parches) y [diagnóstico científico completo](../../docs/C3D_05_DIAGNOSTICO_DETERMINANTE_20261118_ES.md). **Mantener caso preservado rechazado, NO CFD; no cambiar tolerancia ni remallar sin identificar patrón.**

> **18-11-2026 — PRIMER MALLADO NATIVO C3D-05 RECHAZADO EN CALIDAD, EVIDENCIA PRESERVADA:** OpenFOAM Foundation 14 generó desde los STEP originales **190,365 celdas de metal y 335,341 de arena (525,706 totales)**. Los volúmenes nativos fueron **4.79675605036e-5 m³ metal** y **1.02843547305e-4 m³ arena**, desviaciones frente a CAD de **−0.042 % y +0.0002 %**. **`mesh_ok NO` para ambas regiones; `REJECTED / stage=CHECK_REGION_QUALITY`**. Los datos citados son de la terminal del investigador; el motivo concreto de los checks fallidos **NO SE CONOCE hasta leer los logs locales**. La auditoría de `mappedWall`/área NO llegó a ejecutarse. **No repetir el Gmsh ni borrar la salida**. Carpeta preservada `~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`. Inspeccionar sin remallar: `python3 cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py ~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`. [Resultados, limitaciones y protocolo de diagnóstico](../../docs/C3D_05_RESULTADO_PRIMER_MALLADO_20261118_ES.md). **NO CFD**.

> **18-11-2026 — Resultado REAL del primer preflight en WSL:** tras `git pull --ff-only`, el test `tests/test_step_gmsh_static.sh` pasó y verificó hashes SHA-256 de los dos STEP. Pero `python3 -c "import gmsh"` produjo **`ModuleNotFoundError: No module named 'gmsh'`**: faltan los bindings Gmsh para el Python activo. **No se ejecutó `Allmesh` ni CAD import, mallado, conversión o CFD.** Ubuntu 26.04 tiene paquete `python3-gmsh` en repositorios `universe`; instalar con `sudo apt update && sudo apt install -y python3-gmsh gmsh` y repetir `python3 -c 'import gmsh; print(gmsh.__version__)'` antes de ejecutar `Allmesh`. Si falla la importación pese a instalar, comparar `command -v python3` y `/usr/bin/python3 -c 'import gmsh; print(gmsh.__version__)'`: el intérprete activo puede pertenecer a un entorno diferente. No usar `sudo pip install` ni instalar paquetes sin que lo haga el dueño de la laptop.

> **18-11-2026 — CAD ORIGINAL VERSIONADO EN GITHUB:** los dos STEP AP214 auténticos **ya están incorporados a `main`, bit a bit idénticos a los adjuntos** (comprobación mediante Git SHA-1 de los archivos originales y blob remoto). [Metal `metalmm.STEP`](constant/geometry/metalmm.STEP) (SHA256 `ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475`) y [molde `QuickCupmm.STEP`](constant/geometry/QuickCupmm.STEP) (SHA256 `fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c`). **Ya no necesitas enviar ni copiar los archivos**: `git pull --ff-only` los descargará, y `Allmesh` selecciona las dos rutas del repositorio de manera automática y comprueba los SHA. `C3D05_METAL_STEP` y `C3D05_MOLD_STEP` permanecen como sobrescrituras opcionales para futuros ensayos controlados. **No hay Gmsh, conversión nativa, `checkMesh` ni CFD ejecutados todavía**.

> **18-11-2026 — STEP YA RECIBIDOS Y VERIFICADOS EN CHAT:** `metalmm.STEP` y `QuickCupmm.STEP` exportados desde SolidWorks 2026, STEP AP214, **un sólido válido por archivo**. Volúmenes CAD **47,988.524998 mm³ metal** y **102,843.320825 mm³ molde**. La unión booleana da un único sólido, volumen igual a la suma y un área interior compartida deducida de **6,352.821119 mm²**, diferencia apenas **+0.00295 %** frente a STL. **Aclaración de unidades:** ambos STEP declaran **SI metros** internamente; OCC lee e interpreta en milímetros, y el mallado a OpenFOAM debe convertirse a metros exactamente una vez. [Evidencia completa y SHA](../../docs/C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md). Los archivos recibidos ya se versionaron **sin cambios de bytes** dentro de `constant/geometry/`; la copia en WSL queda disponible tras el siguiente `git pull`. Por tanto el *bloqueo de obtención y versionado CAD está resuelto*; todavía hay que verificar Gmsh en WSL y ejecutar `Allmesh` para obtener una malla nativa. **NO CFD**.

# C3D-05 — Ruta paralela CAD multivolumen STEP → Gmsh → OpenFOAM 14

**18-11-2026 — Preparado en GitHub, NO ejecutado:** ruta tridimensional **independiente de `blockMesh`**. Su objetivo es comparar el mallado tetraédrico/no estructurado de dos sólidos CAD en un dominio conformante contra el multibloque curvilíneo `C3D-04`. **No existe todavía una malla C3D-05 aprobada ni CFD 3D.**

## ¿Por qué no es lo mismo que C3D-04?

- `C3D-03`: 3D `blockMesh` de 24 bloques, contornos rectos; **se ejecutó y pasó checkMesh**.
- `C3D-04`: 3D **curvilíneo con `blockMesh`**, 180 bloques, 144 arcos de esquina y refinamiento de base; **preparado, no ejecutado en WSL**.
- **`C3D-05` (este caso):** **Gmsh + OpenCASCADE**, importación de dos sólidos **STEP reales de SolidWorks**, `fragment` de los dos volúmenes para obtener **una sola cara común**, generación de mallado no estructurado, exportación MSH2 ASCII (coordenadas en metros), conversión nativa con `gmshToFoam` Foundation14 y separación mediante `splitMeshRegions`.

En el caso original del doctor, metal y arena compartían caras de bloques desde `blockMesh`. Aquí el principio científico es **el mismo contacto topológicamente compartido**, pero **el mallador y la representación CAD son distintos**.

## CAD original disponible en este repositorio

**Los dos STEP sólidos auténticos ya están en `constant/geometry/`, exportados desde SolidWorks con el mismo sistema de referencia** (coordenadas físicas de la pieza en mm, cabecera STEP declara SI metros internamente):

- [`metalmm.STEP`](constant/geometry/metalmm.STEP): volumen de hierro solamente, ~47,987.697 mm³, altura Y=-40 a 0 mm.
- [`QuickCupmm.STEP`](constant/geometry/QuickCupmm.STEP): arena sólida, excluyendo el volumen interior ocupado por el hierro, ~102,843.333 mm³, altura Y=-65.5 a 0 mm, exterior X/Z 0 a 51.8 mm y abertura inferior rectangular 22.5×27.5 mm hasta Y=-56 mm.

Ambos cuerpos deben ocupar **sus coordenadas globales originales** sin reorientaciones individuales, compartir interfaces geométricas y no solaparse. No usar STL renombrados, no fabricar STEP a partir de las cajas envolventes ni mezclar archivos con diferentes orígenes. Los STEP pueden permanecer en la laptop: el script registra sus hashes SHA256 y rutas. Los STEP ya son insumos versionados y verificados. El paso pendiente es **verificar disponibilidad de Gmsh/Python y compatibilidad de conversión con OpenFOAM Foundation 14 en WSL**, no conseguir nuevos archivos.

## Por qué se usa `fragment`

`gmsh.model.occ.fragment` procesa ambos volúmenes como un solo problema geométrico, identifica su superficie de contacto y permite generar **una malla conformante**. Los volúmenes se etiquetan mediante `Physical Volume("metal")` y `Physical Volume("mold")`; superficies con etiquetas temporales `metal_mold_contact`, `metalTop` y `moldOuterUnclassified`. Esta última **NO es una BC térmica aprobada**; la clasificación posterior de pared superior, base, exterior y paredes de abertura sigue pendiente. La conversión a OpenFOAM debe **probar** que conserva las dos zonas y crea parches `mappedWall` recíprocos; el código rechaza resultados dudosos.

Documentación técnica externa: [Gmsh t16 / OpenCASCADE fragment](https://gmsh.info/doc/texinfo/gmsh.html#t16); [Gmsh t20 / STEP](https://gmsh.info/doc/texinfo/gmsh.html#t20).

## Puertas del script — sin física ni solver

Antes de mallar, `scripts/build_step_mesh.py` obliga a confirmar:

1. Dos **sólidos CAD cerrados** importables; un volumen por archivo.
2. Fragmentación que deje **solo una región `metal` y una `mold`**, sin fragmentos volumétricos adicionales ni solapamiento.
3. Volumen de metal y arena **dentro de ±2 %** de los STL autorizados.
4. Superficie común metal–arena, incluyendo laterales y fondo, dentro de **±3 %** de 6,352.634 mm².
5. `metalTop` dentro de **±3 %** de 1,326.886 mm², sin otras caras metálicas expuestas inesperadas.
6. Dimensiones globales de arena ~51.8 × 65.5 × 51.8 mm (tolerancia de lectura 0.30 mm).
7. Exportación `Mesh.ScalingFactor=0.001`: modelo OCC en mm, malla MSH2 en m (solo una conversión).

Después, `Allmesh` ejecuta `gmshToFoam`, `checkMesh -allGeometry -allTopology` del padre y ambas regiones, `splitMeshRegions -cellZones 'metal mold' -noFields`, auditoría de parches y áreas de sus caras. La medida nativa del área de contacto debe coincidir entre metal y arena dentro de **0.1 %** y con el CAD dentro de **±3 %**. Los conteos de caras de una malla no estructurada **no tienen por qué coincidir con los 2,496 de C3D-04**.

**Ninguna de estas puertas garantiza por sí sola fidelidad geométrica punto a punto, independencia de malla, correctas BC térmicas o estabilidad CFD.**

## Cómo ejecutar una vez que existan los STEP

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_05_step_gmsh_conformal/tests/test_step_gmsh_static.sh

# Los dos STEP auténticos ya están incluidos en el repositorio.
# `Allmesh` los detecta sin variables de entorno.
# Opcional: C3D05_METAL_STEP y C3D05_MOLD_STEP permiten probar otros CAD.

# Verificar disponibilidad de Gmsh / Python / Foundation14 en tu máquina:
python3 -c 'import gmsh; print("Gmsh Python OK")'
source /opt/openfoam14/etc/bashrc
command -v gmshToFoam

# Crear salida independiente, sin solver:
bash cases_3d/C3D_05_step_gmsh_conformal/Allmesh
```

**Salida preservada**: `~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`; rechaza carpetas existentes. Si se necesita otro ensayo, crear un destino **nuevo** mediante `C3D05_OUT=/ruta/absoluta/nueva`. La disponibilidad y versión exacta del módulo Python `gmsh` y de `gmshToFoam` en la laptop **todavía no están comprobadas**.

Si OpenFOAM rechaza conversión o `checkMesh`, preservar `log.gmsh3d`, `log.gmshToFoam`, `log.splitMeshRegions`, `log.checkMesh.*`, `STEP_CAD_AUDIT.json`, `PILOT_MESH_REPORT.tsv`, `CONTACT_AREA_REPORT.json` y `NATIVE_BUILD_STATUS.txt`. No ejecutar `foamMultiRun`.

## Comparación futura A/B

Evaluar ambos contra los **mismos STL oficiales**, versión OF14 y umbrales: volumen, área de contacto, forma del frente de solidificación/base, distancia superficial al STL, proporción de celdas de mala calidad, cantidad de elementos, tiempo de mallado, costo de CPU y, después de validar BC, convergencia y `Co_max` observado. **No seleccionar ganador por el número de celdas ni solo por `Mesh OK`.**

- [C3D-04 curvilíneo mediante blockMesh](../C3D_04_rounded_multiblock_pilot/README.md)
- [C3D-03 resultado medido](../../docs/C3D_03_RESULTADO_NATIVO_20261118_ES.md)
- [Criterios comparativos A/B](../../docs/C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md)
