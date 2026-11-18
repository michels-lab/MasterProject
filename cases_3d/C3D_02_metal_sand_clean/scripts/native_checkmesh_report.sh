#!/usr/bin/env bash
# Read ONLY logs produced by OpenFOAM Foundation 14 checkMesh.
# Bash/awk reporting; never mesh, solve or change physical dictionaries.

foam_checkmesh_total_volume() {
    local log="$1"
    awk '
        /Total volume[[:space:]]*=/ {
            for (i=1; i<=NF-3; i++) {
                if ($i=="Total" && $(i+1)=="volume" && $(i+2)=="=") {
                    value=$(i+3)
                    sub(/\.$/, "", value)
                    print value
                    exit
                }
            }
        }
    ' "$log"
}

foam_checkmesh_comparison_row() {
    local source_name="$1" region="$2" log="$3"
    if [[ ! -s "$log" ]]; then
        printf '%s\t%s\tNA\tNA\tNA\tNA\tNA\tNA\tNA\n' "$source_name" "$region"
        return
    fi
    awk -v source_name="$source_name" -v region="$region" '
        /^[[:space:]]*cells:/ { cells=$2 }
        /Total volume[[:space:]]*=/ {
            for (i=1; i<=NF-3; i++) {
                if ($i=="Total" && $(i+1)=="volume" && $(i+2)=="=") {
                    volume=$(i+3)
                    sub(/\.$/, "", volume)
                    break
                }
            }
        }
        /Concave cells \(using face planes\) found/ { concave=$NF }
        /Cells with small determinant/ { lowdet=$NF }
        /Error in face tets:/ {
            for (i=1; i<NF; i++) if ($i=="tets:") {bad_tet=$(i+1); break}
        }
        /Failed [0-9]+ mesh checks/ { failed=$2 }
        /Mesh OK/ { mesh_ok=1 }
        END {
            if (cells=="") cells="NA"
            if (volume=="") volume="NA"
            printf "%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\n", \
                source_name, region, cells, volume, concave, lowdet, \
                bad_tet, failed, mesh_ok
        }
    ' "$log"
}

foam_write_mesh_comparison() {
    local baseline="$1" candidate="$2" out="$3" region
    printf 'source\tregion\tcells\tvolume_m3\tconcave_cells\tlow_determinant_cells\tbad_tet_faces\tfailed_checks\tmesh_ok\n' > "$out"
    for region in metal mold; do
        foam_checkmesh_comparison_row BASELINE "$region" "$baseline/log.checkMesh.$region" >> "$out"
        foam_checkmesh_comparison_row CANDIDATE "$region" "$candidate/log.checkMesh.$region" >> "$out"
    done
}
