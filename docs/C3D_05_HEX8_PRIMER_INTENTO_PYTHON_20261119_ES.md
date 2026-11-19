# Caso B C3D-05 — Primer intento HEX8, error Python y corrección verificada en fuente

**Fecha del registro:** 18–19 noviembre 2026. **Evidencia primaria:** salida real de terminal WSL compartida por el investigador después de ejecutar `run_hex_subdivision_pilot.sh`. Se conserva la distinción entre capacidad del Gmsh de malla HEX8 y la ejecución real QuickCup, que **no llegó a iniciar correctamente**. **NO CFD**.

## Resultados del primer piloto `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01`

El orquestador sincronizó `MasterProject/main` a `8736a58c1`; pasaron las pruebas estáticas + 4 pruebas del postmortem + 2 pruebas de conectividad sintética.

**La prueba independiente de capacidad sí pasó**, con el mensaje nativo:

```text
HEX_SUBDIVISION_PREFLIGHT_OK: two OCC materials, common shared QUAD4 contact,
3092 HEX8 cells, physical regions 101/102 preserved;
memory-only test, NOT QuickCup quality approval
```

Esta prueba confirma que la instalación Python/Gmsh puede realizar la conversión de una **geometría de prueba en memoria** con dos sólidos y una interfaz compartida. **No significa que el CAD de QuickCup haya pasado su malla HEX8.**

Al iniciar la lectura real de `metalmm.STEP`, el script `build_step_mesh.py` abortó **antes de importar los sólidos STEP**:

```text
UnboundLocalError: cannot access local variable 'volume_tags'
where it is not associated with a value
  at metal_import = volume_tags(gmsh.model.occ.importShapes(str(metal_path)), "metal")
REJECTED / stage=gmsh3d / NO_CFD
Preserved: /home/michel/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01
```

**Causa reproducible identificada en fuente:** `build_step_mesh.py` declaró la función global `volume_tags(entities, source)` para identificar un sólido y más tarde asignó `volume_types, volume_tags, _ = gmsh.model.mesh.getElements(3)` dentro de `main()`. Python considera `volume_tags` un nombre local de toda `main()`, así que la primera invocación falla con `UnboundLocalError`. **No era error de STEP, de OpenCASCADE, de recursos RAM, de la malla HEX8 ni de `gmshToFoam`**: estos últimos pasos nunca se intentaron en esta corrida real.

## Reparación de código subida a GitHub

- Se reemplazó solamente la variable local conflictiva por `hex_element_tags`. **Se conservó la función global `volume_tags`**, las referencias CAD, el algoritmo de malla y las puertas nativas `checkMesh`.
- Se añadió `tests/test_build_step_mesh_regressions.py` que revisa la tabla de símbolos `symtable` de `main()` para detectar que `volume_tags`, `sha256` y `relative_error` son funciones globales no ensombrecidas por asignaciones locales; también comprueba el comportamiento de `volume_tags` sobre entidades 3D válidas e inválidas. Se ejecuta **antes de invocar Gmsh**; se integró en `test_step_gmsh_static.sh` y en el orquestador.
- Se actualizó **`scripts/run_hex_subdivision_pilot.sh`** para conservar la carpeta histórica `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01` **sin borrarla ni sobrescribirla**; exige que el log anterior contenga la evidencia `UnboundLocalError / volume_tags` y crea el ensayo reparado en la carpeta nueva **`~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`**. El resto del protocolo sigue: CAD original AP214 SHA256, preflight 2-volúmenes, prueba inicial tetra a 3.6 mm, tope 150,000 tetra, subdivisión a HEX8/QUAD4, `gmshToFoam`, separación de regiones, `checkMesh` padre/metal/arena y auditoría de contacto sin CFD.
- **El ensayo corregido `_02` está PREPARADO pero aún NO ejecutado en WSL**. Ningún `Mesh OK` se afirma ni se prevén conteos de hexaedros para el QuickCup.

**Un único comando para el investigador**, coherente con la regla permanente:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh
```

**Criterios:** éxito de importación del CAD, generación de HEX8/QUAD4, volumen CAD correcto, `Mesh OK` padre/metal/arena sin bajar umbrales, `mappedWall` recíprocos e iguales áreas de contacto. Si el nuevo piloto `_02` falla en otro punto, **conservar ambos intentos HEX** y analizar la causa exacta antes de crear otro experimento.

[Reporte HXT y fundamento del piloto HEX8](C3D_05_HXT_RESULTADO_Y_PILOTO_HEX_20261118_ES.md) · [Regla de un solo comando](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
