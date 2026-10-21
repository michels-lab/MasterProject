# Plan D — caso científico `case3d-01`

**Nombre oficial de caso: `case3d-01`**. Este es el espacio canónico de la línea de investigación **Plan D**: fundición de hierro en molde de arena, modelo tridimensional QuickCup.

## Estado actual

- Preparada y documentada la geometría STL de metal y arena.
- Malla de fondo prevista: 58×72×58 mm, 29×36×29 celdas a 2 mm nominales.
- **NO** se ha ejecutado todavía `blockMesh`, `checkMesh`, `snappyHexMesh` ni el solver de solidificación en un registro disponible.
- Por lo tanto, no hay malla de metal–arena, intercambio conjugado validado, independencia de malla ni resultado experimental validado.
- Los cambios de refinamiento de volumen a 0.5 mm y los límites científicos de ese refinamiento pertenecen a **PR #18 y PR #19**, ambos abiertos. No los fusionar conceptualmente ni imponer como resolución demostrada.

La carpeta histórica `cases_3d/C3D_01_metal_mold/` conserva temporalmente **los archivos técnicos fuente** mientras dichos PR editan ese directorio. Este directorio `cases_3d/case3d-01/` conserva la nomenclatura canónica, una nueva herramienta segura para preparar **una copia local de ejecución** y la documentación de su trazabilidad. No es aún un caso OpenFOAM completo ejecutable directamente desde GitHub. **No borrar ni renombrar** el directorio antiguo mientras existan cambios simultáneos.

## Preparar una copia nueva con el nombre correcto

Desde la raíz del repositorio y en Ubuntu, con ambos STL originales en la carpeta indicada:

```bash
bash cases_3d/case3d-01/scripts/stage_mesh_only.sh \
  /tmp/case3d-01-meshA \
  "$HOME/OpenFOAM/Piezas_STL"
```

Este script valida las huellas SHA-256 de `QuickCup.STL` y `metal.STL` antes de copiar byte a byte sin alterar escala, orientación ni origen; incorpora el `blockMeshDict` y el script de diagnóstico antiguos a una carpeta nueva. Rechaza sobreescritura, enlaces simbólicos de STL y colocación del destino dentro del repositorio. No crea superficies STL públicamente en Git.

El resultado es **solo una copia preparada para mallado de fondo**, no para CFD. En la nueva carpeta, bajo Foundation v14:

```bash
source /opt/openfoam14/etc/bashrc
cd /tmp/case3d-01-meshA
bash scripts/run_blockMesh_only.sh
```

Si el script deja logs, conservarlos. Antes de proceder a `snappyHexMesh`, revisar que el valor `Mesh OK.`, la cantidad de celdas, bounds y geometría sean coherentes.

## Auditar fuentes, STL y evidencia de malla

Sin STL privados ni logs, el siguiente comando inspecciona solo los datos versionados y reporta **NOT_RUN**:

```bash
python3 analysis_tools/granada_plan_d_case3d01_mesh_gate.py \
  --root . --out /tmp/case3d-01-source-audit
```

Tras una prueba real de mallado, para auditar sus registros y los STL originales:

```bash
python3 analysis_tools/granada_plan_d_case3d01_mesh_gate.py \
  --root . \
  --stl-dir "$HOME/OpenFOAM/Piezas_STL" \
  --log-blockmesh /tmp/case3d-01-meshA/log.blockMesh \
  --log-checkmesh /tmp/case3d-01-meshA/log.checkMesh.background \
  --out /tmp/case3d-01-mesh-evidence \
  --require-stls --require-mesh-logs
```

La auditoría no abre ni modifica los archivos originales. Sus checks de logs son un cribado de texto + hash, **no una ejecución independiente de `checkMesh`**. Hasta ejecutar el solver y disponer de datos termofísicos, no aceptar balances térmicos ni recalescencia.

## Por qué no se declara 0.5 mm como malla válida

El refinamiento de 2 mm a 0.5 mm significa dos niveles octree nominales, no una prueba de una arista máxima de 0.5 mm en celdas ajustadas. La red de dendritas primaria se representa macroscópicamente con leyes de zona pastosa, no por una afirmación de que cada celda debe ser del tamaño dendrítico. La resolución se escogerá mediante datos de `snappyHexMesh`, calidad por regiones, estabilidad del solver y convergencia de magnitudes físicas, sin sustituir opinión del director y propiedades verificadas.

Documentación ampliada: [Plan D — gate científico](../../docs/granada/PLAN_D_CASE3D_01_MESH_GATE_20261021.md). El trabajo de superficie libre [FS-C01](../../freesurface/FS-C01) es una línea separada, no el mismo caso.
