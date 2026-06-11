#!/usr/bin/env python3
"""
VEP Cross-platform Environment Fingerprint Collector
采集环境指纹用于诊断跨平台评测结果差异
"""
import sys
import os
import platform
import subprocess
import json
import hashlib
import tempfile
import shutil
from pathlib import Path

def run_cmd(cmd, default="unavailable"):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else default
    except Exception:
        return default

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return "missing"
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"error: {e}"

def check_case_sensitivity():
    tmpdir = tempfile.mkdtemp()
    try:
        test_upper = os.path.join(tmpdir, "CaseTest.txt")
        test_lower = os.path.join(tmpdir, "casetest.txt")
        with open(test_upper, 'w') as f:
            f.write("test")
        case_insensitive = os.path.exists(test_lower)
        return "case-insensitive" if case_insensitive else "case-sensitive"
    except Exception as e:
        return f"error: {e}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def collect_fingerprint():
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    fingerprint = {
        "platform": {
            "system": platform.system(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "filesystem": {
            "case_sensitivity": check_case_sensitivity(),
            "cwd": os.getcwd(),
            "cwd_realpath": os.path.realpath(os.getcwd()),
        },
        "locale": {
            "LANG": os.environ.get("LANG", "unset"),
            "LC_ALL": os.environ.get("LC_ALL", "unset"),
        },
        "tools": {
            "java_version": run_cmd("java -version 2>&1 | head -1"),
            "mvn_version": run_cmd("mvn -version 2>&1 | head -1"),
            "python_path": sys.executable,
            "codeql_version": run_cmd("codeql version 2>&1"),
            "godel_version": run_cmd("godel version 2>&1"),
        },
        "git": {
            "commit": run_cmd("git rev-parse HEAD"),
            "branch": run_cmd("git rev-parse --abbrev-ref HEAD"),
            "status": run_cmd("git status --short"),
            "dirty": bool(run_cmd("git status --short")),
        },
        "checksums": {
            "expectedresults": compute_sha256("expectedresults-1.2.csv"),
            "cwe_manifest": compute_sha256("configs/cwe_manifest.yml"),
            "eval_findings_py": compute_sha256("scripts/evaluation/eval_findings.py"),
            "evaluator_py": compute_sha256("scripts/evaluation/evaluator.py"),
            "findings_py": compute_sha256("scripts/evaluation/findings.py"),
            "ground_truth_py": compute_sha256("scripts/evaluation/ground_truth.py"),
            "metrics_py": compute_sha256("scripts/evaluation/metrics.py"),
        }
    }

    return fingerprint

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Collect VEP environment fingerprint")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    fingerprint = collect_fingerprint()

    with open(args.out, 'w') as f:
        json.dump(fingerprint, f, indent=2, ensure_ascii=False)

    print(f"✅ Environment fingerprint saved to: {args.out}")
    print(f"Platform: {fingerprint['platform']['system']}")
    print(f"Filesystem: {fingerprint['filesystem']['case_sensitivity']}")
    print(f"Git commit: {fingerprint['git']['commit'][:8]}")

if __name__ == "__main__":
    main()
