# Caso B / C3D-05 — Operación Granada: compilación nativa del extractor térmico con Foundation14

**20 de noviembre de 2026 · Etapa 3/7, 2/7 hitos técnicos (29 %), NO porcentaje de tesis.**

## Avance real respecto a la CI sintética

Se incorporó un nuevo [workflow de GitHub Actions](../../.github/workflows/c3d05-foundation14-native-build.yml), independiente de la CI Python/Bash, que instala **OpenFOAM Foundation 14 auténtico en Ubuntu 24.04** (paquete oficial `openfoam14`), copia el código nativo fuera del árbol versionado y llama `wmake`. Después verifica la presencia del ejecutable, dependencias dinámicas mediante `ldd` y arranque `-help`.

El objetivo es confirmar **API C++/compilación/enlace en una instalación real**, no ejecutar `foamMultiRun`, Gmsh, checkMesh, la malla de 270,788 elementos ni el proyecto experimental. Es complementario al flujo WSL que sigue siendo responsable de ejecutar las verdaderas mallas y condiciones del investigador.

## Fallos descubiertos por compilador real y corregidos en origen

1. CI inicial [`44828002104`](https://github.com/michels-lab/MasterProject/actions/runs/44828002104): `fvCFD.H: No such file or directory`. Se sustituyó la inclusión paraguas heredada por encabezados propios y disponibles de Foundation14: `fvMesh.H`, `surfaceFields.H`, `Time.H`, `argList.H` y las interfaces termofísicas existentes.
2. CI [`44828287798`](https://github.com/michels-lab/MasterProject/actions/runs/44828287798): `fvMesh` no implementa `boundaryMesh()`; se usa `mesh.poly().boundary()`. Asimismo se evita comparar estados de lectura `fvMesh` con el enum de `polyMesh`.
3. CI [`44828528231`](https://github.com/michels-lab/MasterProject/actions/runs/44828528231): `polyBoundaryMesh` no tiene `findPatchID`; el [código fuente oficial](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/OpenFOAM/meshes/polyMesh/polyBoundaryMesh/polyBoundaryMesh.H) define `findIndex(const word&)`. Se corrigió el extractor y fijó la API en [regresiones](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_patch_flux.py).

Las observaciones anteriores demuestran que **las CI anteriores, que solo ejecutaban Python/Bash y pruebas sintéticas, eran insuficientes para certificar compilación nativa**. No se sustituyó el código de C14 ni se tocó la malla aceptada.

## Aislamiento y conservación de evidencia

Se mejoró también [`run_native_t0_patch_flux.sh`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh): el código C++ se compila en una copia de la carpeta aislada del caso, y solo tras obtener y validar ambos CSV (12,636 caras por lado) publica de forma transaccional un directorio `T0_NATIVE_FACE_FLUX` con `metal.csv`, `mold.csv`, `bilateral_diagnostics.json`, `log.c3d05PatchFlux` y `manifest.sha256`. No presenta archivos parciales como resultados. La reentrada no recompila ni reejecuta si el paquete existente coincide y los SHA son válidos. Un fallo conserva su carpeta temporal para diagnóstico, sin reabrir los 270,788 HEX8 aceptados.

Se añadió [`test_native_flux_atomic_handoff.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_native_flux_atomic_handoff.py), una regresión **end-to-end sintética**, que genera las 12,636 parejas con orden de caras intercambiado, prueba publicación/reutilización sin modificación, caída tras CSV parcial y preservación de un paquete previo. CI estática: [`44828225904` aprobada](https://github.com/michels-lab/MasterProject/actions/runs/44828225904).

**Límites:** ninguna prueba compila la aplicación en la WSL personal del investigador, ejecuta el solver en la malla real, mide el q real del contacto, confirma conservación energética ni valida termopares o JMatPro. Esas pruebas requieren la corrida nativa. **G3/G4 siguen pendientes; avance 2/7 = 29 % hitos técnicos.**

## Resultado de compilación

Se deberá registrar aquí la primera ejecución **PASS** que demuestre `wmake`, `ldd` y `-help` con Foundation14. Hasta entonces la compilación es `EN_VERIFICACION`; que el código esté publicado no equivale a compilado.
