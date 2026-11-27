#!/usr/bin/env bash
# Caso B C3D05: REAL new F14 10s CFD with EXACT original C14 functionObjects.
# No unit tests. No original CFD modifications. No blockMesh/splitMeshRegions.
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO="$(cd -- "$HERE/../../.." && pwd)"
SRC="$HOME/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
OUT="$HOME/OpenFOAM/C3D05_B_C14_FUNCIONES_C14_COMPLETAS_10S_01"
ORIGINAL="$REPO/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
TOP="$REPO/analysis_tools/topSurfaceFlowPostProcessing"
LOG="log.foamMultiRun.C14_FULL_FUNCTIONS_10S"

if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--post-only" ) ]]; then
  printf 'Uso: bash %s [--post-only]\n' "$0" >&2
  exit 2
fi
POST_ONLY=false
if [[ $# -eq 1 ]]; then POST_ONLY=true; fi

# Serialize cooperating invocations (solver and post-only) outside the CFD.
# Reject aliases before resolving paths; do not write through symlinks.
[[ ! -L "$SRC" && ! -L "$OUT" ]] || { echo "Origen/salida enlazados." >&2; exit 2; }
SRC="$(realpath -m -- "$SRC")"
OUT="$(realpath -m -- "$OUT")"
if [[ "$SRC" == "$OUT" || "$SRC" == "$OUT/"* || "$OUT" == "$SRC/"* ]]; then
  echo "Origen y salida se solapan." >&2; exit 2
fi
command -v flock >/dev/null || { echo "Falta flock; no ejecutar." >&2; exit 2; }
LOCK="$OUT.UVA.lock"
[[ ! -L "$LOCK" ]] || { echo "Lock enlazado." >&2; exit 2; }
exec 9>>"$LOCK"
flock -n 9 || { echo "Otra ejecucion posee el lock: $LOCK" >&2; exit 3; }
if [[ "$POST_ONLY" == true ]]; then
  [[ -d "$OUT" && ! -L "$OUT" ]] || { echo "Salida no disponible." >&2; exit 2; }
  output_link="$(find "$OUT" -type l -print -quit)"
  [[ -z "$output_link" ]] || { echo "Salida contiene enlace: $output_link" >&2; exit 2; }
fi

# Foundation14 native function objects load directly from system/functions.
if [[ "$POST_ONLY" == false ]]; then
  if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "La nueva corrida ya existe: $OUT; NO repetir ni sobreescribir." >&2
    echo "Para postprocesar un CFD nuevo ya COMPLETO: bash $0 --post-only" >&2
    exit 3
  fi
  [[ -d "$SRC" && ! -L "$SRC" ]] || {
    echo "No existe la simulacion original C14-B: $SRC" >&2; exit 2; }
  [[ -f "$SRC/10/metal/T" && -f "$SRC/10/mold/T" ]] || {
    echo "No existen campos originales hasta t=10s." >&2; exit 2; }
  [[ -f "$SRC/0/metal/T" && -f "$SRC/0/mold/T" ]] || {
    echo "No existe el tiempo inicial real del CFD original." >&2; exit 2; }
  [[ -f "$SRC/constant/metal/polyMesh/points" &&
     -f "$SRC/constant/mold/polyMesh/points" ]] || {
    echo "No hay malla metal/arena original." >&2; exit 2; }
  cmp -s "$SRC/system/controlDict" "$ORIGINAL/system/controlDict" || {
    echo "controlDict Caso B y C14 original NO son identicos; nada se lanza." >&2; exit 2; }
  for file in functions researchDiagnostics lineProfiles momentumPostProcessing; do
    [[ -f "$ORIGINAL/system/$file" ]] || {
      echo "Falta diccionario C14: $file" >&2; exit 2; }
  done
  [[ -f "$TOP" ]] || { echo "Falta topSurfaceFlow C14 original." >&2; exit 2; }
fi

if [[ "$(printenv WM_PROJECT_VERSION || true)" != "14" ]]; then
  if [[ ! -f /opt/openfoam14/etc/bashrc ]]; then
    echo "Activa OpenFOAM Foundation 14 antes de ejecutar." >&2
    exit 2
  fi
  set +u
  source /opt/openfoam14/etc/bashrc
  set -u
fi
[[ "$(printenv WM_PROJECT_VERSION || true)" == "14" ]] || {
  echo "Es obligatorio OpenFOAM Foundation14." >&2; exit 2; }
for tool in foamMultiRun foamPostProcess foamLog; do
  command -v "$tool" >/dev/null || {
    echo "No esta disponible el comando Foundation14: $tool" >&2; exit 2; }
done

if [[ "$POST_ONLY" == false ]]; then
  # Reject source symlinks before copying because a solver must NEVER
  # write through one back into the original completed 3D CFD.
  source_link="$(find "$SRC/0" "$SRC/constant" "$SRC/system" -type l -print -quit)"
  if [[ -n "$source_link" ]]; then
    echo "Fuente CFD con enlace; no arriesgar escritura sobre original: $source_link" >&2
    exit 2
  fi
  # Only the 0, constant and system directories are copied. In particular,
  # the original 101 solved time steps and original postProcessing are
  # NEVER copied/altered/deleted. All F14 inputs in the new case are physical
  # copies; never symlinks to writable CFD input.
  mkdir -p "$HOME/OpenFOAM"
  STAGE="$(mktemp -d "$HOME/OpenFOAM/.C3D05_B_C14_FULL_FOS_STAGE_XXXXXXXX")"
  echo "Creando corrida nueva separada: $OUT"
  cp -a "$SRC/0" "$STAGE/0"
  cp -a "$SRC/constant" "$STAGE/constant"
  cp -a "$SRC/system" "$STAGE/system"
  # Literal C14 postprocessing dictionaries, same names/timing/sample sites.
  # From OpenFOAM F14, separate system/functions is loaded by foamMultiRun.
  for file in functions researchDiagnostics lineProfiles momentumPostProcessing; do
    cp "$ORIGINAL/system/$file" "$STAGE/system/$file"
    cmp -s "$STAGE/system/$file" "$ORIGINAL/system/$file" || {
      echo "Copia literal C14 fallo: $file" >&2; exit 2; }
  done
  cp "$TOP" "$STAGE/system/topSurfaceFlowPostProcessing"
  cmp -s "$SRC/system/controlDict" "$STAGE/system/controlDict" || {
    echo "Se altero controlDict. No ejecutar." >&2; exit 2; }
  (
    cd "$STAGE"
    sha256sum system/controlDict system/functions \
      system/researchDiagnostics system/lineProfiles \
      system/momentumPostProcessing system/topSurfaceFlowPostProcessing \
      constant/metal/polyMesh/points constant/mold/polyMesh/points \
      > PROVENIENCIA_ENTRADAS_C14_SHA256.txt
  )
  cat > "$STAGE/LEEME_EJECUCION_C14.txt" <<EOF
Caso B C3D05. NUEVA solucion 3D, desde t=0 hasta 10s.
C14 2D original: controlDict, functions, researchDiagnostics,
lineProfiles y momentumPostProcessing copiados byte-identicos.
Geometria REAL original: Caso B STEP/Gmsh HEX8 ya mallado.
No se ejecuta blockMesh ni splitMeshRegions.
CFD anterior NO se toca: $SRC
Los probes/perfiles conservan EXACTAMENTE sus coordenadas 2D C14;
si esas coordenadas no intersectan la malla 3D-B, OpenFOAM puede
marcarlas como no disponibles (se ve en el log, no se inventan).
EOF
  if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "Otro proceso creo el destino; etapa preservada: $STAGE" >&2
    exit 3
  fi
  mv -T --no-clobber "$STAGE" "$OUT"
  [[ ! -e "$STAGE" ]] || { echo "Destino ocupado; etapa preservada: $STAGE" >&2; exit 3; }
  echo "LANZANDO foamMultiRun 0..10s; dt=0.001; guardado cada 100 pasos."
  echo "La sonda temperatureProbe original escribe cada 1 paso (0.001s)."
  echo "Log: $OUT/$LOG"
  (
    cd "$OUT"
    set -o pipefail
    foamMultiRun -case "$OUT" 2>&1 | tee "$LOG"
  )
  [[ -f "$OUT/10/metal/T" && -f "$OUT/10/mold/T" ]] || {
    echo "No se encontro solucion completa a 10s; revisar log." >&2; exit 4; }
  [[ -d "$OUT/postProcessing" ]] || {
    echo "No hay postProcessing runtime: comprobar que Foundation14 leyo system/functions." >&2
    exit 4
  }
fi

[[ -f "$OUT/10/metal/T" && -f "$OUT/10/mold/T" && -f "$OUT/$LOG" ]] || {
  echo "La nueva corrida no tiene t10 ni log. No postprocesar." >&2
  exit 4
}
grep -Eq '^[[:space:]]*Time[[:space:]]*=[[:space:]]*10([.]0+)?s[[:space:]]*$' "$OUT/$LOG" || {
  echo "Falta Time = 10s en log nuevo; no postprocesar." >&2
  exit 4
}
grep -Eq '^[[:space:]]*End[[:space:]]*$' "$OUT/$LOG" || {
  echo "Falta End del solver nuevo; no postprocesar." >&2
  exit 4
}
cd "$OUT"

post_once() {
  local logfile="$1"; shift
  if [[ -f "$logfile.DONE" ]]; then
    [[ -s "$logfile" ]] || { echo "Marca DONE sin log: $logfile" >&2; return 4; }
    echo "Etapa completada: $logfile"
    return 0
  fi
  if [[ -e "$logfile" ]]; then
    local preserved
    preserved="$(mktemp -- "$logfile.INCOMPLETE_XXXXXXXX")"
    mv -- "$logfile" "$preserved"
  fi
  "$@" 2>&1 | tee "$logfile"
  touch "$logfile.DONE"
}

post_once log.foamPostProcess.C14.momentum \
  foamPostProcess -case "$OUT" -region metal \
    -dict "$OUT/system/momentumPostProcessing" -time '0:' \
    -fields '(phaseChangeSolidFraction phaseChangeDarcyCoeff phaseChangeModelDeltaT phaseChangeDarcyAcceleration phaseChangeBuoyancyAcceleration pRghAcceleration magPhaseChangeDarcyAcceleration magPhaseChangeBuoyancyAcceleration magPRghAcceleration phaseChangeDragToBuoyancy phaseChangeDragToPressure)'
post_once log.foamLog.C14 foamLog "$LOG"
post_once log.foamPostProcess.C14.topSurfaceFlow \
  foamPostProcess -case "$OUT" -region metal \
    -dict "$OUT/system/topSurfaceFlowPostProcessing" -time '0:' \
    -fields '(U T p_rgh rho phi phaseChangeSource:alpha1)'
touch "$OUT/C3D05_B_C14_FUNCIONES_COMPLETAS.foam"
printf '\n%s\n' \
  "TERMINADO: nueva corrida C14 con posprocesamiento original" \
  "Directorio: $OUT" \
  "ParaView: paraview --data=$OUT/C3D05_B_C14_FUNCIONES_COMPLETAS.foam" \
  "Caso B 10s original preservado: $SRC"
