#!/usr/bin/env bash
# One-command CASE B C14 visual review. NO tests, wmake or CFD.
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ -f /opt/openfoam14/etc/bashrc ]]; then
  set +u
  source /opt/openfoam14/etc/bashrc
  set -u
fi
exec python3 -B "$HERE/open_case_b_review.py" "$@"
