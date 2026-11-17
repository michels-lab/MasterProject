#!/usr/bin/env bash
# C3D-02 — one controlled A/B test: mold cellZone L2 snap=false -> snap=true.
# Source STL, point, blockMesh, refinement, meshQualityControls unchanged.
# Fresh cases ONLY, no edits to metal, previous meshes, C14 or CAD; NO CFD.
source /opt/openfoam14/etc/bashrc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="$HOME/OpenFOAM/C3D02_materials"
PREVIOUS="$BASE/mold_extracted_l2_01"
PARENT="$BASE/mold_zoned_snap_l2_01"
EXTRACT="$BASE/mold_extracted_snap_l2_01"
TEMPLATE="$ROOT/system/materialSingle/snappyHexMeshDict.template"
STL=mold_repaired.stl
POINT='(0.0043 -0.0207 0.0259)'
CAD_VOLUME=0.00010284309608

[[ "${WM_PROJECT_VERSION:-}" == 14 ]] || {
    echo "ERROR: usar OpenFOAM Foundation 14"; exit 2;
}
bash "$ROOT/tests/test_sources.sh"
for f in \
    "$PREVIOUS/log.checkMesh.full" \
    "$BASE/mold_zoned_l2_01/log.snappyHexMesh" \
    "$ROOT/constant/geometry/$STL" \
    "$ROOT/system/blockMeshDict" \
    "$TEMPLATE"; do
    [[ -f "$f" ]] || { echo "ERROR: falta $f; no ejecutar ensayo"; exit 2; }
done
grep -Fq 'Failed 2 mesh checks' "$PREVIOUS/log.checkMesh.full" || {
    echo "ERROR: falta evidencia de calidad del ensayo A"; exit 2;
}
for dest in "$PARENT" "$EXTRACT"; do
    [[ ! -e "$dest" && ! -L "$dest" ]] || {
        echo "ERROR: $dest ya existe; NO sobrescribir el ensayo"; exit 2;
    }
done
for tool in foamDictionary blockMesh snappyHexMesh subsetMesh checkMesh; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: falta utilidad $tool"; exit 2;
    }
done
echo "=== C3D-02: A/B SOLO EFECTO DE snap=false A snap=true ==="
echo "A: $PREVIOUS (274788 celdas, 103.409 cm3; 22737 cóncavas, 1 determinante bajo)"
echo "B nuevo: $PARENT -> extracción en $EXTRACT"
echo "El STL, celda base 2 mm, level (2 2), insidePoint y calidad quedan idénticos."
echo "Nunca se reusa ni sobrescribe A, metal, geometrías o propiedades."

mkdir -p "$PARENT/system" "$PARENT/constant/geometry"
cp -p "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" "$PARENT/system/"
cp -p "$ROOT/constant/geometry/$STL" "$PARENT/constant/geometry/"
python3 - "$TEMPLATE" "$PARENT/system/snappyHexMeshDict" "$STL" "$POINT" <<'PY'
from pathlib import Path
import sys

src, dest, stl, point = sys.argv[1:]
data = Path(src).read_text(encoding="utf-8")
changes = (
    ("MATERIAL_STL_PLACEHOLDER", stl),
    ("MATERIAL_POINT_PLACEHOLDER", point),
    ("level (2 2);", """level (2 2);
            faceZone moldInterface;
            cellZone moldVolume;
            mode inside;
            faceType internal;"""),
)
for old, new in changes:
    if data.count(old) != 1:
        raise SystemExit(f"ERROR: plantilla cambió; {old!r} no aparece exactamente una vez")
    data = data.replace(old, new, 1)
if data.count("snap true;") != 1 or "snap false;" in data:
    raise SystemExit("ERROR: no está habilitado EXCLUSIVAMENTE snap=true")
if data.count("addLayers false;") != 1:
    raise SystemExit("ERROR: no se autorizó generar capas")
Path(dest).write_text(data, encoding="utf-8")
PY

# Strict static gate before any mesher starts.
for entry in \
    castellatedMeshControls/refinementSurfaces/material/cellZone \
    castellatedMeshControls/refinementSurfaces/material/faceZone \
    castellatedMeshControls/refinementSurfaces/material/mode \
    castellatedMeshControls/insidePoint; do
    foamDictionary -case "$PARENT" system/snappyHexMeshDict -entry "$entry" \
        >> "$PARENT/log.preflight" 2>&1 || {
        echo "ERROR: no se reconoció $entry"; tail -n 30 "$PARENT/log.preflight"; exit 3;
    }
done

echo "=== ETAPA B1: blockMesh y snappyHexMesh L2 CON snap (solo caso nuevo) ==="
if ! blockMesh -case "$PARENT" > "$PARENT/log.blockMesh" 2>&1; then
    echo "ERROR: blockMesh. Ver log.blockMesh"; tail -n 45 "$PARENT/log.blockMesh"; exit 3;
fi
if ! snappyHexMesh -case "$PARENT" -overwrite > "$PARENT/log.snappyHexMesh" 2>&1; then
    echo "ERROR: snappyHexMesh. El caso nuevo se conserva para diagnóstico."
    tail -n 70 "$PARENT/log.snappyHexMesh"; exit 4;
fi

