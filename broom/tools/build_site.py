#!/usr/bin/env python3
"""Bundle the codebase into an in-page exhibit + compute live stats.

Writes:
  site/assets/code-data.js   window.CODEBASE = {tree, files:[{path,lang,code}]}
  site/assets/stats.js       window.STATS = {files, loc, tests, langs, ...}

The engineering / code pages read these to show the whole source tree with
syntax highlighting -- no external GitHub link, the code lives in the site.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # broom/
OUT = os.path.join(ROOT, "site", "assets")

INCLUDE_DIRS = ["nimbus_fc", "rust/nimbus_core/src", "scenarios", "tests", "tools"]
INCLUDE_FILES = ["Cargo.toml", "rust/nimbus_core/Cargo.toml", "Makefile",
                 "requirements.txt", "pyproject.toml", "README.md", "BALLS.md",
                 "MATCH.md"]
EXT_LANG = {".py": "python", ".rs": "rust", ".toml": "toml", ".md": "markdown",
            ".cfg": "ini", ".txt": "text", "Makefile": "makefile"}


def _lang(path: str) -> str:
    base = os.path.basename(path)
    if base in EXT_LANG:
        return EXT_LANG[base]
    return EXT_LANG.get(os.path.splitext(path)[1], "text")


def _collect() -> list[dict]:
    files = []
    seen = set()

    allow_ext = {".py", ".rs", ".toml", ".md"}
    allow_name = {"Makefile", "requirements.txt"}

    def add(rel):
        full = os.path.join(ROOT, rel)
        if not os.path.isfile(full) or rel in seen:
            return
        if "build_site" in rel or rel.endswith("code-data.js"):
            return
        base = os.path.basename(rel)
        if os.path.splitext(rel)[1] not in allow_ext and base not in allow_name:
            return   # source only -- no csv/gif/png/etc.
        try:
            code = open(full, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            return
        seen.add(rel)
        files.append({"path": rel, "lang": _lang(rel), "code": code,
                      "loc": code.count("\n") + 1, "bytes": len(code)})

    for d in INCLUDE_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _, names in os.walk(base):
            if "__pycache__" in dirpath or "/target" in dirpath:
                continue
            for n in sorted(names):
                if n.endswith((".pyc",)):
                    continue
                add(os.path.relpath(os.path.join(dirpath, n), ROOT))
    for f in INCLUDE_FILES:
        add(f)

    files.sort(key=lambda x: x["path"])
    return files


def _tree(files):
    """Nested dict tree for the sidebar."""
    root = {}
    for f in files:
        parts = f["path"].split("/")
        node = root
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node.setdefault("__files__", []).append(
            {"name": parts[-1], "path": f["path"], "lang": f["lang"], "loc": f["loc"]})
    return root


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    files = _collect()
    tree = _tree(files)

    loc = sum(f["loc"] for f in files)
    langs = {}
    for f in files:
        langs[f["lang"]] = langs.get(f["lang"], 0) + f["loc"]
    tests = sum(f["code"].count("def test_") for f in files if f["path"].startswith("tests/"))

    with open(os.path.join(OUT, "code-data.js"), "w", encoding="utf-8") as fh:
        fh.write("window.CODEBASE = ")
        json.dump({"tree": tree, "files": files}, fh, ensure_ascii=False)
        fh.write(";")

    stats = {
        "files": len(files), "loc": loc, "tests": tests,
        "langs": langs,
        "py_loc": langs.get("python", 0), "rs_loc": langs.get("rust", 0),
        "modules": len([f for f in files if f["path"].endswith("__init__.py")]),
    }
    with open(os.path.join(OUT, "stats.js"), "w", encoding="utf-8") as fh:
        fh.write("window.STATS = ")
        json.dump(stats, fh)
        fh.write(";")

    print(f"exhibit: {len(files)} files, {loc:,} LOC, {tests} tests")
    print(f"  python {stats['py_loc']:,} | rust {stats['rs_loc']:,}")
    print(f"  wrote {OUT}/code-data.js ({os.path.getsize(OUT + '/code-data.js')//1024} KB), stats.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
