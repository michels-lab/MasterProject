# C14_3D_A_faithful — Caso A
Reference: C14_topFixedFlux_explicitRef (2D), transferred to accepted V4/T02
3D mesh, 8960 metal and 12352 mold cells. Native faithful run reached 10 s
(10000 steps, dt=.001, 101 saved states) with original controlDict and
researchDiagnostics, adapted sampling coordinates, 17 lines and 10001
samples per native probe variable. Preferred A scientific reference.

## Versioning
Same policy as the 2D cases: 0/, constant/, system/, postProcessing/, logs/,
raw solver logs and scientific evidence. Calculated volume directories
0.1..10, generated polyMesh, dynamicCode and ParaView marker stay in the
original WSL run unchanged. analysis_results/GIT_PUBLICATION_MANIFEST.json
records file hashes, mesh hashes and provenance. Import this folder in
FoamLens for spatial/temporal data; full 3D visualization needs local
native mesh and calculated fields. If available, the previous baseline
comparison with C14 2D is archived in analysis_results/previous_A_baseline_vs_C14_2D,
explicitly distinct from this new faithful run.

## Reproduction
Allrun uses the parent faithful runtime executor with accepted V4/T02 and
the validated local A baseline, creating a new out-of-tree run. The parent
geometry workflow (../README.md, ../AGENTS.md) documents the mesh provenance.
Allclean intentionally does not delete scientific evidence in this archive.

## Status
Native diagnostic parity confirmed in WSL. Discrete energy closure,
same-geometry mesh/time independence and QuickCup validation remain open.
