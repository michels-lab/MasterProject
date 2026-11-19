#!/usr/bin/env python3
"""Comprueba estado/bitácoras del proyecto sin ejecutar OpenFOAM ni modificar archivos."""
import argparse
import json
import pathlib
import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKER = "PROJECT_PROGRESS_CONTRACT_20261119"
CORE = [
"AGENTS.md","README.md","PROJECT_AUDIT_LOG.md","PROJECT_AUDIT_LOG_ES.md",
"PROJECT_AUDIT_LOG_EN.md","RUN_MASTER_PROTOCOL.md","NEXT_RESEARCH_ROADMAP_ES.md",
"VALIDATION_MATRIX.md","VALIDATION_MATRIX_ES.md","VALIDATION_MATRIX_EN.md",
"GITHUB_EXECUTION_POLICY.md","cases_3d/README.md",
"cases_3d/C3D_05_step_gmsh_conformal/README.md",
"cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/README.md",
"docs/DOCUMENTATION_INDEX.md","docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md",
"docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md"
]
def check_case_a_status():
    """CASE A has an independent 10-gate manifest; never borrow B's 7 gates."""
    errors = []
    path = ROOT/"docs/C3D04_CASE_A_STATUS.json"
    if not path.is_file():
        return ["Caso A: missing independent progress source"]
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("milestones")
    if data.get("scope") != "CASE_A_C3D_04_V4_T02_ONLY":
        errors.append("Caso A: wrong status scope")
    if not isinstance(entries, list) or len(entries) != 10:
        return errors+["Caso A: expected ten defined milestones"]
    done = sum(entry.get("status") == "DONE" for entry in entries)
    active = [e for e in entries if e.get("status") == "IN_PROGRESS"]
    if (
        done != data.get("progress_count_done")
        or data.get("progress_count_total") != 10
        or 10*done != data.get("progress_percent")
        or len(active) != 1
        or active[0].get("id") != data.get("current_stage")
    ):
        errors.append("Caso A: stage, percentage and closed evidence gates disagree")
    if any(not (ROOT/e["evidence"]).is_file()
           for e in entries if e.get("status") == "DONE"):
        errors.append("Caso A: DONE milestone with missing cited file")
    for p in (
        "cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md",
        "cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md",
        "cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/T0_INPUTS.json",
        ".github/workflows/case-a-t0-stage-contract.yml",
    ):
        if not (ROOT/p).is_file():
            errors.append("Caso A: missing mandatory governance/QA: "+p)
    if data.get("CFD_run") is not False or data.get("physical_validation") is not False:
        errors.append("Caso A: invalid scientific acceptance without T0/CFD evidence")
    return errors


def check(s):
    errors = []
    gates = s["gates"]
    count = sum(g["done"] is True for g in gates)
    if len(gates) != 7 or s["total"] != len(gates) or count != s["completed"] or round(100*count/len(gates)) != s["percent_hitos"]:
        errors.append("Avance e hitos no coinciden")
    if s["percentage_scope"] != "SOLO_HITOS_TECNICOS_DEL_CASO_NO_TESIS_NO_CFD":
        errors.append("Porcentaje de alcance impreciso")
    if s["t0"]["case_materialized"] is False and gates[2]["done"]:
        errors.append("T0 no materializado pero G3 cerrado")
    if s["t0"]["solver_executed"] is False and any(g["done"] for g in gates[3:]):
        errors.append("CFD no ejecutado pero hitos superiores cerrados")
    for g in gates:
        if g["done"] and (not g["evidence"] or not (ROOT/g["evidence"]).is_file()):
            errors.append("Hito sin evidencia: "+g["id"])
    for e in s["other_cases"]:
        if not (ROOT/e["evidence"]).is_file():
            errors.append("Caso sin fuente: "+e["case_id"])
    for path in CORE:
        p=ROOT/path
        if not p.is_file() or MARKER not in p.read_text(encoding="utf-8"):
            errors.append("Regla no sincronizada: "+path)
    if "C3D_05_step_gmsh_conformal," not in (ROOT/"RUN_CASE_REGISTRY.csv").read_text():
        errors.append("C3D05 falta del registro")
    errors.extend(check_case_a_status())
    return errors
def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--status",action="store_true")
    args=parser.parse_args()
    s=json.loads((ROOT/"docs/PROJECT_STAGE_STATUS.json").read_text(encoding="utf-8"))
    if args.status:
        print(f"CASO: {s['case']} | ETAPA: {s['stage']}")
        print(f"AVANCE: {s['completed']}/{s['total']} = {s['percent_hitos']}% de hitos técnicos, NO de tesis ni CFD")
        print("BLOQUEO:",s["blocker"])
        print("SIGUIENTE HITO:",s["next_integrated_delivery"])
        return 0
    errs=check(s)
    for e in errs:print("ERROR:",e,file=sys.stderr)
    if errs:return 1
    print("PASS: "+MARKER+"; documentación consistente, sin comprobar CFD")
    return 0
if __name__=="__main__":raise SystemExit(main())
