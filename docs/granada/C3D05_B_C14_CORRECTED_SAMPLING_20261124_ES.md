# Caso B — recuperación del muestreo C14 en coordenadas 3D (24-11-2026)

Etapa 3/7; 2/7=29% de hitos técnicos, sin cierre físico G3/G4/G5.

## Evidencia y causa
La publicación del investigador, commit [2257ac295](https://github.com/michels-lab/MasterProject/commit/2257ac295981c081391a23b318ee9f766bd32145), contiene 339 archivos. El postproceso anterior registró éxito de proceso pero las sondas T/U en (0.02 0.02 0.005) contienen el sentinel -1.79769e+307 y los perfiles horizontales/verticales tienen cero archivos. No usar esos resultados para análisis. La geometría CAD auditada (docs/C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md) tiene X/Z 7.65–44.15 mm y Y -40–0 mm. Se traslada el centro a (25.9,-20,25.9) mm; alturas relativas 10/20/30 mm corresponden a Y=-30/-20/-10 mm. Se conservan los 80 puntos solicitados y la longitud nominal C14 de 39.5 mm; las líneas pueden exceder el metal, no interpolar ni inventar valores fuera de dominio. La cobertura nativa efectiva sigue pendiente.

## Entrega
`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/recover_case_b_c14_sampling.py`: usa la copia offline existente, compara hashes de la malla metal y controlDict con el caso original, genera familias nuevas de objetos y conserva las antiguas. Recupera 17 perfiles y sonda para U,T,p_rgh,alpha1,vorticidad,flowType,gradT,magGradT a 101 estados; rho,gradRho,magGradRho,CoCell a 100 estados positivos. Verifica cadencia, centinelas finitos, cobertura, encabezados raw abreviados y genera encabezados explícitos, sin modificar valores. Los ejes son globales; diagonales usan proyección X. No equivale a promedio radial ni a derivadas de paso nativo. --publish crea rama de resultados descendiente del commit anterior desde worktree separado. --publish-only permite reintentar el push tras auditoría local exitosa.
 
```bash
B="$HOME/OpenFOAM/C3D05_B_WORKTREE"
source /opt/openfoam14/etc/bashrc
export HWLOC_COMPONENTS=-gl
git -C "$B" fetch origin &&
git -C "$B" merge --ff-only origin/main &&
python3 -B "$B/cases_3d/C3D_05_step_gmsh_conformal/c14_physics/recover_case_b_c14_sampling.py" --publish
```

Código publicado; regresiones incluidas y se ejecutan al inicio en WSL, no verificadas en este turno. No afirmar ejecución local, cobertura válida ni importación FoamLens hasta observar evidencia. No se repite CFD, no se reconstruye la malla, no se recuperan sondas de 1 ms ni fuentes nativas de momentum/latente. G3/G4/G5 pendientes.
