# FS-C08 — Primer paso conservativo nativo con Γ distinto de cero

## Qué se implementó

El ejecutable **fsC08NativeShadowStep.C** usa una **malla OpenFOAM Foundation14 real** mediante fvMesh, mesh.V(), mesh.owner() y mesh.neighbour(). Construye **masas iniciales sintéticas** de tres fases en todas las celdas, aplica un paso FV explícito en memoria de líquido, sólido y gas, con fuentes +Gamma/-Gamma y flujos de las tres fases sobre una cara interior real. El núcleo **ConservativePhaseNetwork.H** reutiliza el C++17 previamente validado ConservativePhaseExchange.H e invierte el balance entálpico incluyendo calor latente una sola vez.

**Estado al incorporarlo:** el núcleo C++17 con dos celdas, Gamma no nula, flujos de tres fases y entalpía **sí compiló y pasó en el contenedor Linux del asistente** con -std=c++17 -Wall -Wextra -Werror. El nuevo ejecutable OpenFOAM14 **todavía debe compilarse y ejecutarse en el WSL del investigador**, por lo que NO se proclama validación nativa WSL ni simulación real de contracción.

## Un solo comando para el siguiente paso en WSL

El worktree FS_C08_WORKTREE ya existe. Ejecuta exactamente:

    cd ~/OpenFOAM/FS_C08_WORKTREE && \
    git fetch origin research/fs-c08-conservative-phase-mass-20261123 && \
    git switch --detach FETCH_HEAD && \
    python3 -B analysis_tools/run_fs_c08_native_shadow.py \
      --case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4

Este comando es **diferente al puente anterior**. Usa el programa de malla real con fuentes no nulas, pero no modifica archivos del caso ni corre foamMultiRun. Todos los parámetros sintéticos están en SYNTHETIC_ONLY_NOT_JMATPRO.dict. El programa rechaza cualquier identificación material distinta de SYNTHETIC_ONLY_NOT_JMATPRO.

El ejecutor:
1. Verifica WM_PROJECT_VERSION=14, wmake, la fixture y SHA256 de los seis archivos nativos originales (campos de 0.2, 0.4 y 1 s).
2. Compila fsC08NativeShadowStep con wmake e inicia un paso nativo en la conectividad fvMesh de FS-C07, con masas sintéticas totalmente separadas del hierro real.
3. Comprueba en el stdout que Gamma(owner)>0, Gamma(neighbour)<0, que los flujos internos de las tres fases no sean cero, y que los residuos globales de metal, gas y entalpía se cierren.
4. Repite los seis SHA256, sin modificar los campos. Guarda logs y JSON en un subdirectorio nuevo de ~/OpenFOAM/FS_C08_DIAGNOSTICS.

PASS esperado: **FS_C08_NATIVE_GAMMA_FV_SHADOW_PASS__SYNTHETIC_NO_CFD**. Si falla wmake o las invariantes, se preserva el log y se informa el error concreto.

## Ecuaciones discretizadas

Cada fase k tiene una masa por celda m_k [kg]; cada cara interior conecta owner y neighbour, contribuyendo con el mismo flujo y signos exactamente opuestos. Para dt en segundos, Gamma en kg/(m3 s):

    m_l(new) = m_l(old) - dt*SUM(face_liquid_flow_out_kg_s) - Gamma*V*dt
    m_s(new) = m_s(old) - dt*SUM(face_solid_flow_out_kg_s)  + Gamma*V*dt
    m_g(new) = m_g(old) - dt*SUM(face_gas_flow_out_kg_s)

La entalpía H [J] se conserva con flujos internos del valor upstream de cada fase, y con calor externo opcional. Para la fixture actual el calor externo es cero y el calor por cara es un intercambio entre owner y neighbour, no una fuente global. La entalpía específica líquida incluye exactamente una vez el calor latente:

    h_l(T) = cp_l*(T-Tref) + L
    h_s(T) = cp_s*(T-Tref)
    h_g(T) = cp_g*(T-Tref)

El mismo transporte conservativo de fase permite recuperar algebraicamente T(new) sin agregar otra fuente artificial de Gamma*L. Se rechazan masa negativa, volumen metálico sobrellenado, temperatura no positiva, Gamma no finita, y conectividad inválida. El cambio de volumen reportado es V_metal(new)-V_metal(old), usando las densidades constantes SINTÉTICAS de la fixture.

## Lo que NO hace

- No alimenta las fracciones iniciales con campos reales de FS-C07 ni usa JMatPro o curvas experimentales del hierro hipoeutéctico; se usa solo la malla y conectividad real.
- No resuelve el sistema completo de transporte de caras, fvm::ddt, fvm::div, ecuación de momento, presión, VOF, CHT o superficie libre. Es un **paso explícito FV sobre una cara interna del mallado real**, no una integración de todo el VoFSolver.
- No incluye compresión/expansión termodinámica del gas, p*dV, cálculo termocinético de Gamma, expansión grafítica calibrada, alimentación, porosidad ni rechupe real.
- No permite interpretar cambio algebraico de volumen como contracción de la pieza ni como validación metalúrgica.

**Próximo hito:** después de verificar wmake de la nueva utilidad en WSL, reemplazar flujos prescritos por flujos CFD y Gamma por un cierre de solidificación calibrado, con masa, energía, presión e interfaz acopladas.
