#!/usr/bin/env bash
#
# scripts/run-all.sh [analysis...]  -- run every bc/*/*.bc with each analysis
#
# Smallest programs first. PARALLEL runs at a time, each with THREADS Soufflé
# threads, MEMMAX memory and TIMEOUT time (see run.sh). Finished runs
# (metrics.json present) are skipped, so the script can be restarted.
#
#   PARALLEL  concurrent runs   (default 4)
#   PROGRAMS  extended regex over suite/program to restrict the set
#   FORCE=1   rerun finished runs too

set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${CCLYZER:?set CCLYZER to a built cclyzer-souffle checkout}"
export CCLYZER THREADS=${THREADS:-4} TIMEOUT=${TIMEOUT:-2h} MEMMAX=${MEMMAX:-96G}
PARALLEL=${PARALLEL:-4}
ANALYSES=("$@")
[ ${#ANALYSES[@]} -gt 0 ] || ANALYSES=(context-insensitive 1-call-site-sensitive+heap 2-call-site-sensitive+heap)

cd "$ROOT"
for a in "${ANALYSES[@]}"; do
    for bc in $(ls -S -r bc/*/*.bc); do
        id=$(basename "$(dirname "$bc")")/$(basename "$bc" .bc)
        [[ $id =~ ${PROGRAMS:-.} ]] || continue
        [ "${FORCE:-0}" != 1 ] && [ -f "results/$id/$a/metrics.json" ] && continue
        printf '%s\t%s\n' "$bc" "$a"
    done
done | xargs -P "$PARALLEL" -L 1 bash -c 'nice scripts/run.sh "$0" "$1"' \
     | tee -a "$ROOT/results/run-all.log"
