#!/usr/bin/env bash
#
# scripts/run.sh <bc/suite/program.bc> <analysis>
#
# Runs one cclyzer analysis on one benchmark and records its metrics.
# Facts are generated once per program and reused by every analysis.
# The analysis runs under a memory cap (systemd scope) and a time limit, so
# a run that blows up is recorded as oom/timeout instead of hurting the host.
#
#   CCLYZER   cclyzer-souffle checkout, built with make   (required)
#   THREADS   Soufflé threads                              (default 8)
#   TIMEOUT   analysis time limit, timeout(1) syntax        (default 3h)
#   MEMMAX    analysis memory cap                          (default 128G)
#   KEEP_RESULTS=1 keeps the result relations instead of deleting them

set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
BC=$(readlink -f "${1:?usage: run.sh <program.bc> <analysis>}")
ANALYSIS=${2:?usage: run.sh <program.bc> <analysis>}
: "${CCLYZER:?set CCLYZER to a built cclyzer-souffle checkout}"
THREADS=${THREADS:-8}; TIMEOUT=${TIMEOUT:-3h}; MEMMAX=${MEMMAX:-128G}

SUITE=$(basename "$(dirname "$BC")"); PROG=$(basename "$BC" .bc)
BASE=$ROOT/results/$SUITE/$PROG
FACTS=$BASE/facts
OUT=$BASE/$ANALYSIS
BIN=$CCLYZER/build/logic/cclyzer-$ANALYSIS
[ -x "$BIN" ] || { echo "no compiled analysis $BIN (run make in $CCLYZER)" >&2; exit 1; }

mkdir -p "$BASE"
# One fact generation per program at a time, even with several analyses
# of the same program running in parallel.
exec 9> "$BASE/.facts.lock"
flock 9
# Facts, once per program and fact generator (the .done marker guards
# against half-written facts; a rebuilt fact generator invalidates them)
if [ ! -f "$FACTS/.done" ] || [ "$BC" -nt "$FACTS/.done" ] \
   || [ "$CCLYZER/bin/fact-generator" -nt "$FACTS/.done" ]; then
    rm -rf "$FACTS"; mkdir -p "$FACTS"
    start=$(date +%s.%N)
    if "$CCLYZER/bin/fact-generator" -o "$FACTS/" "$BC" > "$BASE/factgen.log" 2>&1 \
       && { [ ! -f "$CCLYZER/cti.py" ] || python3 "$CCLYZER/cti.py" "$FACTS/" >> "$BASE/factgen.log" 2>&1; }; then
        echo "$(echo "$(date +%s.%N) - $start" | bc)" > "$FACTS/.done"
    else
        echo "fact generation failed for $BC, see $BASE/factgen.log" >&2
        exit 1
    fi
fi
flock -u 9

rm -rf "$OUT"; mkdir -p "$OUT/results"
timefile=$OUT/time.txt
systemd-run --user --scope --quiet -p MemoryMax="$MEMMAX" -p MemorySwapMax=0 \
    /usr/bin/time -f '%e %M' -o "$timefile" \
    timeout "$TIMEOUT" "$BIN" -j "$THREADS" -F "$FACTS/" -D "$OUT/results/" \
    > "$OUT/analysis.log" 2>&1
rc=$?

if [ $rc = 0 ]; then status=ok
elif [ $rc = 124 ]; then status=timeout
elif [ $rc = 137 ] || grep -qiE 'killed|out of memory|bad_alloc' "$OUT/analysis.log"; then status=oom
else status=error
fi
read -r wall rss_kb < <(grep -E '^[0-9.]+ [0-9]+$' "$timefile" 2>/dev/null || echo "NA NA")

python3 "$ROOT/scripts/metrics.py" --facts "$FACTS" --results "$OUT/results" \
    --program "$PROG" --suite "$SUITE" --analysis "$ANALYSIS" --status "$status" \
    --wall "$wall" --rss-kb "$rss_kb" --factgen "$(cat "$FACTS/.done")" \
    --bc "$BC" > "$OUT/metrics.json"

[ "${KEEP_RESULTS:-0}" = 1 ] || rm -rf "$OUT/results"
echo "$SUITE/$PROG $ANALYSIS: $status (${wall}s, $((${rss_kb/NA/0} / 1024)) MB)"
