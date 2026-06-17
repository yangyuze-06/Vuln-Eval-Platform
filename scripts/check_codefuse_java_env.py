#!/usr/bin/env python3
"""Pre-build Java environment gate for CodeFuse/Sparrow databases."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


BREW_PREFIX_RE = re.compile(
    r"^/(?:opt/homebrew|usr/local)/opt/openjdk(?:@\d+)?/?$"
)


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError as exc:
        return {"cmd": cmd, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": "command timed out",
        }


def executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def parse_major_version(output: str) -> int | None:
    match = re.search(r'version "([^"]+)"', output)
    if not match:
        match = re.search(r"\b(?:javac|openjdk|java)\s+([0-9][^\s]*)", output)
    if not match:
        return None
    version = match.group(1)
    first = version.split(".", 1)[0]
    if first == "1":
        parts = version.split(".")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    return int(first) if first.isdigit() else None


def expected_home_for_prefix(java_home: Path) -> Path:
    return java_home / "libexec" / "openjdk.jdk" / "Contents" / "Home"


def recommended_exports(java_home: str) -> list[str]:
    path = Path(java_home)
    recommendations: list[str] = []

    if BREW_PREFIX_RE.match(java_home.rstrip("/")):
        expected = expected_home_for_prefix(path)
        recommendations.append(f'export JAVA_HOME="{expected}"')
        recommendations.append('export PATH="$JAVA_HOME/bin:$PATH"')
        return recommendations

    for prefix in ("/opt/homebrew", "/usr/local"):
        for version in ("21", "17"):
            candidate = Path(prefix) / "opt" / f"openjdk@{version}" / "libexec" / "openjdk.jdk" / "Contents" / "Home"
            if candidate.exists():
                recommendations.append(f'export JAVA_HOME="{candidate}"')
                recommendations.append('export PATH="$JAVA_HOME/bin:$PATH"')
                return recommendations
    return recommendations


def add_result(results: list[dict[str, str]], level: str, message: str, detail: str = "") -> None:
    results.append({"level": level, "message": message, "detail": detail})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate JAVA_HOME before creating CodeFuse/Sparrow Java databases."
    )
    parser.add_argument("--require-version", type=int, choices=(8, 11, 17, 21), help="Require a Java major version.")
    parser.add_argument("--require-modules", action="store_true", help="Fail unless JDK module metadata is present.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable PASS/WARN lines.")
    args = parser.parse_args()

    java_home_raw = os.environ.get("JAVA_HOME", "").strip()
    results: list[dict[str, str]] = []
    evidence: dict[str, Any] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "java_home": java_home_raw,
        "checks": {},
        "commands": {},
        "recommendations": [],
    }

    if not java_home_raw:
        add_result(results, "FAIL", "JAVA_HOME is not set.")
        evidence["recommendations"] = recommended_exports(java_home_raw)
        return finish(args, results, evidence)

    java_home = Path(java_home_raw)
    expected = expected_home_for_prefix(java_home)
    suspicious_brew_prefix = bool(BREW_PREFIX_RE.match(java_home_raw.rstrip("/")))

    if suspicious_brew_prefix:
        add_result(
            results,
            "FAIL",
            "JAVA_HOME points to Homebrew keg prefix, not real JDK home.",
            f"Expected: {expected}",
        )
        evidence["recommendations"] = recommended_exports(java_home_raw)

    paths = {
        "java": java_home / "bin" / "java",
        "javac": java_home / "bin" / "javac",
        "lib_modules": java_home / "lib" / "modules",
        "ct_sym": java_home / "lib" / "ct.sym",
        "jmods": java_home / "jmods",
    }
    evidence["checks"] = {name: str(path) for name, path in paths.items()}

    if not executable(paths["java"]):
        add_result(results, "FAIL", "$JAVA_HOME/bin/java is missing or not executable.", str(paths["java"]))
    if not executable(paths["javac"]):
        add_result(results, "FAIL", "$JAVA_HOME/bin/javac is missing or not executable.", str(paths["javac"]))

    has_modules = paths["lib_modules"].is_file()
    has_ct_sym = paths["ct_sym"].is_file()
    has_jmods = paths["jmods"].is_dir()

    if not has_modules:
        level = "FAIL" if args.require_modules else "WARN"
        add_result(
            results,
            level,
            "Missing $JAVA_HOME/lib/modules, so Sparrow cannot load the JDK type model.",
            str(paths["lib_modules"]),
        )
    if not has_ct_sym:
        add_result(results, "WARN", "Missing $JAVA_HOME/lib/ct.sym.", str(paths["ct_sym"]))
    if not has_jmods:
        level = "FAIL" if args.require_modules else "WARN"
        add_result(results, level, "Missing $JAVA_HOME/jmods directory.", str(paths["jmods"]))

    java_version = run_cmd([str(paths["java"]), "-version"]) if executable(paths["java"]) else None
    javac_version = run_cmd([str(paths["javac"]), "-version"]) if executable(paths["javac"]) else None
    evidence["commands"]["java_version"] = java_version
    evidence["commands"]["javac_version"] = javac_version

    version_text = ""
    if java_version:
        version_text += "\n".join(x for x in (java_version["stdout"], java_version["stderr"]) if x)
    major = parse_major_version(version_text)
    evidence["java_major_version"] = major
    if args.require_version and major != args.require_version:
        add_result(
            results,
            "FAIL",
            f"Java major version is {major or 'unknown'}, expected {args.require_version}.",
        )

    if platform.system() == "Darwin":
        for key, cmd in {
            "java_home_V": ["/usr/libexec/java_home", "-V"],
            "java_home_21": ["/usr/libexec/java_home", "-v", "21"],
            "java_home_17": ["/usr/libexec/java_home", "-v", "17"],
        }.items():
            result = run_cmd(cmd)
            evidence["commands"][key] = result
            if result["returncode"] != 0:
                add_result(results, "INFO", f"{' '.join(cmd)} failed; keeping as discovery evidence.", result["stderr"])

    if not any(item["level"] in {"FAIL", "WARN"} for item in results):
        add_result(results, "PASS", "JAVA_HOME is suitable for CodeFuse/Sparrow JDK type model discovery.")

    if not evidence["recommendations"]:
        evidence["recommendations"] = recommended_exports(java_home_raw)

    return finish(args, results, evidence)


def finish(args: argparse.Namespace, results: list[dict[str, str]], evidence: dict[str, Any]) -> int:
    has_fail = any(item["level"] == "FAIL" for item in results)
    has_warn = any(item["level"] == "WARN" for item in results)
    status = "FAIL" if has_fail else "WARNING" if has_warn else "PASS"
    exit_code = 1 if has_fail else 2 if has_warn else 0
    evidence["status"] = status
    evidence["results"] = results
    evidence["exit_code"] = exit_code

    if args.json:
        print(json.dumps(evidence, indent=2, sort_keys=True))
    elif not args.quiet:
        for item in results:
            print(f"[{item['level']}] {item['message']}")
            if item.get("detail"):
                print(f"       {item['detail']}")
        if evidence.get("recommendations") and status != "PASS":
            print()
            print("Suggested fix:")
            for line in evidence["recommendations"]:
                print(f"       {line}")
        java_version = evidence.get("commands", {}).get("java_version")
        javac_version = evidence.get("commands", {}).get("javac_version")
        if java_version:
            text = "\n".join(x for x in (java_version.get("stdout"), java_version.get("stderr")) if x)
            print(f"\njava -version:\n{text}")
        if javac_version:
            text = "\n".join(x for x in (javac_version.get("stdout"), javac_version.get("stderr")) if x)
            print(f"\njavac -version:\n{text}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
