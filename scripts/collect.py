#!/usr/bin/env python3
"""Collect results/*/*/*/metrics.json into one CSV (stdout or -o file)."""
import argparse, csv, glob, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output")
ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), ".."))
args = ap.parse_args()

rows = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(args.root, "results/*/*/*/metrics.json")))]
order = {"context-insensitive": 0, "1-call-site-sensitive+heap": 1,
         "2-call-site-sensitive+heap": 2, "2-call-site-sensitive+2-heap": 3}
rows.sort(key=lambda r: (r["suite"], r["program"], order.get(r["analysis"], 9)))
fields = []
for r in rows:
    fields += [k for k in r if k not in fields]
out = open(args.output, "w", newline="") if args.output else sys.stdout
w = csv.DictWriter(out, fieldnames=fields)
w.writeheader()
w.writerows(rows)
print(f"{len(rows)} runs", file=sys.stderr)
