# cclyzer-benchmarks

Whole-program LLVM bitcode benchmarks for
[cclyzer-souffle](https://github.com/plast-lab/cclyzer-souffle), built from
pinned upstream sources with one command, plus one-liners to analyse them and
collect metrics.

Each `bc/<suite>/<program>.bc` is **one whole program**: every translation unit
and every static library of the project is linked into it (with LTO), so only
real external libraries such as libc stay undefined. Analysing single
translation units instead leaves calls into other files undefined, which cuts
the call graph and loses function-pointer targets.

## Requirements

- clang, lld and llvm-ar for one LLVM version (default 22), e.g. from
  [apt.llvm.org](https://apt.llvm.org): `clang-22 lld-22 llvm-22`
- the usual autotools build dependencies (`build-essential`), curl, tar, xz
- for running analyses: a built cclyzer-souffle checkout (`make` there builds
  one compiled binary per analysis)

## Building the bitcode

```sh
make list                 # the recipes
make bc                   # all of them, into bc/
make bc-nginx             # just one
make bc LLVM_VERSION=21   # with another LLVM
```

Sources are downloaded once into `downloads/` and checked against the
sha256 in each recipe.

### How it works

`scripts/cc-wrap` is used as the C/C++ compiler. It adds `-flto -g -O0` to
every compile, so object files and static libraries hold bitcode, and links
with `lld --save-temps`. lld then writes the merged whole-program module before
any LTO optimisation (`<output>.0.0.preopt.bc`), which the wrapper saves. The
project's own `configure` and `make` run unchanged and still produce working
executables, so no build files need patching. `BENCH_OPT=-O1` changes the
optimisation level of the compiles.

A recipe (`recipes/<name>.sh`) is a few lines: version, URL, sha256, which
outputs to keep (`KEEP`, a regex over output paths), and a `build()`
function with the project's normal build commands.

## Running analyses

```sh
export CCLYZER=~/dev/cclyzer-souffle
make run BC=bc/lua/lua.bc ANALYSIS=context-insensitive
make results              # every program x every analysis, resumable
make metrics.csv          # one row per run
```

Analyses: `context-insensitive`, `1-call-site-sensitive+heap`, `selective`,
`2-call-site-sensitive+heap`, `2-call-site-sensitive+2-heap`.

Each run is limited by `TIMEOUT` (default 2h with `make results`, 3h with `make run`) and `MEMMAX` (default 96G / 128G,
through a systemd scope), and recorded as `ok`, `timeout`, `oom` or `error`.
`PARALLEL` runs go at once with `THREADS` threads each. Facts are generated
once per program and shared by all analyses; result relations are deleted
after their metrics are taken unless `KEEP_RESULTS=1`.

## Metrics

| Column | Meaning |
|---|---|
| `bc_bytes`, `functions_defined`, `functions_external`, `instructions`, `call_sites`, `fact_lines` | program size |
| `factgen_s`, `analysis_s`, `peak_rss_mb` | cost (fact generation, analysis wall time, analysis peak memory) |
| `reachable_functions`, `reachable_instructions` | reachable from `main` |
| `callgraph_edges` | call-graph edges without contexts; `_with_ctx` with them |
| `indirect_calls_reachable/resolved/unresolved` | reachable indirect calls with and without a target |
| `avg_targets_per_resolved_indirect` | precision of indirect-call resolution |
| `var_points_to`, `vars_with_points_to`, `avg_points_to_set` | points-to without contexts; `var_points_to_with_ctx` with them |

Context-sensitive results are compared through their context-stripped
projections, so the numbers are comparable across analyses.

## Programs

| Suite | Version | Programs | Source |
|---|---|---|---|
| coreutils | 9.5 | 107 | [coreutils-9.5.tar.xz](https://ftp.gnu.org/gnu/coreutils/coreutils-9.5.tar.xz) |
| postgresql | 16.4 | 32 (server and client tools) | [postgresql-16.4.tar.bz2](https://ftp.postgresql.org/pub/source/v16.4/postgresql-16.4.tar.bz2) |
| git | 2.47.0 | 5 | [git-2.47.0.tar.xz](https://mirrors.edge.kernel.org/pub/software/scm/git/git-2.47.0.tar.xz) |
| redis | 7.2.6 | 3 | [redis-7.2.6.tar.gz](https://download.redis.io/releases/redis-7.2.6.tar.gz) |
| bc | 1.07.1 | 2 | [bc-1.07.1.tar.gz](https://ftp.gnu.org/gnu/bc/bc-1.07.1.tar.gz) |
| bzip2 | 1.0.8 | 2 | [bzip2-1.0.8.tar.gz](https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz) |
| lua | 5.4.7 | 2 | [lua-5.4.7.tar.gz](https://www.lua.org/ftp/lua-5.4.7.tar.gz) |
| bash | 5.2.37 | 1 | [bash-5.2.37.tar.gz](https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz) |
| curl | 8.10.1 | 1 | [curl-8.10.1.tar.xz](https://curl.se/download/curl-8.10.1.tar.xz) |
| grep | 3.11 | 1 | [grep-3.11.tar.xz](https://ftp.gnu.org/gnu/grep/grep-3.11.tar.xz) |
| gzip | 1.13 | 1 | [gzip-1.13.tar.xz](https://ftp.gnu.org/gnu/gzip/gzip-1.13.tar.xz) |
| jq | 1.7.1 | 1 | [jq-1.7.1.tar.gz](https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-1.7.1.tar.gz) |
| make | 4.4.1 | 1 | [make-4.4.1.tar.gz](https://ftp.gnu.org/gnu/make/make-4.4.1.tar.gz) |
| nginx | 1.26.2 | 1 | [nginx-1.26.2.tar.gz](https://nginx.org/download/nginx-1.26.2.tar.gz) |
| sed | 4.9 | 1 | [sed-4.9.tar.xz](https://ftp.gnu.org/gnu/sed/sed-4.9.tar.xz) |
| sqlite | 3.46.1 | 1 | [sqlite-autoconf-3460100.tar.gz](https://www.sqlite.org/2024/sqlite-autoconf-3460100.tar.gz) |
| tar | 1.35 | 1 | [tar-1.35.tar.xz](https://ftp.gnu.org/gnu/tar/tar-1.35.tar.xz) |
| zstd | 1.5.6 | 1 | [zstd-1.5.6.tar.gz](https://github.com/facebook/zstd/releases/download/v1.5.6/zstd-1.5.6.tar.gz) |

Each source is checked against the sha256 in its recipe before building.

164 programs in total.
