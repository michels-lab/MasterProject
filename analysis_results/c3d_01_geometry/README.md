# C3D-01 — Puerta de geometría y malla preliminar

**Etapa:** CAD+STL verificados preliminarmente; `blockMesh`, `snappyHexMesh`, `splitMeshRegions` y `checkMesh` no ejecutados aquí. **Sin CFD.**

## Qué se verificó de los archivos individuales del investigador

- `QuickCup.STEP` y `metal.STEP` son un sólido válido cada uno mediante OCC; intersección volumétrica CAD = 0 y distancia entre sólidos = 0 (contacto).
- La geometría del metal no fue reconstruida: corresponde al volumen de la cavidad obtenido con la herramienta CAD del investigador.
- Se trianguló cada sólido por separado. Metal: **2252 triángulos**, volumen STL ≈ **47.9874 cm³**; arena: **2668 triángulos**, volumen STL ≈ **102.8435 cm³**.
- Ambas superficies resultaron cerradas, con aristas de dos incidencias y orientación consistente. El preflight nuevo determinó los puntos interiores: metal `(0.0259 -0.02 0.0259)`, arena `(0.003 -0.02 0.0259)` en metros.
- **Advertencia metrológica:** la conversión STEP→STL usó de forma provisional la interpretación de un molde de **51.8 × 65.5 × 51.8 mm** y metal de **36.5 × 40 × 36.5 mm**, pese a que el STEP indica unidades metro y trae coordenadas con valores ~51.8. **Confirmar escala con medida CAD/física independiente antes de cualquier resultado publicable.**
- Referencia verificable, SHA-256 y manifiesto: [reference_geometry.json](reference_geometry.json).

## Política de evidencias y privacidad

No se añaden los archivos originales STEP/SLDPRT, STL ni el ensamble al repositorio público. El paquete CAD/STL permanece como entrega local del investigador. El manifiesto guarda solo cotas/volúmenes/hashes y puntos de región que permiten reconocer una exportación alterada. No modificar ni volver a ejecutar las referencias 2D B14/C14.

El preflight reproducible está en `analysis_tools/preflight_c3d_stl.py`. Se verificó contra los STL reales en un entorno Python con resultado **PASS_PRELIMINARY_STL_ONLY** y cuatro pruebas sintéticas independientes. Esta etiqueta **no certifica** OpenFOAM, una interfaz térmica ni una simulación.

## Próximo paso: Ubuntu + OpenFOAM Foundation v14

El ZIP local `QuickCup_C3D_01_geometria_validada_preliminar.zip` contiene `QuickCup_C3D_geometry/` con `constant/triSurface/{metal,mold}.stl`, `system/{blockMeshDict,snappyHexMeshDict}`, el manifiesto y `scripts/mesh_only.sh`. Descomprimir en una carpeta nueva y sin archivos de malla anteriores.

```bash
mkdir -p ~/OpenFOAM/C3D_01_mesh_trial_01
cd ~/OpenFOAM/C3D_01_mesh_trial_01
unzip ~/Descargas/QuickCup_C3D_01_geometria_validada_preliminar.zip
cd QuickCup_C3D_geometry
source /opt/openfoam14/etc/bashrc
python3 scripts/preflight_c3d_stl.py --stl-dir constant/triSurface --manifest geometry_audit.json
bash scripts/mesh_only.sh
```

La ruta ZIP es orientativa: ajustarla al directorio de descarga real. Cada intento debe extraerse en un directorio nuevo y vacío, nunca encima de una malla anterior. **No** ejecutar `Allclean`/`Allrun` de C14. El script es **solo malla**; aborta si existe una malla previa y no llama al solver CFD. El diccionario `snappyHexMeshDict` es un **borrador no probado en Foundation 14**: revisar especialmente la conservación de ambas zonas y la compatibilidad de `locationsInMesh` y `splitMeshRegions`.

Guardar y revisar:
`log.preflight_c3d.json`, `log.surfaceCheck.mold`, `log.surfaceCheck.metal`, `log.blockMesh`, `log.snappyHexMesh`, `log.checkMesh.preSplit`, `log.splitMeshRegions`, `log.checkMesh.metal`, `log.checkMesh.mold`.

## Puerta de aceptación de mallado (NO CUMPLIDA)

1. Ambas regiones de volumen existen y sus volúmenes mallados son físicamente plausibles frente al CAD y a las pérdidas de triangulación; ninguna región queda omitida o conectada a exterior por error.
2. `checkMesh` sin fallos topológicos/geométricos graves en ambas regiones; evaluar skewness, non-orthogonality, volumen mínimo y patches.
3. Establecer y auditar correspondencia de interfaz metal–molde: áreas, superficies, normales, patch pairs y método real de acoplamiento térmico. Un STL watertight o `checkMesh` PASS **no es prueba de acoplamiento CHT**.
4. Identificar pared exterior, fondo, interfaz y `metalTop`; quitar `empty` 2D solo al sustituirlo por patches físicos 3D.
5. Verificar gravedad, referencia de presión, temperaturas iniciales, propiedades, condiciones ambientales, posición medida del termopar y continuidad energética. Las entradas de C14 son referencia conceptual pero no un `Allrun` intercambiable con C3D.
6. Solo con evidencia de malla y BC adecuadas, ejecutar CFD **en laptop del investigador**, subir logs y efectuar balances/validación en GitHub con análisis de solo lectura.

## Arquitectura científica

- **C3D-01**: adaptación geométrica multirregión desde línea **C14**, densidad constante + flotación explícita, metal completamente lleno. No implica que C16 sustituya automáticamente al baseline.
- **B-FS/B-SH**: línea independiente con superficie metal–aire, alimentación/contracción que requiere nueva física; no confundir con una frontera `slip` de la rama C.
- J0 (propiedades JMatPro) y G1 (curvas experimentales) siguen abiertas. La recalescencia no se establece por un rebote de temperatura aislado.
