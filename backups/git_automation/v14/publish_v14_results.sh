#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

ORIGINAL_BRANCH="$(git branch --show-current)"
if [ -z "$ORIGINAL_BRANCH" ]; then
    echo "ERROR: detached HEAD."
    exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
RESULT_BRANCH="results/v14-$STAMP"

echo "============================================================"
echo "QuickCup V14 results publisher"
echo "Current branch: $ORIGINAL_BRANCH"
echo "Upload branch:  $RESULT_BRANCH"
echo "============================================================"

git switch -c "$RESULT_BRANCH"

cleanup_on_error() {
    rc=$?
    if [ "$rc" -ne 0 ]; then
        echo
        echo "Publication failed; returning to $ORIGINAL_BRANCH."
        git switch "$ORIGINAL_BRANCH" >/dev/null 2>&1 || true
    fi
    exit "$rc"
}
trap cleanup_on_error EXIT

CASES=(
  B14_topFixedFlux_explicitRef
  C14_topFixedFlux_explicitRef
)

for CASE in "${CASES[@]}"; do
    CASE_DIR="cases_controlled_buoyancy/$CASE"

    for f in log.foamMultiRun log.topSurfaceFlowPostProcess; do
        if [ -e "$CASE_DIR/$f" ]; then
            git add -A -- "$CASE_DIR/$f"
        fi
    done

    for d in logs postProcessing; do
        if [ -d "$CASE_DIR/$d" ]; then
            git add -A -- "$CASE_DIR/$d"
        fi
    done
done

if [ -d analysis_results/v14_run ]; then
    git add -A -- analysis_results/v14_run
fi

if git diff --cached --quiet; then
    echo "No V14 scientific results to publish."
    git switch "$ORIGINAL_BRANCH"
    trap - EXIT
    exit 0
fi

echo
echo "Files selected for V14 publication:"
git --no-pager diff --cached --stat

too_large=0
while IFS= read -r -d '' file; do
    entry="$(git ls-files -s -- "$file" | head -n1 || true)"
    sha="$(printf '%s' "$entry" | awk '{print $2}')"
    if [ -n "$sha" ]; then
        size="$(git cat-file -s "$sha")"
        if [ "$size" -ge 95000000 ]; then
            echo "ERROR: staged file is >=95 MB: $file ($size bytes)"
            too_large=1
        fi
    fi
done < <(git diff --cached --name-only -z)

if [ "$too_large" -ne 0 ]; then
    git restore --staged .
    git switch "$ORIGINAL_BRANCH"
    trap - EXIT
    exit 3
fi

git commit -m "results: publish V14 B/C controlled runs"
git push -u origin "$RESULT_BRANCH"

PUBLISHED_SHA="$(git rev-parse HEAD)"
git switch "$ORIGINAL_BRANCH"
trap - EXIT

echo
echo "============================================================"
echo "V14 RESULTS PUBLISHED"
echo "Branch: $RESULT_BRANCH"
echo "Commit: $PUBLISHED_SHA"
echo "Returned to local branch: $ORIGINAL_BRANCH"
echo "============================================================"
