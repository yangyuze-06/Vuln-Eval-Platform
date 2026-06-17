#!/usr/bin/env python3
"""Read-only diagnostic for CodeFuse/Sparrow DB cross-platform discrepancy.

Compares two coref_java_src.db builds (e.g. Linux vs macOS) and detects the
"JDK type model not loaded" failure mode that demotes method-access expressions
from `*_with_type` to `*_without_type` and collapses `java.*` reference types.

This script is STRICTLY READ-ONLY against the databases. It only writes the
markdown report (--out) and optional data artifacts (--data-dir).

Usage (diff two builds):
  python3 scripts/diagnose_codefuse_db_diff.py \
    --linux dataset/codefuse-db-linux/coref_java_src.db \
    --mac   dataset/codefuse-db-mac/coref_java_src.db \
    --out   reports/codefuse-db-diff-latest.md

Usage (CI gate on a single build, absolute thresholds):
  python3 scripts/diagnose_codefuse_db_diff.py \
    --db dataset/codefuse-db-mac/coref_java_src.db --out reports/codefuse-db-gate.md

Exit code 0 = gate passed, 1 = gate failed (do NOT use that DB for evaluation),
2 = usage / IO error.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

# Sink/source/relay FQNs that taint rules match on. If these are absent the
# corresponding CWE detections silently disappear.
KEY_FQNS = [
    "java.lang.String",            # universal taint relay
    "java.lang.StringBuilder",     # universal taint relay
    "java.lang.StringBuffer",      # universal taint relay
    "java.util.List",              # common container relay
    "java.lang.Runtime",           # CWE-078 sink
    "java.lang.ProcessBuilder",    # CWE-078 sink
    "java.sql.Statement",          # CWE-089 sink
    "java.sql.Connection",         # CWE-089 sink
    "javax.naming.directory.DirContext",  # CWE-090 sink
    "javax.xml.xpath.XPath",       # CWE-643 sink
]

# Gate must see these resolved (fully-qualified) or the DB is unusable.
GATE_REQUIRED_FQNS = ["java.lang.String", "java.util.List", "java.lang.Runtime"]

# A healthy build resolves thousands of java.* reference types. A build that
# failed to load the JDK image drops to tens. 200 is a wide safety margin.
GATE_MIN_JAVA_REFTYPES = 200


def connect_ro(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    # immutable=1 => guaranteed read-only, no locks, no journal writes.
    return sqlite3.connect(f"file:{path}?immutable=1", uri=True)


def scalar(con: sqlite3.Connection, sql: str, args=()) -> int:
    return con.execute(sql, args).fetchone()[0]


def table_names(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def table_counts(con: sqlite3.Connection, tables) -> dict[str, int]:
    out = {}
    for t in tables:
        try:
            out[t] = scalar(con, f'SELECT COUNT(*) FROM "{t}"')
        except sqlite3.Error:
            out[t] = -1
    return out


def fqn_categories(con: sqlite3.Connection) -> dict[str, int]:
    q = lambda where: scalar(  # noqa: E731
        con, f"SELECT COUNT(*) FROM reference_type WHERE {where}")
    return {
        "total_nonnull": q("qualified_name IS NOT NULL"),
        "java.*": q("qualified_name LIKE 'java.%'"),
        "javax.*": q("qualified_name LIKE 'javax.%'"),
        "jakarta.*": q("qualified_name LIKE 'jakarta.%'"),
        "org.owasp.*": q("qualified_name LIKE 'org.owasp.%'"),
        "simple_name": q("qualified_name NOT LIKE '%.%' "
                         "AND qualified_name IS NOT NULL"),
    }


def fqn_present(con: sqlite3.Connection, fqn: str) -> int:
    # Match exact and generic-parameterized forms: `java.util.List` also counts
    # `java.util.List<java.lang.String>`. Raw types are stored parameterized.
    return scalar(
        con,
        "SELECT COUNT(*) FROM reference_type "
        "WHERE qualified_name = ? OR qualified_name LIKE ? || '<%'",
        (fqn, fqn))


def method_access_totals(con: sqlite3.Connection) -> tuple[int, int]:
    w = scalar(con, "SELECT COUNT(*) FROM method_access_expression_with_type")
    wo = scalar(con,
                "SELECT COUNT(*) FROM method_access_expression_without_type")
    return w, wo


def md_table(rows, headers) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def diff_mode(linux: str, mac: str, out: str, data_dir: str) -> int:
    cl, cm = connect_ro(linux), connect_ro(mac)
    lines: list[str] = []
    p = lines.append
    p("# CodeFuse DB Diff (auto-generated)\n")
    p(f"- linux DB: `{linux}`")
    p(f"- mac DB:   `{mac}`\n")

    # --- table set + count diff ---
    lt, mt = table_names(cl), table_names(cm)
    p("## Table set")
    p(f"- linux tables: {len(lt)}, mac tables: {len(mt)}")
    if lt ^ mt:
        p(f"- ONLY linux: {sorted(lt - mt)}")
        p(f"- ONLY mac:   {sorted(mt - lt)}")
    else:
        p("- table sets identical")
    p("")

    common = sorted(lt & mt)
    lc, mc = table_counts(cl, common), table_counts(cm, common)
    diffs = [(t, lc[t], mc[t], mc[t] - lc[t]) for t in common if lc[t] != mc[t]]
    p("## Tables with differing row counts")
    p(md_table(diffs, ["table", "linux", "mac", "delta"]) if diffs
      else "_none_")
    p("")

    # --- FQN categories ---
    fl, fm = fqn_categories(cl), fqn_categories(cm)
    cats = list(fl.keys())
    p("## reference_type FQN categories")
    p(md_table([(k, fl[k], fm[k], fm[k] - fl[k]) for k in cats],
               ["category", "linux", "mac", "delta"]))
    p("")

    # --- key FQN presence ---
    p("## Key sink/source/relay FQN presence")
    p(md_table([(f, fqn_present(cl, f), fqn_present(cm, f)) for f in KEY_FQNS],
               ["qualified_name", "linux", "mac"]))
    p("")

    # --- method_access totals ---
    lw, lwo = method_access_totals(cl)
    mw, mwo = method_access_totals(cm)
    p("## method_access_expression with_type vs without_type")
    p(md_table([("linux", lw, lwo, f"{lw/(lw+lwo):.1%}"),
                ("mac", mw, mwo, f"{mw/(mw+mwo):.1%}")],
               ["build", "with_type", "without_type", "with_type %"]))
    p("")

    # --- linux-only FQN artifact ---
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
        ls = {r[0] for r in cl.execute(
            "SELECT qualified_name FROM reference_type "
            "WHERE qualified_name IS NOT NULL")}
        ms = {r[0] for r in cm.execute(
            "SELECT qualified_name FROM reference_type "
            "WHERE qualified_name IS NOT NULL")}
        only = sorted(x for x in (ls - ms) if "." in x)
        art = os.path.join(data_dir, "linux_only_fqn.txt")
        with open(art, "w") as fh:
            fh.write("\n".join(only) + "\n")
        p(f"- linux-only FQN list written to `{art}` ({len(only)} entries)\n")

    # --- verdict ---
    ratio = mw / lw if lw else 0.0
    java_ok = fm["java.*"] >= GATE_MIN_JAVA_REFTYPES
    ratio_ok = ratio >= 0.95
    verdict = "PASS" if (java_ok and ratio_ok) else "FAIL"
    p("## Verdict")
    p(f"- mac with_type / linux with_type = {ratio:.1%} "
      f"(threshold >= 95%) -> {'ok' if ratio_ok else 'FAIL'}")
    p(f"- mac java.* reference types = {fm['java.*']} "
      f"(threshold >= {GATE_MIN_JAVA_REFTYPES}) -> {'ok' if java_ok else 'FAIL'}")
    p(f"- **{verdict}**")
    if verdict == "FAIL":
        p("- ACTION: mac build lost the JDK type model; "
          "DO NOT use it for evaluation. Rebuild with JAVA_HOME/JDK on the "
          "type-resolution path.")

    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[written] {out}")
    return 0 if verdict == "PASS" else 1


def single_mode(db: str, out: str) -> int:
    con = connect_ro(db)
    lines = [f"# CodeFuse DB Gate (single build)\n", f"- DB: `{db}`\n"]
    fc = fqn_categories(con)
    w, wo = method_access_totals(con)
    lines.append(md_table([(k, fc[k]) for k in fc], ["category", "count"]))
    lines.append("")
    lines.append(f"- method_access with_type={w}, without_type={wo}, "
                 f"with_type %={w/(w+wo):.1%}" if (w + wo) else "- no calls")
    missing = [f for f in GATE_REQUIRED_FQNS if fqn_present(con, f) == 0]
    java_ok = fc["java.*"] >= GATE_MIN_JAVA_REFTYPES
    verdict = "PASS" if (java_ok and not missing) else "FAIL"
    lines.append(f"\n## Verdict: **{verdict}**")
    if missing:
        lines.append(f"- MISSING required FQNs (JDK not loaded): {missing}")
    if not java_ok:
        lines.append(f"- java.* reference types {fc['java.*']} "
                     f"< {GATE_MIN_JAVA_REFTYPES}")
    if verdict == "FAIL":
        lines.append("- ACTION: DO NOT use this DB for evaluation.")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[written] {out}")
    return 0 if verdict == "PASS" else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--linux", help="Linux-built coref_java_src.db")
    ap.add_argument("--mac", help="macOS-built coref_java_src.db")
    ap.add_argument("--db", help="single DB to gate (no baseline)")
    ap.add_argument("--out", default="reports/codefuse-db-diff-latest.md")
    ap.add_argument("--data-dir", default="reports/data")
    a = ap.parse_args()
    try:
        if a.db:
            return single_mode(a.db, a.out)
        if a.linux and a.mac:
            return diff_mode(a.linux, a.mac, a.out, a.data_dir)
        ap.error("provide either --db, or both --linux and --mac")
    except (FileNotFoundError, sqlite3.Error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
