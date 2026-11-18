#!/usr/bin/env python3
"""Build a spreadsheet (.xlsx) of all benchmark metrics.

  scripts/sheet.py -o cclyzer-benchmarks.xlsx [--before baseline-O0] [--original baseline-original]

Tabs: Summary, Results (one row per program x analysis; every relation and
fact size in collapsed column groups), Before-After, Programs, Columns,
Data sources. Needs openpyxl. Upload the file to Google Drive to get a
Google Sheet (groups, frozen panes and hidden columns are kept).
"""
import argparse, glob, json, os, statistics, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", required=True)
ap.add_argument("--results", default=os.path.join(ROOT, "results"))
ap.add_argument("--before", default=os.path.join(ROOT, "baseline-O0"))
ap.add_argument("--original", default=os.path.join(ROOT, "baseline-original"))
ap.add_argument("--newer", help="ignore result metrics older than this file")
ap.add_argument("--cclyzer", default=os.environ.get("CCLYZER", os.path.expanduser("~/dev/cclyzer-souffle")))
args = ap.parse_args()

ANALYSES = ["context-insensitive", "1-call-site-sensitive+heap",
            "2-call-site-sensitive+heap", "2-call-site-sensitive+2-heap"]
SHORT = {"context-insensitive": "CI", "1-call-site-sensitive+heap": "1cs+H",
         "2-call-site-sensitive+heap": "2cs+H", "2-call-site-sensitive+2-heap": "2cs+2H"}


def load(d, newer=None):
    out = {}
    for f in glob.glob(os.path.join(d, "*/*/*/metrics.json")):
        if newer and os.path.getmtime(f) < os.path.getmtime(newer):
            continue
        try:
            m = json.load(open(f))
        except (OSError, ValueError):
            continue
        out[(m["suite"], m["program"], m["analysis"])] = m
    return out


new, before, orig = load(args.results, args.newer), load(args.before), load(args.original)
if not new:
    sys.exit(f"no metrics under {args.results}")
key = lambda k: (k[0], k[1], ANALYSES.index(k[2]) if k[2] in ANALYSES else 9)

# Column descriptions: cclyzer's own statistic labels plus ours
labels = {}
try:
    sys.path.insert(0, os.path.join(args.cclyzer, "scripts"))
    import stats as _stats
    labels.update({k: v.strip() for k, v in _stats.LABELS.items()})
except Exception:
    pass
labels.update({
    "suite": "benchmark suite (source package)", "program": "program (one linked binary)",
    "analysis": "cclyzer analysis", "status": "ok / timeout / oom / error",
    "loc_code": "lines of C code (no blanks, no comments) in the program's source files",
    "loc_physical": "physical lines in the program's source files",
    "source_files": "source files linked into the program",
    "binary_bytes": "size of the native binary (-O0 -g)",
    "binary_stripped_bytes": "size of the stripped native binary",
    "bc_bytes": "size of the whole-program bitcode",
    "functions_defined": "functions with a body in the bitcode",
    "functions_external": "declared-only (library) functions",
    "instructions": "LLVM instructions in the bitcode",
    "fact_lines": "total input fact lines",
    "factgen_s": "fact generation time (s)",
    "analysis_s": "analysis wall time (s)",
    "peak_rss_mb": "analysis peak memory (MB)",
    "var_points_to": "var points-to pairs, contexts removed (VPT)",
    "var_points_to_ctx": "var points-to tuples with contexts (sensitive VPT)",
    "ptr_points_to": "object points-to pairs, contexts removed",
    "ptr_points_to_ctx": "object points-to tuples with contexts",
    "callgraph_edges": "call-graph edges, contexts removed (CGE)",
    "callgraph_edges_ctx": "call-graph edges with contexts (sensitive CGE)",
    "reachable_contexts": "contexts of reachable functions",
    "heap_allocations": "heap allocation sites", "stack_allocations": "stack allocation sites",
    "global_allocations": "global variables / functions as objects",
    "allocations": "abstract objects (including typed views and field objects)",
    "reachable_vars": "reachable pointer variables", "nonempty_vars": "  with a non-empty points-to set",
    "empty_vars": "  with an empty points-to set",
    "nonempty_ptrs": "objects that point to something", "empty_ptrs": "pointer-typed objects pointing to nothing",
})

rows = sorted(new.values(), key=lambda m: key((m["suite"], m["program"], m["analysis"])))
cols = []
for m in rows:
    cols += [k for k in m if k not in cols and k not in cols]
seen = set(); cols = [c for c in cols if not (c in seen or seen.add(c))]
ident = ["suite", "program", "analysis", "status"]
size = ["loc_code", "loc_physical", "source_files", "binary_bytes", "binary_stripped_bytes", "bc_bytes"]
perf = ["analysis_s", "peak_rss_mb", "factgen_s"]
head = ["var_points_to", "var_points_to_ctx", "avg_var_points_to", "callgraph_edges", "callgraph_edges_ctx",
        "reachable_functions", "reachable_functions_defined", "reachable_functions_external",
        "call_sites", "call_sites_direct", "call_sites_external",
        "indirect_calls", "indirect_calls_mono", "indirect_calls_poly", "indirect_calls_unresolved",
        "avg_indirect_targets", "deref_sites", "deref_sites_empty", "avg_deref_points_to",
        "inttoptr_casts", "ptrtoint_casts", "dynamic_cast_sites"]
