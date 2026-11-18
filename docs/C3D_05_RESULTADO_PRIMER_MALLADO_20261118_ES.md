> **POSTMORTEM ACTUALIZADO 18-11-2026:** la causa que este documento histórico marca como «pendiente» **YA fue identificada** por los logs de WSL: **un solo check fallido por determinante <0.001** (306 celdas en malla padre, 96 metal, 402 arena tras split), con ortogonalidad, skewness, conectividad y volumen aprobados. La distribución espacial/topológica y el área de contacto aún **NO** se han estudiado; no bajar umbral ni relanzar Gmsh. [Diagnóstico y protocolo siguiente](C3D_05_DIAGNOSTICO_DETERMINANTE_20261118_ES.md).

# C3D-05 — Primera ejecución nativa Gmsh/OF14 con STEP auténticos (18-11-2026)

**Fuente de evidencia:** salida de terminal WSL proporcionada por el investigador. Se respeta la distinción entre los resultados mostrados y el contenido de los logs **que todavía no se ha compartido**. Este documento no dice que la malla fue aceptada.

## Ejecución realmente observada

El investigador ejecutó:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_05_step_gmsh_conformal/Allmesh
```

El repositorio se sincronizó hasta `main=79056bbce` y `Allmesh` avanzó por lectura y mallado STEP con Gmsh, conversión `gmshToFoam`, `splitMeshRegions` y análisis de malla con `checkMesh`. La etapa final fue **`REJECTED / stage=CHECK_REGION_QUALITY`**. Por el script de ejecución, el resultado confirma que se produjo malla y se separó en dos regiones; no confirma que los parches térmicos sean aún aceptables, pues la etapa de auditoría de interfaz no se alcanzó.

```text
region  cells   volume_m3         CAD_m3        mesh_ok
metal   190365  4.79675605036e-05 4.7987697e-05 NO
mold    335341  0.000102843547305 1.02843333e-04 NO
REJECTED / stage=CHECK_REGION_QUALITY / Native mesh quality, connectivity or physical volume gate failed / NO_CFD
Preserved: /home/michel/OpenFOAM/C3D05_STEP_GMSH_PILOT_01
```

| Parámetro | Metal | Arena |
|---|---:|---:|
| Celdas nativas | **190,365** | **335,341** |
| Volumen nativo [m³] | 4.79675605036e-05 | 1.02843547305e-04 |
| Volumen referencia [m³] | 4.7987697e-05 | 1.02843333e-04 |
| Error volumen aproximado | **−0.04196 %** | **+0.000208 %** |
| `mesh_ok` del runner | **NO** | **NO** |
| Naturaleza exacta de los checks fallidos | **PENDIENTE DE LEER LOG** | **PENDIENTE DE LEER LOG** |

**Total = 525,706 celdas.** Ambas desviaciones volumétricas son **menores a 2 %**, por lo que este umbral de volumen no explica por sí mismo el `mesh_ok NO`. Pero las otras condiciones del runner pueden fallar: `Mesh OK` ausente, cantidad de componentes `Number of regions` distinta de 1, resultado no cero de `checkMesh` o defectos geométricos/topológicos. **No afirmar** que hay celdas cóncavas, skewness, nonorthogonality o desconexiones **sin inspeccionar `log.checkMesh.metal` y `log.checkMesh.mold`**.

La ejecución pasó la etapa `run_stage checkMesh.parent` sin que el comando terminara con error; su criterio de `Mesh OK` debe igualmente comprobarse en su log. La etapa de auditoría de `mappedWall`, `CONTACT_AREA_REPORT.json` y la física CFD **NO se completó**.

## Evidencia y diagnóstico sin remallar

**Ubicación local PRESERVADA**:
`/home/michel/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`

**No borrar, no volver a generar la misma malla, no reducir los estándares de `checkMesh`.** Para conocer la razón exacta sin repetir Gmsh ni OpenFOAM, sincronizar `main` e inspeccionar los archivos existentes mediante el nuevo diagnóstico de solo lectura:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
python3 -m unittest discover -s cases_3d/C3D_05_step_gmsh_conformal/tests -p 'test_diagnose_existing_mesh.py' -v
python3 cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py \
  ~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01
```

El script reporta separadamente los predicados exactos del `Allmesh` original: celda positiva, volumen en ±2 %, cantidad de componentes, línea `Mesh OK`, checks fallidos y líneas importantes del log. También lee, sin modificarlas, las declaraciones de los parches existentes y la presencia de reportes. Está prohibido etiquetar como `MESH_OK` una salida que reportó `mesh_ok NO`.

## Decisión académica

La ruta alternativa C3D-05 **es viable para generar y separar dos materiales desde los STEP auténticos**; queda **RECHAZADA POR LA PUERTA NATIVA DE CALIDAD/CONEXIÓN PENDIENTE DE DIAGNÓSTICO ESPECÍFICO**. Se mantiene como ruta de mejora controlada, sin realizar ajustes de Gmsh a ciegas. En paralelo, C3D-03 conserva su aceptación preliminar de calidad, C3D-04 requiere la ejecución local de su piloto curvilíneo, y **NO hay CFD 3D ejecutado**.

Fuentes: [código C3D-05](../cases_3d/C3D_05_step_gmsh_conformal/Allmesh), [diagnóstico no destructivo](../cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py), [fuentes STEP B-Rep autenticadas](C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md), [avances de mallado](C3D_MESH_PROGRESS_20261118.csv).
