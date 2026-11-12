# Geometría SolidWorks C3D-02

**No se generan ni alteran los STL con código.** Se copia una vez desde la referencia CAD verificada, y después se audita con `sha256sum` y `surfaceCheck`.

| Archivo | Función | SHA-256 histórico |
|---|---|---|
| `metal.stl` | hierro original, malla de interfaz | `fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810` |
| `mold.stl` | molde original de SolidWorks, archivo de trazabilidad, **superficie abierta** | `2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638` |
| `mold_repaired.stl` | molde cerrado para meshing | `860525e8a9fb2de483cf90f331f2753a339d82c5eee706ecfc1b8186bf49e9fe` |

**Aún no están dentro de esta nueva carpeta de GitHub.** Ejecutar `scripts/prepare_geometry.sh` **antes de borrar el caso histórico**, revisar hashes y versionar las copias expresamente. El código de preparación es independiente de las carpetas anteriores **una vez hecha esta copia**.

No confundir STL con unidades: CAD originales en mm; `blockMeshDict` usa `units [mm];`; una futura configuración `snappyHexMesh` debe definir las unidades correctas una sola vez. No inferir que `surfaceCheck` cerrado = malla 3D validada.