rest = [c for c in cols if c not in ident + size + perf + head and not c.startswith(("rel:", "fact:"))]
rels = sorted(c for c in cols if c.startswith("rel:"))
facts = sorted(c for c in cols if c.startswith("fact:"))
order = ident + size + perf + [c for c in head if c in cols] + rest + rels + facts

BOLD = Font(bold=True)
HEAD = PatternFill("solid", fgColor="DDE4EE")
BAD = PatternFill("solid", fgColor="F6D5D5")


def header(ws, names, row=1):
    for j, n in enumerate(names, 1):
        c = ws.cell(row=row, column=j, value=n)
        c.font = BOLD; c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")


def widths(ws, w):
    for j, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(j)].width = x


wb = Workbook()

# ---------------------------------------------------------------- Summary
ws = wb.active; ws.title = "Summary"


def agg(data, a, keys=None):
    ks = [k for k in data if k[2] == a and (keys is None or k in keys)]
    ok = [data[k] for k in ks if data[k]["status"] == "ok"]
    s = lambda f: sum((m.get(f) or 0) for m in ok)
    return dict(n=len(ks), ok=len(ok), bad=len(ks) - len(ok), time=s("analysis_s"),
                mem=max([m.get("peak_rss_mb") or 0 for m in ok] or [0]),
                vpt=s("var_points_to"), cge=s("callgraph_edges"),
                avgvpt=statistics.mean([m.get("avg_var_points_to") or 0 for m in ok]) if ok else None,
                unres=s("indirect_calls_unresolved"), ind=s("indirect_calls"),
                empty=s("deref_sites_empty"), deref=s("deref_sites"))


ws.append(["cclyzer-souffle on cclyzer-benchmarks: whole programs, LLVM 22, -O0 -g, full LTO"]); ws["A1"].font = Font(bold=True, size=13)
ws.append([f"{len({(m['suite'], m['program']) for m in rows})} programs from "
           f"{len({m['suite'] for m in rows})} packages; one row per program and analysis in the Results tab."])
ws.append([])
ws.append(["Current version (mem2reg facts, refined 2-call-site, optimized rules)"]); ws.cell(ws.max_row, 1).font = BOLD
hdr = ["analysis", "runs", "ok", "timeout/oom/error", "total analysis time (s)", "max peak memory (MB)",
       "total VPT", "total CGE", "mean avg var points-to", "indirect calls", "unresolved", "derefs", "empty derefs"]
header(ws, hdr, ws.max_row + 1)
for a in ANALYSES:
    g = agg(new, a)
    if g["n"]:
        ws.append([a, g["n"], g["ok"], g["bad"], round(g["time"]), g["mem"], g["vpt"], g["cge"],
                   round(g["avgvpt"], 2) if g["avgvpt"] is not None else None, g["ind"], g["unres"], g["deref"], g["empty"]])
ws.append([])
ws.append(["Before -> after, on the runs that finished in both (same programs, same analysis)"]); ws.cell(ws.max_row, 1).font = BOLD
header(ws, ["analysis", "comparison", "programs", "time before (s)", "time after (s)", "speedup",
            "mean avg VPT before", "mean avg VPT after", "total VPT before", "total VPT after"], ws.max_row + 1)
for label, base in [("original rules (master), no mem2reg", orig), ("optimized rules, no mem2reg, old 2-call-site", before)]:
    for a in ANALYSES:
        both = {k for k in new if k[2] == a and k in base and new[k]["status"] == base[k]["status"] == "ok"}
        if not both:
            continue
        b, n = agg(base, a, both), agg(new, a, both)
        ws.append([a, label, len(both), round(b["time"]), round(n["time"]),
                   round(b["time"] / n["time"], 2) if n["time"] else None,
                   round(b["avgvpt"], 2), round(n["avgvpt"], 2), b["vpt"], n["vpt"]])
ws.append([])
notes = [
    "Notes",
    "VPT = var points-to pairs with contexts removed; sensitive VPT keeps contexts. CGE = call-graph edges (same convention).",
    "'mean avg var points-to' = mean over programs of each program's average non-empty points-to set size.",
    "mem2reg: locals whose address is never taken are SSA values, not stack objects (fact-generator default; --no-mem2reg = old model).",
    "2-call-site refinement: stack objects get the full method context; heap objects keep one call site ('+heap').",
    "Rule optimizations (query plans, intermediate relations) do not change results (outputs compared on the benchmark programs).",
    "Unresolved indirect calls are high because indirect-call resolution is broken for opaque pointers (student task).",
    "Each analysis ran under a memory cap (64 GB; 700 GB for the largest programs) and a time limit; see status.",
]
for n in notes:
    ws.append([n])
ws.cell(ws.max_row - len(notes) + 1, 1).font = BOLD
widths(ws, [30, 40, 10, 16, 16, 12, 16, 16, 18, 14, 12, 12, 12])

