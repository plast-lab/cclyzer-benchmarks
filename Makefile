# cclyzer-benchmarks: whole-program LLVM bitcode benchmarks for cclyzer-souffle
#
#   make list                  list the recipes
#   make bc                    build every recipe into bc/<recipe>/<program>.bc
#   make bc-<recipe>           build one recipe, e.g. make bc-nginx
#   make run BC=bc/lua/lua.bc ANALYSIS=context-insensitive
#   make results               every program x every analysis (resumable)
#   make metrics.csv           collect all finished runs into one CSV
#
# Variables: LLVM_VERSION (22), JOBS (8), CCLYZER (cclyzer-souffle checkout),
# ANALYSES, PARALLEL, THREADS, TIMEOUT, MEMMAX (see scripts/run*.sh).

LLVM_VERSION ?= 22
JOBS         ?= 8
CCLYZER      ?= $(HOME)/dev/cclyzer-souffle
ANALYSIS     ?= context-insensitive
ANALYSES     ?= context-insensitive 1-call-site-sensitive+heap 2-call-site-sensitive+heap
export LLVM_VERSION JOBS CCLYZER

RECIPES := $(basename $(notdir $(wildcard recipes/*.sh)))

.PHONY: bc results run list metrics.csv clean-results $(RECIPES:%=bc-%)
bc: $(RECIPES:%=bc-%)

$(RECIPES:%=bc-%): bc-%:
	scripts/build.sh $*

list:
	@for r in $(RECIPES); do printf '%-12s %s\n' $$r "$$(head -n 1 recipes/$$r.sh | sed 's/^# //')"; done

run:
	@test -n "$(BC)" || { echo "usage: make run BC=bc/<suite>/<program>.bc [ANALYSIS=...]"; exit 1; }
	scripts/run.sh $(BC) $(ANALYSIS)

results:
	scripts/run-all.sh $(ANALYSES)

metrics.csv:
	scripts/collect.py -o $@
