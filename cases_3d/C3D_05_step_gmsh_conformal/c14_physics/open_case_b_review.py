#!/usr/bin/env python3
"""Prepare and open the FINISHED real C3D05-B C14 101-state CFD in ParaView.

No tests, no numerical postprocessing, no foamMultiRun, no wmake, no rerun.
An independent lightweight case includes symbolic links to ORIGINAL saved CFD
files plus the original reports. Original CFD remains unchanged.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SOURCE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
DEST=Path.home()/"OpenFOAM/C3D05_B_C14_PARAVIEW_REVIEW"
FOAM="CASE_B_C14_10S.foam"
RESULTS={
    "01_C14_temperature_time_series.csv":("C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01","C3D05_B_C14_REAL_10S_TIME_SERIES.csv"),
    "02_volume_weighted_phase_101.csv":("C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01","C3D05_B_C14_VOLUME_WEIGHTED_ALPHA1_101_STATES.csv"),
    "03_native_q_4patches_101x4.csv":("C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01","C3D05_B_C14_NATIVE_Q_101X4_PATCHES.csv"),
    "04_native_q_time_series_101.csv":("C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01","C3D05_B_C14_NATIVE_Q_101_TIMES.csv"),
    "05_native_q_facewise_at_10s.csv":("C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01","C3D05_B_C14_NATIVE_Q_T10_ALL_FACES.csv"),
    "06_q_vs_reference_storage_101.csv":("C3D05_B_C14_Q_VS_REFERENCE_STORAGE_01","C3D05_B_C14_101_TIME_Q_VS_STORAGE_REFERENCE_ONLY.csv"),
    "07_q_sampling_sensitivity.csv":("C3D05_B_C14_ENERGY_TERMS_READINESS_01","C3D05_B_C14_SAVED_TIME_Q_QUADRATURE_SENSITIVITY_NOT_SOLVER_DT.csv"),
    "08_rho_phi_mass_if_already_available.csv":("C3D05_B_C14_NATIVE_RHO_PHI_MASS_01","C3D05_B_C14_REAL_METAL_RHO_PHI_MASS_101_TIME_COVERAGE.csv")
}
MANIFEST="CASE_B_C14_MANUAL_REVIEW.json"

def require(ok,reason):
    if not ok:
        raise ValueError("CASE_B_MANUAL_REVIEW: "+reason)

def times_in(source):
    times=[]
    for entry in source.iterdir():
        if entry.is_dir() and not entry.is_symlink() and re.fullmatch(r"\d+(?:\.\d+)?",entry.name):
            times.append((float(entry.name),entry.name))
    times.sort()
    require(len(times)==101 and len(set(t for t,n in times))==101 and
            all(abs(t-.1*i)<1e-8 for i,(t,n) in enumerate(times)),
            "se requieren 101 directorios guardados en la simulacion real entre 0 y 10 s")
    return times

def safe_link(where,original):
    require(original.exists() and not original.is_symlink(),
            "no existe campo original o es enlace: "+str(original))
    where.symlink_to(original,target_is_directory=original.is_dir())

def prepare(source,dest):
    require(source.is_dir() and not source.is_symlink() and source.name==SOURCE.name,
            "falta el CFD original C14-B completado")
    require(dest!=source and dest not in source.parents and source not in dest.parents,
            "nunca preparar la vista dentro del CFD original")
    for r in ("metal","mold"):
        require((source/"constant"/r/"polyMesh/points").is_file(),
                "falta malla real de "+r)
    saved=times_in(source)
    for t,name in (saved[0],saved[1],saved[-1]):
        for r in ("metal","mold"):
            require((source/name/r/"T").is_file(),
                    "falta campo T original en "+r+" tiempo "+name)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="."+dest.name+".staging_",dir=dest.parent) as base:
        staging=Path(base)/"ready"
        staging.mkdir()
        case=staging/"OPEN_IN_PARAVIEW"
        case.mkdir()
        for dirname in ("constant","system"):
            safe_link(case/dirname,source/dirname)
        count=0
        for t,name in saved:
            time=case/name
            time.mkdir()
            originals=source/name
            for region in ("metal","mold"):
                original_region=originals/region
                require(original_region.is_dir() and not original_region.is_symlink(),
                        "falta la region original "+name+"/"+region)
                view_region=time/region
                view_region.mkdir()
                for file in original_region.iterdir():
                    safe_link(view_region/file.name,file)
                    count+=1
            for file in originals.iterdir():
                if file.name not in ("metal","mold"):
                    safe_link(time/file.name,file)
                    count+=1
        (case/FOAM).touch()
        tables=staging/"RESULTADOS_CSV"
        tables.mkdir()
        linked=[]
        absent=[]
        for friendly,(folder,filename) in RESULTS.items():
            original=source.parent/folder/filename
            if original.is_file() and not original.is_symlink():
                safe_link(tables/friendly,original)
                linked.append(friendly)
            else:
                absent.append(friendly)
        manifest={
            "status":"C3D05_B_C14_OPENFOAM_PARAVIEW_READY_FOR_MANUAL_REVIEW",
            "source_original_CFD_read_only":str(source),
            "original_saved_times":len(saved),
            "original_CFD_last_time_s":saved[-1][0],
            "native_metal_cells":92200,
            "native_mold_cells":178588,
            "native_faces_contact_each_side":12636,
            "field_symlinks":count,
            "linked_original_CSV":linked,
            "not_yet_existing_optional_CSV":absent,
            "foam":str(dest/"OPEN_IN_PARAVIEW"/FOAM),
            "NO_CFD_RERUN":True,
            "NO_NEW_TESTS":True,
            "source_files_copied":False,
            "full_energy_conservation_or_experimental_validation":False,
        }
        (staging/MANIFEST).write_text(json.dumps(manifest,indent=2)+"\n")
        (staging/"LEEME_REVISION_MANUAL.txt").write_text(
            "CASO B C14: LISTO PARA REVISION VISUAL\n\n"
            "Abre OPEN_IN_PARAVIEW/"+FOAM+" en ParaView.\n"
            "Mesh Regions: activa metal/internalMesh y mold/internalMesh.\n"
            "Cell Arrays: T, U, p_rgh, p, phaseChangeSource:alpha1 (si están listadas).\n"
            "Apply; recorre la barra de tiempo desde t=0 hasta t=10s.\n"
            "Temperatura: T para metal y arena.\n"
            "Solidificacion: phaseChangeSource:alpha1 del metal, 1 liquido, 0 solido.\n"
            "Velocidad: U solo en hierro; usa Slice, Glyph, Stream Tracer.\n"
            "Surface With Edges sirve para revisar el contacto metal-molde.\n"
            "RESULTADOS_CSV enlaza curvas reales ya calculadas, sin recalcularlas.\n\n"
            "C14 de referencia NO validado experimentalmente ni cerrado en energia.\n"
            "La comparacion -11.436 J NO es calor perdido.\n"
            "No se repite CFD ni se altera un campo de la simulacion real.\n")
        require(not dest.exists() and not dest.is_symlink(),
                "ya existe un destino con ese nombre, no sobrescribir")
        staging.rename(dest)
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prepare-only",action="store_true",
                   help="prepara caso y CSV sin abrir ParaView")
    args=p.parse_args()
    source=SOURCE.expanduser().absolute()
    dest=DEST.expanduser().absolute()
    try:
        if dest.exists():
            doc=dest/MANIFEST
            require(doc.is_file() and not doc.is_symlink(),
                    "destino existente no pertenece a esta vista, no sobrescribir")
            report=json.loads(doc.read_text())
            require(report.get("status")==
                "C3D05_B_C14_OPENFOAM_PARAVIEW_READY_FOR_MANUAL_REVIEW"
                and report.get("source_original_CFD_read_only")==str(source),
                "destino existente ajeno a esta corrida C14")
        else:
            report=prepare(source,dest)
        file=dest/"OPEN_IN_PARAVIEW"/FOAM
        require(file.is_file(),"no se genero marcador foam")
        print("\nCASO B C14 LISTO: 101 TIEMPOS, HIERRO + ARENA, RESULTADOS EXISTENTES")
        print("ParaView .foam: "+str(file))
        print("Tablas enlazadas: "+str(len(report["linked_original_CSV"])))
        print("Sin CFD, sin pruebas, sin modificar el caso original.")
        print("Apertura manual alternativa: paraview --data="+str(file))
        if args.prepare_only:
            return 0
        program=shutil.which("paraview")
        if not program:
            print("ParaView no aparece en PATH; abre el marcador desde ParaView.")
            return 0
        print("Abriendo ParaView para revision manual...",flush=True)
        return subprocess.call([program,"--data="+str(file)])
    except (ValueError,OSError,KeyError,UnicodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
