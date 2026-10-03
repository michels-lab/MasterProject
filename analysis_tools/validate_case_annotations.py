#!/usr/bin/env python3
from pathlib import Path
import subprocess

MARKER = b"QUICKCUP DOCUMENTATION APPENDIX"
ROOTS = ("cases_controlled_buoyancy/", "cases_buoyancy/", "cleanproy/")

changed = subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
checked = 0
failures = []

for path in changed:
    if not path.startswith(ROOTS):
        continue
    old = subprocess.check_output(["git", "show", f"HEAD:{path}"])
    new = Path(path).read_bytes()

    if not new.startswith(old):
        failures.append((path, "el contenido original dejó de ser un prefijo byte-a-byte"))
        continue

    appended = new[len(old):]
    if MARKER not in appended:
        failures.append((path, "falta el marcador del apéndice documental"))
        continue

    try:
        extra = appended.decode("utf-8")
    except UnicodeDecodeError:
        failures.append((path, "el contenido añadido no es UTF-8"))
        continue

    for line in extra.splitlines():
        if line.strip() and not (
            line.lstrip().startswith("//")
            or line.lstrip().startswith("#")
        ):
            failures.append((path, f"línea añadida no comentada: {line[:80]}"))
            break
    else:
        checked += 1

if failures:
    raise SystemExit(f"Validación fallida: {failures[:10]}")

print(f"Validación OK: {checked} archivos conservan exactamente sus bytes originales y sólo agregan comentarios.")
