#!/usr/bin/env python3
"""Metrics for one cclyzer run, as a JSON object on stdout.

Headline numbers are cclyzer's own end-of-run statistics
($CCLYZER/scripts/stats.py). Program size comes from the facts and from
bc/<suite>/<program>.info.json (scripts/describe.py: LOC, binary size).
Every result relation's and every fact relation's row count is included too,
as "rel:<relation>" and "fact:<relation>".
"""
import argparse, importlib.util, json, os


def lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return None


def relation_sizes(d, prefix):
    out = {}
    for root, _, files in os.walk(d):
        for f in sorted(files):
            if f.endswith(".csv"):
                rel = os.path.relpath(os.path.join(root, f), d)[:-4]
                out[f"{prefix}:{rel}"] = lines(os.path.join(root, f))
    return dict(sorted(out.items()))


def load_stats(cclyzer):
    spec = importlib.util.spec_from_file_location("cclyzer_stats", os.path.join(cclyzer, "scripts", "stats.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    for a in ("facts", "results", "program", "suite", "analysis", "status", "wall", "rss-kb", "factgen", "bc"):
        ap.add_argument("--" + a, required=True)
    ap.add_argument("--cclyzer", default=os.environ.get("CCLYZER"))
    o = ap.parse_args()
    F, R = o.facts, o.results

    m = {"suite": o.suite, "program": o.program, "analysis": o.analysis, "status": o.status}

    info_path = o.bc[:-3] + ".info.json"
    info = json.load(open(info_path)) if os.path.exists(info_path) else {}
    m.update({
        "loc_code": info.get("loc_code"),
        "loc_physical": info.get("loc_physical"),
        "source_files": info.get("source_files"),
        "binary_stripped_bytes": info.get("binary_stripped_bytes"),
        "binary_bytes": info.get("binary_bytes"),
        "bc_bytes": os.path.getsize(o.bc),
    })

    defined = lines(f"{F}/function.csv")
    declared = lines(f"{F}/function_decl.csv")
    m.update({
        "functions_defined": defined,
        "functions_external": declared,
        "call_sites": (lines(f"{F}/call_instruction.csv") or 0) + (lines(f"{F}/invoke_instruction.csv") or 0),
        "instructions": sum(lines(os.path.join(F, f)) or 0 for f in os.listdir(F)
                            if f.endswith("_instruction.csv") and f.count("_") >= 1
                            and f[:-len("_instruction.csv")].replace("_", "").isalpha()),
        "fact_lines": None,
        "factgen_s": float(o.factgen),
        "analysis_s": None if o.wall == "NA" else float(o.wall),
        "peak_rss_mb": None if o.rss_kb == "NA" else round(int(o.rss_kb) / 1024, 1),
    })

    stats = load_stats(o.cclyzer).compute(R, F) if o.status == "ok" else {}
    for key in load_stats(o.cclyzer).ORDER if o.cclyzer else []:
        m[key] = stats.get(key)

    facts = relation_sizes(F, "fact")
    m["fact_lines"] = sum(v or 0 for v in facts.values())
    if o.status == "ok":
        m.update(relation_sizes(R, "rel"))
    m.update(facts)
    print(json.dumps(m))


if __name__ == "__main__":
    main()
