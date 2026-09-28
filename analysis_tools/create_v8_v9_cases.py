#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"

CASES = {
    "B8_adaptiveOuter4": {"source": "B6_adaptiveDt", "kind": "adaptive_outer4"},
    "C8_adaptiveOuter4": {"source": "C6_adaptiveDt", "kind": "adaptive_outer4"},
    "B9_topFixedFlux": {"source": "B5_outer3", "kind": "top_fixed_flux"},
    "C9_topFixedFlux": {"source": "C5_outer3", "kind": "top_fixed_flux"},
}

COPY_ITEMS = ("0", "constant", "system", "Allrun", "Allclean")

def replace_once(text, pattern, repl, desc):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if n != 1:
        raise RuntimeError("%s: expected 1 replacement, got %d" % (desc, n))
    return out

def add_top_phi_diagnostic(path):
    text = path.read_text()
    if "metalTopPhiSum" in text:
        return

    marker = "// Net power [W] across the exposed metal surface."
    insert = """
// Net solver flux through metalTop.
// For these static-mesh compressible cases phi is used as the direct
// impermeability diagnostic. A physically impermeable slip top should
// integrate to approximately zero.
metalTopPhiSum
{
    type            surfaceFieldValue;
    libs            ("libfieldFunctionObjects.so");
    region          metal;

    log             true;
    executeControl  writeTime;
    executeInterval 1;
    writeControl    writeTime;
    writeInterval   1;

    writeFields     false;
    surfaceFormat   none;
    patch           metalTop;
    operation       sum;

    fields
    (
        phi
    );
}

"""
    if marker not in text:
        raise RuntimeError("Could not locate energy diagnostic insertion point in %s" % path)
    path.write_text(text.replace(marker, insert + marker, 1))

def prepare_case(name, spec):
    source = BASE / spec["source"]
    dest = BASE / name

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for item in COPY_ITEMS:
        src = source / item
        dst = dest / item
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.is_file():
            shutil.copy2(src, dst)
        else:
            raise RuntimeError("Missing required source item: %s" % src)

    if spec["kind"] == "adaptive_outer4":
        fv = dest / "system" / "fvSolution"
        text = fv.read_text()
        text = replace_once(
            text,
            r"(nOuterCorrectors\s+)3(\s*;)",
            r"\g<1>4\g<2>",
            "%s: nOuterCorrectors" % name,
        )
        fv.write_text(text)

    elif spec["kind"] == "top_fixed_flux":
        prgh = dest / "0" / "metal" / "p_rgh"
        text = prgh.read_text()
        block_pattern = (
            r"(metalTop\s*\{\s*)"
            r"type\s+totalPressure\s*;\s*"
            r"p0\s+uniform\s+1e5\s*;\s*"
            r"value\s+uniform\s+1e5\s*;"
            r"(\s*\})"
        )
        replacement = (
            r"\1"
            "type            fixedFluxPressure;\n"
            "        value           $internalField;"
            r"\2"
        )
        text = replace_once(
            text,
            block_pattern,
            replacement,
            "%s: metalTop p_rgh" % name,
        )
        prgh.write_text(text)
        add_top_phi_diagnostic(dest / "system" / "researchDiagnostics")
    else:
        raise RuntimeError(spec["kind"])

    note = dest / "CASE_VARIANT.md"
    if spec["kind"] == "adaptive_outer4":
        note.write_text(
            "# %s\n\nParent case: `%s`.\n\n"
            "Controlled change: root-level `system/fvSolution` "
            "`nOuterCorrectors` changed from 3 to 4.\n\n"
            "Purpose: test whether the V6 adaptive-timestep flow differences are "
            "caused by insufficient outer PIMPLE coupling rather than timestep size itself.\n\n"
            "Everything else is inherited unchanged from the parent input case. "
            "No calculated results from the parent were copied.\n"
            % (name, spec["source"])
        )
    else:
        note.write_text(
            "# %s\n\nParent case: `%s`.\n\n"
            "Controlled change: `0/metal/p_rgh` on `metalTop` changed from "
            "`totalPressure` to `fixedFluxPressure`, while `U=slip` and the "
            "thermal boundary condition remain unchanged.\n\n"
            "Purpose: test whether the previous non-zero top advective-energy flux "
            "and B/C circulation differences are influenced by pressure/flux "
            "inconsistency at the impermeable top wall.\n\n"
            "A `metalTopPhiSum` function object was added to `system/researchDiagnostics` "
            "to verify the solver flux directly.\n\n"
            "Everything else is inherited unchanged from the parent input case. "
            "No calculated results from the parent were copied.\n"
            % (name, spec["source"])
        )

for name, spec in CASES.items():
    prepare_case(name, spec)

(BASE / "README_V8_V9_TESTS.md").write_text("""# V8/V9 controlled diagnostic matrix

These cases are deliberately orthogonal tests. Historical B3-B7/C3-C7 cases are unchanged.

| Case | Parent | Single controlled change | Question |
|---|---|---|---|
| B8_adaptiveOuter4 | B6_adaptiveDt | nOuterCorrectors 3 -> 4 | Does extra PIMPLE coupling recover B6 flow? |
| C8_adaptiveOuter4 | C6_adaptiveDt | nOuterCorrectors 3 -> 4 | Does extra PIMPLE coupling materially change C6? |
| B9_topFixedFlux | B5_outer3 | metalTop p_rgh totalPressure -> fixedFluxPressure | Does enforcing flux consistency remove B top advective leakage / alter circulation? |
| C9_topFixedFlux | C5_outer3 | metalTop p_rgh totalPressure -> fixedFluxPressure | Control counterpart for C |

## Interpretation

V8 isolates outer-coupling count while retaining the adaptive timestep.
V9 isolates the top pressure boundary while retaining fixed timestep and V5 coupling.

Do not compare V8 vs V9 as if they differed by one variable; they answer different questions.
""")

run = BASE / "run_v8_v9_tests.sh"
run.write_text("""#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cases="
B8_adaptiveOuter4
C8_adaptiveOuter4
B9_topFixedFlux
C9_topFixedFlux
"

for c in $cases
do
    echo "============================================================"
    echo "Running $c"
    echo "============================================================"
    (
        cd "$c"
        ./Allrun
    )
done
""")
run.chmod(0o755)

print("Prepared:", ", ".join(CASES))
