#!/usr/bin/env python3
"""Describe built benchmarks: source size and binary size.

  scripts/describe.py [bc/<recipe>/<program>.bc ...]   (default: all of bc/)

Writes bc/<recipe>/<program>.info.json with
  source_files        compile units in the bitcode (the .c/.cc files built into it)
  loc_code            non-blank lines that are not only comments, over those files
  loc_physical        all lines of those files
  languages           compile units per DWARF source language
  binary_path         the executable the build produced (relative to its source tree)
  binary_bytes        its size as built (-O0 -g, LTO)
  binary_stripped_bytes  its size after llvm-strip
Needs the build tree in work/<recipe>/ (kept by scripts/build.sh).
"""
import filecmp, glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLVM = os.environ.get("LLVM_VERSION", "22")
CU = re.compile(r'^!(\d+) = distinct !DICompileUnit\(language: (\w+), file: !(\d+)')
FILE = re.compile(r'^!(\d+) = !DIFile\(filename: "((?:[^"\\]|\\.)*)", directory: "((?:[^"\\]|\\.)*)"')


def compile_units(bc):
    """[(path, language)] for every compile unit in the bitcode."""
    dis = subprocess.Popen([f"llvm-dis-{LLVM}", "-o", "-", bc], stdout=subprocess.PIPE, text=True, errors="replace")
    cus, files = [], {}
    for line in dis.stdout:
        if not line.startswith("!"):
            continue
        m = CU.match(line)
        if m:
            cus.append((m.group(3), m.group(2)))
            continue
        m = FILE.match(line)
        if m:
            files[m.group(1)] = (m.group(2), m.group(3))
    dis.wait()
    out = []
    for fid, lang in cus:
        name, directory = files.get(fid, ("", ""))
        out.append((os.path.normpath(os.path.join(directory, name)), lang))
    return out


def count_lines(path):
    """(code, physical) lines of a C-family file; code excludes blank and comment-only lines."""
    code = physical = 0
    in_block = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            physical += 1
            s, has_code, i = line.strip(), False, 0
            while i < len(s):
                if in_block:
                    j = s.find("*/", i)
                    if j < 0:
                        break
                    in_block, i = False, j + 2
                elif s.startswith("/*", i):
                    in_block, i = True, i + 2
                elif s.startswith("//", i):
                    break
                elif s[i] in "\"'":                    # skip string/char literals
                    q, i, has_code = s[i], i + 1, True
                    while i < len(s) and s[i] != q:
                        i += 2 if s[i] == "\\" else 1
                    i += 1
                else:
                    if not s[i].isspace():
                        has_code = True
                    i += 1
            code += has_code
    return code, physical


def find_binary(bc):
    recipe = os.path.basename(os.path.dirname(bc))
    work = os.path.join(ROOT, "work", recipe)
    src = next((d for d in glob.glob(os.path.join(work, "*")) if os.path.isdir(d) and not d.endswith(("collect", "toolbin"))), None)
    for cand in glob.glob(os.path.join(work, "collect", "*.bc")):
        if os.path.getsize(cand) == os.path.getsize(bc) and filecmp.cmp(cand, bc, shallow=False):
            rel = os.path.basename(cand)[:-3].replace("%", "/")
            return rel, os.path.join(src, rel) if src else None
    return None, None


def describe(bc):
    cus = compile_units(bc)
    seen, code, phys, langs, missing = set(), 0, 0, {}, 0
    for path, lang in cus:
        langs[lang] = langs.get(lang, 0) + 1
        if path in seen:
            continue
        seen.add(path)
        if not os.path.isfile(path) and os.path.isfile(os.path.splitext(path)[0] + ".def"):
            path = os.path.splitext(path)[0] + ".def"   # bash generates builtins/*.c from .def files
        if os.path.isfile(path):
            c, p = count_lines(path)
            code, phys = code + c, phys + p
        else:
            missing += 1
    info = {"source_files": len(seen), "source_files_missing": missing,
            "loc_code": code, "loc_physical": phys, "languages": langs}
    rel, exe = find_binary(bc)
    info["binary_path"] = rel
    if exe and os.path.isfile(exe):
        info["binary_bytes"] = os.path.getsize(exe)
        with tempfile.TemporaryDirectory() as t:
            stripped = os.path.join(t, "s")
            subprocess.run([f"llvm-strip-{LLVM}", "-o", stripped, exe], check=True)
            info["binary_stripped_bytes"] = os.path.getsize(stripped)
    else:
        info["binary_bytes"] = info["binary_stripped_bytes"] = None
    with open(bc[:-3] + ".info.json", "w") as f:
        json.dump(info, f, indent=1)
    return bc, info


if __name__ == "__main__":
    bcs = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "bc", "*", "*.bc")))
    for bc in bcs:
        _, info = describe(os.path.abspath(bc))
        print(f"{os.path.relpath(bc, ROOT)}: {info['source_files']} files, {info['loc_code']} LOC, "
              f"binary {info['binary_stripped_bytes']} B stripped"
              + (f" ({info['source_files_missing']} source files not found)" if info["source_files_missing"] else ""))