# Ensure the snapped source still contains the desired zones.
for zone in "$PARENT/constant/polyMesh/cellZones" "$PARENT/constant/polyMesh/faceZones"; do
    [[ -f "$zone" ]] || { echo "ERROR: falta $zone"; exit 4; }
done
grep -Fq moldVolume "$PARENT/constant/polyMesh/cellZones" || {
    echo "ERROR: cellZone moldVolume no sobrevivió al snapping"; exit 4;
}
grep -Fq moldInterface "$PARENT/constant/polyMesh/faceZones" || {
    echo "ERROR: faceZone moldInterface no sobrevivió al snapping"; exit 4;
}

echo "=== ETAPA B2: subsetMesh SOLO EN COPIA FISICA NUEVA ==="
mkdir -p "$EXTRACT/constant" "$EXTRACT/system"
cp -a -- "$PARENT/constant/polyMesh" "$EXTRACT/constant/polyMesh"
cp -p -- "$PARENT/system/controlDict" "$EXTRACT/system/controlDict"
[[ -z "$(find "$EXTRACT/constant/polyMesh" -type l -print -quit)" ]] || {
    echo "ERROR: copia inesperadamente contiene symlinks; ABORTAR"; exit 4;
}
if ! subsetMesh -case "$EXTRACT" -cellZone moldVolume -noFields \
    > "$EXTRACT/log.subsetMesh" 2>&1; then
    echo "ERROR: subsetMesh sobre copia B. Revisar log.subsetMesh."
    tail -n 70 "$EXTRACT/log.subsetMesh"; exit 4;
fi

echo "=== ETAPA B3: checkMesh EXHAUSTIVO y VTK en copia B ==="
# -writeSets/-writeSurfaces are supported on this specific Foundation 14
# installation according to the user's previous local checkMesh -help.
set +e
checkMesh -case "$EXTRACT" -allGeometry -allTopology -writeSets -writeSurfaces \
    > "$EXTRACT/log.checkMesh.full" 2>&1
rc=$?
set -e
grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|Face tets|small determinant|Concave cells|two non-boundary|Failed [0-9]+ mesh checks|Mesh OK' \
    "$EXTRACT/log.checkMesh.full" | tail -n 32 || true

echo "=== COMPARACIÓN NUMÉRICA Y VEREDICTO ==="
python3 - "$EXTRACT" "$PREVIOUS" "$CAD_VOLUME" "$rc" <<'PY'
from pathlib import Path
import re
import sys

current, baseline, cad, rc = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
def stats(folder):
    text = (folder / "log.checkMesh.full").read_text(errors="replace")
    def get(pattern, default=None):
        m = re.search(pattern, text, flags=re.I)
        return m.group(1) if m else default
    volume = get(r"Total volume\s*=\s*([0-9.eE+-]+)")
    cells = get(r"(?m)^\s*cells:\s*(\d+)")
    regions = get(r"Number of regions:\s*(\d+)")
    concave = get(r"Concave cells .*?number of cells:\s*(\d+)", "0")
    det = get(r"Cells with small determinant.*?number of cells:\s*(\d+)", "0")
    failed = get(r"Failed\s+(\d+)\s+mesh checks", "0")
    if volume is None or cells is None or regions is None:
        raise ValueError(f"checkMesh no reportó todas las métricas: {folder}")
    boundary = (folder / "constant/polyMesh/boundary").read_text(errors="replace")
    match = re.search(r"\bouterBox\s*\{[^}]*?\bnFaces\s+(\d+);", boundary, re.S)
    outer = int(match.group(1)) if match else 0
    return {
        "cells": int(cells), "volume": float(volume), "regions": int(regions),
        "concave": int(concave), "det": int(det), "failed": int(failed),
        "outer": outer, "ok": "Mesh OK" in text and not int(failed),
    }

a, b = stats(baseline), stats(current)
for label, val in (("A: L2 snap=false", a), ("B: L2 snap=true", b)):
    print(
        f"{label} | cells={val['cells']:,d} V={val['volume']*1e6:.5f} cm3 "
        f"(CAD delta={100*(val['volume']/cad-1):+.3f}%), outerBox={val['outer']}, "
        f"regions={val['regions']}, concave={val['concave']:,d}, "
        f"lowDet={val['det']}, failedChecks={val['failed']}"
    )
improvement = a["concave"] - b["concave"]
print(
    f"Celdas cóncavas tras snap: {improvement:+,d} menos "
    f"({100*improvement/max(a['concave'],1):+.2f}% de cambio respecto a A)."
)
print("Ruta de la copia B:", current)
print("checkMesh exit code:", rc, "(NO usarlo solo como criterio de aprobación)")
if b["cells"] <= 0 or b["regions"] != 1 or b["outer"] != 0:
    print("RECHAZADO: topología o aislamiento de la arena no conservados.")
    sys.exit(5)
if abs(b["volume"] / cad - 1) > 0.05:
    print("RECHAZADO: el nuevo volumen supera la tolerancia exploratoria de ±5% CAD.")
    sys.exit(5)
if rc or not b["ok"]:
    print("RESULTADO: geometría aislada plausible, pero calidad NO APROBADA.")
    print("No ejecutar CFD, no relajar umbrales. VTK y logs están en la copia B.")
    sys.exit(5)
print("CHECKMESH de B sin fallos; FALTAN validación de contacto, fronteras y CHT.")
PY
