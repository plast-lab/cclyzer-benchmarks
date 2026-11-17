#!/usr/bin/env bash
#
# scripts/build.sh <recipe>  -- download, verify, build one recipe, and copy its
# whole-program bitcode files to bc/<recipe>/<program>.bc.
#
# A recipe (recipes/<name>.sh) sets VERSION, URL, SHA256 and KEEP (an extended
# regex over output paths relative to the source root) and defines build().
# build() runs inside the extracted source tree with CC/CXX/AR/... pointing
# at the LTO toolchain.

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
NAME=${1:?usage: build.sh <recipe>}
RECIPE=$ROOT/recipes/$NAME.sh
[ -f "$RECIPE" ] || { echo "no recipe $RECIPE" >&2; exit 1; }

export LLVM_VERSION=${LLVM_VERSION:-22}
JOBS=${JOBS:-8}
KEEP_NAME=  # optional sed expression mapping a kept path to a program name
EXCLUDE='^$'
# shellcheck source=/dev/null
source "$RECIPE"

DL=$ROOT/downloads; WORK=$ROOT/work/$NAME; OUT=$ROOT/bc/$NAME
mkdir -p "$DL"
TARBALL=$DL/$(basename "$URL")

if [ ! -f "$TARBALL" ]; then
    echo "[$NAME] downloading $URL"
    curl -fL --retry 3 -o "$TARBALL.part" "$URL"
    mv "$TARBALL.part" "$TARBALL"
fi
actual=$(sha256sum "$TARBALL" | cut -d' ' -f1)
if [ "$actual" != "$SHA256" ]; then
    echo "[$NAME] sha256 mismatch for $TARBALL: expected $SHA256, got $actual" >&2
    exit 1
fi

rm -rf "$WORK"; mkdir -p "$WORK"
tar -xf "$TARBALL" -C "$WORK"
SRC=$(find "$WORK" -mindepth 1 -maxdepth 1 -type d | head -n 1)

export BENCH_SRCROOT=$SRC BENCH_COLLECT=$WORK/collect
export CC=$ROOT/scripts/cc-wrap CXX=$ROOT/scripts/c++-wrap
export AR=llvm-ar-$LLVM_VERSION RANLIB=llvm-ranlib-$LLVM_VERSION NM=llvm-nm-$LLVM_VERSION

# Some projects hard-code gcc/cc/ar in their Makefiles. GNU ar would build
# bitcode archives without a symbol index, which lld cannot link, so put
# LTO-aware stand-ins first on PATH.
TOOLBIN=$WORK/toolbin
mkdir -p "$TOOLBIN"
for t in cc gcc clang; do ln -sf "$CC" "$TOOLBIN/$t"; done
for t in c++ g++ clang++; do ln -sf "$CXX" "$TOOLBIN/$t"; done
for t in ar ranlib nm; do ln -sf "$(command -v "llvm-$t-$LLVM_VERSION")" "$TOOLBIN/$t"; done
export PATH=$TOOLBIN:$PATH
export CFLAGS= CXXFLAGS= LDFLAGS= JOBS

echo "[$NAME] building $VERSION with LLVM $LLVM_VERSION in $SRC"
( cd "$SRC" && build ) > "$WORK/build.log" 2>&1 || {
    echo "[$NAME] build failed, last lines of $WORK/build.log:" >&2
    tail -n 25 "$WORK/build.log" >&2
    exit 1
}

rm -rf "$OUT"; mkdir -p "$OUT"
n=0
shopt -s nullglob
for f in "$BENCH_COLLECT"/*.bc; do
    rel=$(basename "$f" .bc); rel=${rel//%//}
    [[ $rel =~ $KEEP ]] || continue
    [[ $rel =~ $EXCLUDE ]] && continue
    prog=$(basename "$rel")
    [ -n "$KEEP_NAME" ] && prog=$(echo "$rel" | sed -E "$KEEP_NAME")
    cp "$f" "$OUT/$prog.bc"
    n=$((n + 1))
done
[ $n -gt 0 ] || { echo "[$NAME] no bitcode matched KEEP='$KEEP'" >&2; exit 1; }
printf '%s\t%s\t%s\t%s\n' "$NAME" "$VERSION" "$LLVM_VERSION" "$n" > "$OUT/BUILD-INFO.tsv"
echo "[$NAME] $n programs -> bc/$NAME/"
