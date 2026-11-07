#!/usr/bin/env python3
"""
Self-audit and falsification probe harness for OMP (ui-ux-pro-max).

Probes:
- Probe 1: Invalid Domain Rejection (exits non-zero via argparse, no Traceback)
- Probe 2: Out-of-Tree Execution from /tmp (cwd="/tmp", rc==0, valid JSON)
- Probe 3: Special Characters & RTL Filtering (--rtl full, valid JSON, every result rtl_level=="full")
- Probe 4: Zero Orchestrator Context Bloat (0 symlinks/dirs in ~/.omp/agent/skills from ui-ux-pro-max)
- Probe 5: Idempotency Check (re-running adapt.py modifies 0 files)

Writes structured receipt to omp/audit-report.json and exits 0 only on full PASS.
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = REPO_ROOT / "omp" / "audit-report.json"
SYMLINK_RUNNER = Path.home() / ".local" / "bin" / "omp-ui-ux-run"
FALLBACK_RUNNER = REPO_ROOT / "bin" / "ui-ux-run"


def get_runner() -> str:
    if SYMLINK_RUNNER.is_file() and os.access(SYMLINK_RUNNER, os.X_OK):
        return str(SYMLINK_RUNNER)
    return str(FALLBACK_RUNNER)


def check_probe1_invalid_domain() -> dict:
    runner = get_runner()
    cmd = [runner, "test", "--domain", "invalid_domain_xyz"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)

    if res.returncode == 0:
        return {
            "status": "FAIL",
            "detail": f"Expected non-zero exit for invalid domain, got {res.returncode}",
        }

    combined = (res.stdout + res.stderr)
    if "Traceback (most recent call last)" in combined:
        return {
            "status": "FAIL",
            "detail": f"Unhandled Python traceback detected in stderr/stdout:\n{combined}",
        }

    if "invalid choice" not in combined and "error:" not in combined:
        return {
            "status": "FAIL",
            "detail": f"Expected argparse error message, got:\n{combined}",
        }

    return {
        "status": "PASS",
        "detail": f"Clean argparse error rejection with exit code {res.returncode}",
    }


def check_probe2_out_of_tree() -> dict:
    runner = get_runner()
    cmd = [runner, "bento", "--domain", "style", "--json"]
    res = subprocess.run(cmd, cwd="/tmp", capture_output=True, text=True)

    if res.returncode != 0:
        return {
            "status": "FAIL",
            "detail": f"Execution with cwd=/tmp failed with code {res.returncode}: {res.stderr}",
        }

    try:
        data = json.loads(res.stdout)
    except Exception as exc:
        return {
            "status": "FAIL",
            "detail": f"Failed to parse JSON output: {exc}\nStdout: {res.stdout[:300]}",
        }

    count = data.get("count", 0)
    if count < 1:
        return {
            "status": "FAIL",
            "detail": f"Expected count >= 1 for bento style query, got {count}",
        }

    return {
        "status": "PASS",
        "detail": f"Out-of-tree execution from /tmp succeeded: {count} results returned",
    }


def check_probe3_rtl_filtering() -> dict:
    runner = get_runner()
    cmd = [runner, "dashboard", "--domain", "style", "--rtl", "full", "--json"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)

    if res.returncode != 0:
        return {
            "status": "FAIL",
            "detail": f"RTL filtering query failed with code {res.returncode}: {res.stderr}",
        }

    try:
        data = json.loads(res.stdout)
    except Exception as exc:
        return {
            "status": "FAIL",
            "detail": f"Output is not valid JSON: {exc}\nStdout: {res.stdout[:300]}",
        }

    results = data.get("results", [])
    for idx, item in enumerate(results):
        level = item.get("rtl_level")
        if level != "full":
            return {
                "status": "FAIL",
                "detail": f"Result #{idx} has rtl_level={level!r}, expected 'full'",
            }

    # Also perform a non-vacuous check on a style query known to match full RTL
    cmd_non_vacuous = [runner, "minimalism", "--domain", "style", "--rtl", "full", "--json"]
    res_nv = subprocess.run(cmd_non_vacuous, cwd=REPO_ROOT, capture_output=True, text=True)
    if res_nv.returncode != 0:
        return {
            "status": "FAIL",
            "detail": f"Non-vacuous RTL check failed with code {res_nv.returncode}: {res_nv.stderr}",
        }

    try:
        data_nv = json.loads(res_nv.stdout)
    except Exception as exc:
        return {
            "status": "FAIL",
            "detail": f"Non-vacuous output is not valid JSON: {exc}",
        }

    results_nv = data_nv.get("results", [])
    if not results_nv:
        return {
            "status": "FAIL",
            "detail": "Non-vacuous RTL check returned 0 results for 'minimalism'",
        }

    for idx, item in enumerate(results_nv):
        if item.get("rtl_level") != "full":
            return {
                "status": "FAIL",
                "detail": f"Non-vacuous result #{idx} has rtl_level={item.get('rtl_level')!r}",
            }

    return {
        "status": "PASS",
        "detail": f"RTL full filtering verified (dashboard: {len(results)} items, minimalism: {len(results_nv)} items all rtl_level=='full')",
    }


def check_probe4_zero_context_bloat() -> dict:
    omp_skills_dir = Path.home() / ".omp" / "agent" / "skills"
    if not omp_skills_dir.exists():
        return {
            "status": "PASS",
            "detail": f"{omp_skills_dir} does not exist (zero bloat by default)",
        }

    violations: list[str] = []
    for item in omp_skills_dir.iterdir():
        name = item.name
        resolved_target = str(item.resolve()) if item.is_symlink() else ""
        if "ui-ux-pro-max" in name or "ui-ux-pro-max" in resolved_target:
            violations.append(f"{item} -> {resolved_target}")

    if violations:
        return {
            "status": "FAIL",
            "detail": f"Found {len(violations)} orchestrator skill leaks: {violations}",
        }

    return {
        "status": "PASS",
        "detail": "Zero symlinks or directories from omp-ui-ux-pro-max in ~/.omp/agent/skills",
    }


def check_probe5_adapt_idempotency() -> dict:
    cmd = [sys.executable, str(REPO_ROOT / "omp" / "adapt.py")]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)

    if res.returncode != 0:
        return {
            "status": "FAIL",
            "detail": f"adapt.py failed with code {res.returncode}: {res.stderr}",
        }

    stdout = res.stdout.strip()
    if "0 modified" not in stdout:
        return {
            "status": "FAIL",
            "detail": f"adapt.py was not idempotent, reported modifications:\n{stdout}",
        }

    return {
        "status": "PASS",
        "detail": f"Idempotency verified: re-running adapt.py modified 0 files ({stdout})",
    }


def main() -> int:
    probes = [
        ("probe_1_invalid_domain_rejection", check_probe1_invalid_domain),
        ("probe_2_out_of_tree_execution", check_probe2_out_of_tree),
        ("probe_3_rtl_filtering", check_probe3_rtl_filtering),
        ("probe_4_zero_orchestrator_context_bloat", check_probe4_zero_context_bloat),
        ("probe_5_adapt_idempotency", check_probe5_adapt_idempotency),
    ]

    results: dict[str, dict] = {}
    passed = 0
    failed = 0

    print("=== OMP UI-UX-PRO-MAX SELF-AUDIT ===")
    for probe_id, func in probes:
        try:
            outcome = func()
        except Exception as exc:
            outcome = {"status": "FAIL", "detail": f"Unexpected exception: {exc}"}

        results[probe_id] = outcome
        status = outcome.get("status", "FAIL")
        detail = outcome.get("detail", "")
        print(f"[{status}] {probe_id}: {detail}")

        if status == "PASS":
            passed += 1
        else:
            failed += 1

    report = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(REPO_ROOT),
        "results": results,
        "summary": {
            "total": len(probes),
            "passed": passed,
            "failed": failed,
        },
    }

    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nAudit receipt written to: {REPORT_FILE}")
    print(f"Summary: {passed}/{len(probes)} passed, {failed} failed.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
