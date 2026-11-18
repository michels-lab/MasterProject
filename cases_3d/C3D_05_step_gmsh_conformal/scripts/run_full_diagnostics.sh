#!/usr/bin/env bash
# C3D-05: ONE-COMMAND read-only diagnosis of the preserved STEP/Gmsh mesh.
# Never generates/modifies mesh or calls Gmsh, OpenFOAM or a CFD solver.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_ROOT="$CASE_ROOT/tests"
MESH_CASE="${1:-$HOME/OpenFOAM/C3D05_STEP_GMSH_PILOT_01}"

if [[ ! "$MESH_CASE" = /* ]]; then
    echo "ERROR: pass an absolute path to the preserved mesh case" >&2
    exit 2
fi
if [[ ! -d "$MESH_CASE/constant/metal/polyMesh" ||
      ! -d "$MESH_CASE/constant/mold/polyMesh" ]]; then
    echo "ERROR: saved metal/mold meshes missing: $MESH_CASE" >&2
    exit 2
fi

echo "=== C3D-05 | DIAGNÓSTICO ÚNICO | SIN REMALLADO NI CFD ==="
echo "Malla preservada: $MESH_CASE"
echo
echo "=== 1/3: Pruebas de código, sin tocar la malla ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TEST_ROOT" \
    -p "test_*diagnos*.py" -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TEST_ROOT" \
    -p "test_audit_underdetermined_topology.py" -v
echo
echo "=== 2/3: Celdas de bajo determinante y parches ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B \
    "$SCRIPT_DIR/diagnose_existing_mesh.py" "$MESH_CASE"
PYTHONDONTWRITEBYTECODE=1 python3 -B \
    "$SCRIPT_DIR/audit_underdetermined_topology.py" "$MESH_CASE"
echo
echo "=== 3/3: Área real de la interfaz, solo lectura de polyMesh ==="
# The area script accepts a new report path only. Never touch existing reports.
# Use stdout for a repeat invocation, while preserving old saved evidence.
candidate="$MESH_CASE/CONTACT_AREA_DIAGNOSTIC_ONLY.json"
if [[ -e "$candidate" ]]; then
    echo "Ya existe $candidate. Se conserva sin modificar."
    echo "No se sobrescribe el reporte existente: se auditará con la misma fuente."
    # An extra new temporary report would pollute preserved evidence. Instead
    # display existing report if parseable, and ask to compare its fingerprint.
    PYTHONDONTWRITEBYTECODE=1 python3 -B -m json.tool "$candidate"
else
    # A failure of area-gate is scientific evidence. Save JSON if it was
    # produced, then return without claiming success.
    if ! PYTHONDONTWRITEBYTECODE=1 python3 -B \
        "$SCRIPT_DIR/measure_interface_area.py" "$MESH_CASE" --out "$candidate"; then
        echo "ADVERTENCIA: el cálculo de área o su puerta CAD falló; conservar los datos y compartir el resultado." >&2
        exit 5
    fi
fi
echo
echo "DIAGNÓSTICO COMPLETO: ni Gmsh ni OpenFOAM ni CFD fueron ejecutados."
echo "La aceptación nativa de checkMesh continúa RECHAZADA hasta nueva malla validada."
