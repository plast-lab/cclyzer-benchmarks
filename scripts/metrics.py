#!/usr/bin/env python3
"""Metrics for one cclyzer run, as a JSON object on stdout.

Program size comes from the facts, analysis results from the result
relations (only when the run finished). Context-sensitive relations are
compared through their context-stripped projections (stripctx_*), so the
numbers are comparable across analyses.
"""
import argparse, json, os, re


def lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return None


def rows(path, cols):
    """Yield the given 0-based columns of a tab-separated relation."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            yield tuple(parts[c] for c in cols)


def column_set(path, col=0):
    try:
        return {r[0] for r in rows(path, [col])}
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser()
    for a in ("facts", "results", "program", "suite", "analysis", "status", "wall", "rss-kb", "factgen", "bc"):
        ap.add_argument("--" + a, required=True)
    o = ap.parse_args()
    F, R = o.facts, o.results

    instr_files = [f for f in os.listdir(F) if re.fullmatch(r"[a-z_]+_instruction\.csv", f)]
    m = {
        "suite": o.suite, "program": o.program, "analysis": o.analysis, "status": o.status,
        "bc_bytes": os.path.getsize(o.bc),
        "factgen_s": float(o.factgen),
        "analysis_s": None if o.wall == "NA" else float(o.wall),
        "peak_rss_mb": None if o.rss_kb == "NA" else round(int(o.rss_kb) / 1024, 1),
        "functions_defined": lines(f"{F}/function.csv"),
        "functions_external": None,
        "instructions": sum(lines(f"{F}/{f}") or 0 for f in instr_files),
        "call_sites": (lines(f"{F}/call_instruction.csv") or 0) + (lines(f"{F}/invoke_instruction.csv") or 0),
        "fact_lines": sum(lines(os.path.join(d, f)) or 0
                          for d, _, fs in os.walk(F) for f in fs if f.endswith(".csv")),
    }
    decl = column_set(f"{F}/function_decl.csv")
    defined = column_set(f"{F}/function.csv")
    if decl is not None and defined is not None:
        m["functions_external"] = len(decl - defined)
    m["has_main"] = any(n == "@main"
                        for n, in rows(f"{F}/function_has_name.csv", [1])) \
        if os.path.exists(f"{F}/function_has_name.csv") else None

    if o.status == "ok":
        reach_instr = column_set(f"{R}/reachable_instruction.csv")
        indirect = column_set(f"{R}/indirect_call_instruction.csv") or set()
        cg = list(rows(f"{R}/stripctx_callgraph_edge.csv", [0, 1]))
        targets = {}
        for callee, site in cg:
            targets.setdefault(site, set()).add(callee)
        reach_ind = indirect & reach_instr
        resolved = [s for s in reach_ind if targets.get(s)]
        pts_vars = {}
        for alloc, var in rows(f"{R}/stripctx_var_points_to.csv", [0, 1]):
            pts_vars[var] = pts_vars.get(var, 0) + 1
        m.update({
            "reachable_functions": lines(f"{R}/reachable_function.csv"),
            "reachable_instructions": len(reach_instr),
            "callgraph_edges": len(cg),
            "callgraph_edges_with_ctx": lines(f"{R}/callgraph_edge.csv"),
            "indirect_calls_reachable": len(reach_ind),
            "indirect_calls_resolved": len(resolved),
            "indirect_calls_unresolved": len(reach_ind) - len(resolved),
            "avg_targets_per_resolved_indirect": round(sum(len(targets[s]) for s in resolved) / len(resolved), 3) if resolved else None,
            "allocations": lines(f"{R}/allocation.csv"),
            "var_points_to": sum(pts_vars.values()),
            "var_points_to_with_ctx": lines(f"{R}/var_points_to.csv"),
            "vars_with_points_to": len(pts_vars),
            "avg_points_to_set": round(sum(pts_vars.values()) / len(pts_vars), 3) if pts_vars else None,
        })
    print(json.dumps(m))


if __name__ == "__main__":
    main()
