#!/usr/bin/env bash
set -euo pipefail

# Publish scientific outputs from the completed controlled-buoyancy campaign
# without merging/rebasing the user's current branch and without committing
# heavy/regenerable OpenFOAM runtime data.
#
# Tracked:
#   - case log.foamMultiRun
#   - case log.topSurfaceFlowPostProcess
#   - case logs/
#   - case postProcessing/
#   - analysis_results/
#
# Excluded by .gitignore:
#   - calculated numeric time directories outside postProcessing
#   - generated polyMesh
#   - processor*/processors*
#   - VTK, images, videos, archives, core dumps, dynamicCode/platforms

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

ORIGINAL_BRANCH="$(git branch --show-current)"
if [ -z "$ORIGINAL_BRANCH" ]; then
    echo "ERROR: repository is in detached HEAD state."
    echo "Switch to your normal local branch before publishing results."
    exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
RESULT_BRANCH="results/full-campaign-$STAMP"

echo "============================================================"
echo "QuickCup scientific-results publisher"
echo "Current branch: $ORIGINAL_BRANCH"
echo "Upload branch:  $RESULT_BRANCH"
echo "============================================================"

# Create a temporary publication branch from the exact local state.
# No pull, merge, rebase or reset is performed.
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

# Stage only scientific outputs. Configuration/source changes elsewhere in
# the working tree are intentionally left untouched.
while IFS= read -r -d '' p; do
    git add -A -- "$p"
done < <(find cases_controlled_buoyancy -mindepth 2 -maxdepth 2 -type f \
    \( -name 'log.foamMultiRun' -o -name 'log.topSurfaceFlowPostProcess' \) -print0)

while IFS= read -r -d '' p; do
    git add -A -- "$p"
done < <(find cases_controlled_buoyancy -mindepth 2 -maxdepth 2 -type d \
    \( -name logs -o -name postProcessing \) -print0)

if [ -d analysis_results ]; then
    git add -A -- analysis_results
fi

if git diff --cached --quiet; then
    echo "No new scientific results to publish."
    git switch "$ORIGINAL_BRANCH"
    trap - EXIT
    exit 0
fi

echo
echo "Files selected for publication:"
git diff --cached --stat

# Guard against GitHub's per-file limit before committing.
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
    echo "Nothing was pushed. Add an ignore rule for the oversized output first."
    git restore --staged .
    git switch "$ORIGINAL_BRANCH"
    trap - EXIT
    exit 3
fi

git commit -m "results: publish completed 26-case controlled-buoyancy campaign"
git push -u origin "$RESULT_BRANCH"

PUBLISHED_SHA="$(git rev-parse HEAD)"

git switch "$ORIGINAL_BRANCH"
trap - EXIT

echo
echo "============================================================"
echo "RESULTS PUBLISHED"
echo "Branch: $RESULT_BRANCH"
echo "Commit: $PUBLISHED_SHA"
echo "Returned to local branch: $ORIGINAL_BRANCH"
echo "============================================================"
echo "No merge, rebase, reset or solver execution was performed."
