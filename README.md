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

Analyses: `context-insensitive`, `1-call-site-sensitive+heap`,
`2-call-site-sensitive+heap`, `2-call-site-sensitive+2-heap`.

Each run is limited by `TIMEOUT` (default 2h) and `MEMMAX` (default 96G,
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

| Suite | Version | Programs |
|---|---|---|
| coreutils | 9.5 | 107 |
| postgresql | 16.4 | 32 (server and client tools) |
| git | 2.47.0 | 5 |
| redis | 7.2.6 | 3 |
| bc, bzip2, lua | | 2 each |
| bash, curl, grep, gzip, jq, make, nginx, sed, sqlite, tar, zstd | | 1 each |

164 programs in total.