# ---------------------------------------------------------------- Results
ws = wb.create_sheet("Results")
header(ws, order)
for m in rows:
    ws.append([m.get(c) for c in order])
    if m["status"] != "ok":
        for j in range(1, 5):
            ws.cell(ws.max_row, j).fill = BAD
ws.freeze_panes = "E2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(order))}{ws.max_row}"
widths(ws, [11, 20, 26, 8] + [12] * (len(order) - 4))
ws.row_dimensions[1].height = 45
first_rel = order.index(rels[0]) + 1 if rels else None
first_fact = order.index(facts[0]) + 1 if facts else None
if rels:
    ws.column_dimensions.group(get_column_letter(first_rel), get_column_letter(first_rel + len(rels) - 1),
                               hidden=True, outline_level=1)
if facts:
    ws.column_dimensions.group(get_column_letter(first_fact), get_column_letter(first_fact + len(facts) - 1),
                               hidden=True, outline_level=1)

# ---------------------------------------------------------------- Before-After
ws = wb.create_sheet("Before-After")
cmp = ["analysis_s", "peak_rss_mb", "var_points_to", "avg_var_points_to", "callgraph_edges",
       "reachable_functions", "deref_sites_empty"]
hdr = ["suite", "program", "analysis", "status now", "time original rules (s)"]
for c in cmp:
    hdr += [f"{c} before", f"{c} now"]
hdr += ["speedup vs before", "speedup vs original"]
header(ws, hdr)
for m in rows:
    k = (m["suite"], m["program"], m["analysis"])
    b, o = before.get(k, {}), orig.get(k, {})
    r = [k[0], k[1], k[2], m["status"], o.get("analysis_s") if o.get("status") == "ok" else None]
    for c in cmp:
        r += [b.get(c) if b.get("status") == "ok" else None, m.get(c) if m["status"] == "ok" else None]
    t = m.get("analysis_s") if m["status"] == "ok" else None
    tb = b.get("analysis_s") if b.get("status") == "ok" else None
    to = o.get("analysis_s") if o.get("status") == "ok" else None
    r += [round(tb / t, 2) if tb and t else None, round(to / t, 2) if to and t else None]
    ws.append(r)
ws.freeze_panes = "D2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{ws.max_row}"
widths(ws, [11, 20, 26, 9] + [13] * (len(hdr) - 4)); ws.row_dimensions[1].height = 45

# ---------------------------------------------------------------- Programs
ws = wb.create_sheet("Programs")
pc = ["suite", "program", "loc_code", "loc_physical", "source_files", "binary_bytes", "binary_stripped_bytes",
      "bc_bytes", "functions_defined", "functions_external", "instructions", "call_sites", "fact_lines", "factgen_s"]
pc = [c for c in pc if c in cols]
header(ws, pc + ["analyses ok"])
progs = {}
for m in rows:
    progs.setdefault((m["suite"], m["program"]), []).append(m)
for (s, p), ms in sorted(progs.items()):
    first = ms[0]
    ws.append([first.get(c) for c in pc] + [", ".join(SHORT.get(x["analysis"], x["analysis"]) for x in ms if x["status"] == "ok")])
ws.freeze_panes = "C2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(pc) + 1)}{ws.max_row}"
widths(ws, [11, 20] + [13] * (len(pc) - 2) + [24])

# ---------------------------------------------------------------- Columns
ws = wb.create_sheet("Columns")
header(ws, ["column", "meaning"])
for c in order:
    if c.startswith("rel:"):
        d = f"tuples in output relation {c[4:]}"
    elif c.startswith("fact:"):
        d = f"lines in input fact file {c[5:]}"
    else:
        d = labels.get(c, "")
    ws.append([c, d])
widths(ws, [48, 90])

# ---------------------------------------------------------------- Data sources
ws = wb.create_sheet("Data sources")
for line in [
    "Programs: cclyzer-benchmarks recipes (pinned source tarballs, sha256-checked), built with clang -flto -g -O0 and lld --save-temps;",
    "  the whole-program bitcode is lld's merged module before LTO optimization (<binary>.0.0.preopt.bc).",
    "LOC: C/C++ code lines (comments and blank lines excluded) of the source files compiled into each binary (from the build's dependency files).",
    "Binary size: the native -O0 -g binary built alongside, and its stripped size.",
    "Analyses: cclyzer-souffle branch llvm-floor-20, compiled Soufflé 2.5 programs (64-bit domains), 4 threads (8 for the largest programs).",
    "'before' = baseline-O0: same programs and rules, without mem2reg and with the old 2-call-site stack contexts.",
    "'original' = baseline-original: master's rules (before the query-plan work), context-insensitive only.",
    "Headline statistics: cclyzer's scripts/stats.py; rel:* = every output relation's size; fact:* = every input fact file's line count.",
    "Machine: 750 GB RAM shared server; times are wall-clock with several runs in parallel (phase 1: 6 at a time).",
]:
    ws.append([line])
ws.column_dimensions["A"].width = 150

wb.save(args.output)
print(f"{args.output}: {len(rows)} runs, {len(order)} columns ({len(rels)} relations, {len(facts)} fact files)", file=sys.stderr)
