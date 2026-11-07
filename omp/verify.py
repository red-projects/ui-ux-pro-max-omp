#!/usr/bin/env python3
"""
Verification gate runner for OMP (ui-ux-pro-max).

5 strict verification gates:
- Gate 1: Frontmatter & Byte Budget (13 SKILL.md, name/desc, <=300 bytes, no CLAUDE_PLUGIN_ROOT, no node host-path)
- Gate 2: Negative Byte Control (301-byte string raises ValueError via validate_description)
- Gate 3: Upstream Data & Core Integrity (git diff main -- data, scripts, src, cli/assets/scripts)
- Gate 4: BM25 Multi-Domain Execution (5 domains, rc==0, valid JSON, count >= 1)
- Gate 5: Design System Generator (--design-system -p "FinFlow" --json, rc==0, expected keys)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "omp"))

from adapt import (  # noqa: E402
    MAX_DESC_BYTES,
    skill_files,
    validate_description,
)

SYMLINK_RUNNER = Path.home() / ".local" / "bin" / "omp-ui-ux-run"
FALLBACK_RUNNER = REPO_ROOT / "bin" / "ui-ux-run"


def get_runner() -> str:
    if SYMLINK_RUNNER.is_file() and os.access(SYMLINK_RUNNER, os.X_OK):
        return str(SYMLINK_RUNNER)
    return str(FALLBACK_RUNNER)


def parse_frontmatter(content: str) -> dict[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing frontmatter opening '---'")
    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx == -1:
        raise ValueError("Missing frontmatter closing '---'")

    fm: dict[str, str] = {}
    for line in lines[1:closing_idx]:
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def run_gate1() -> bool:
    print("--- Gate 1: Frontmatter & Byte Budget ---")
    files = skill_files()
    if len(files) != 13:
        print(f"FAIL: Expected 13 skill files, found {len(files)}")
        return False

    for sf in files:
        text = sf.read_text(encoding="utf-8")
        if "${CLAUDE_PLUGIN_ROOT}" in text:
            print(f"FAIL: {sf} contains ${{CLAUDE_PLUGIN_ROOT}}")
            return False
        if re.search(r"\bnode\s+/home/konstantin/", text):
            print(f"FAIL: {sf} contains node invocation with host path (Bun required)")
            return False
        try:
            fm = parse_frontmatter(text)
        except Exception as exc:
            print(f"FAIL: {sf} frontmatter error: {exc}")
            return False

        if "name" not in fm or "description" not in fm:
            print(f"FAIL: {sf} missing 'name' or 'description' in frontmatter")
            return False

        if fm["name"] != sf.parent.name:
            print(f"FAIL: {sf} name {fm['name']!r} does not match directory {sf.parent.name!r}")
            return False

        desc_bytes = len(fm["description"].encode("utf-8"))
        if not (0 < desc_bytes <= MAX_DESC_BYTES):
            print(f"FAIL: {sf} description length {desc_bytes} not in 1..{MAX_DESC_BYTES}")
            return False

    print(f"PASS: All 13 skills verified (name+desc present, 0 < bytes <= {MAX_DESC_BYTES}, 0 plugin-root refs, 0 node host-path refs)")
    return True


def run_gate2() -> bool:
    print("--- Gate 2: Negative Byte Control ---")
    valid_300 = "a" * 300
    invalid_301 = "a" * 301

    # 300 bytes must pass without raising
    try:
        validate_description(valid_300)
    except Exception as exc:
        print(f"FAIL: validate_description raised on 300-byte string: {exc}")
        return False

    # 301 bytes must raise ValueError
    try:
        validate_description(invalid_301)
        print("FAIL: validate_description accepted 301-byte string without ValueError")
        return False
    except ValueError:
        pass
    except Exception as exc:
        print(f"FAIL: validate_description raised {type(exc).__name__} instead of ValueError: {exc}")
        return False

    print("PASS: Negative byte control confirmed: 301-byte string correctly rejected with ValueError")
    return True


def run_gate3() -> bool:
    print("--- Gate 3: Upstream Data & Core Integrity ---")
    protected_paths = [
        ".claude/skills/ui-ux-pro-max/data/",
        ".claude/skills/ui-ux-pro-max/scripts/",
        "src/",
        "cli/assets/scripts/",
    ]
    cmd = ["git", "diff", "main", "--"] + protected_paths
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: git diff returned {res.returncode}: {res.stderr}")
        return False

    diff_lines = res.stdout.strip()
    if diff_lines:
        print(f"FAIL: Upstream data/scripts modified relative to main:\n{diff_lines[:500]}")
        return False

    print(f"PASS: 0 diff lines relative to main across {len(protected_paths)} protected directories")
    return True


def run_gate4() -> bool:
    print("--- Gate 4: BM25 Multi-Domain Execution ---")
    runner = get_runner()
    domain_queries = {
        "style": "dashboard",
        "color": "dashboard",
        "typography": "dashboard",
        "ux": "accessibility",
        "chart": "dashboard",
    }

    for domain, query in domain_queries.items():
        cmd = [runner, query, "--domain", domain, "--json"]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FAIL: Domain {domain!r} query {query!r} failed with code {res.returncode}: {res.stderr}")
            return False

        try:
            data = json.loads(res.stdout)
        except Exception as exc:
            print(f"FAIL: Domain {domain!r} output is not valid JSON: {exc}\n{res.stdout[:300]}")
            return False

        count = data.get("count", 0)
        if count < 1:
            print(f"FAIL: Domain {domain!r} returned count={count} (expected >= 1)")
            return False

        if data.get("domain") != domain:
            print(f"FAIL: Domain {domain!r} response has domain={data.get('domain')!r}")
            return False

    print("PASS: BM25 queries across 5 domains (style, color, typography, ux, chart) succeeded with count >= 1")
    return True


def run_gate5() -> bool:
    print("--- Gate 5: Design System Generator ---")
    runner = get_runner()
    cmd = [runner, "fintech neobank", "--design-system", "-p", "FinFlow", "--json"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: Design system generator failed with code {res.returncode}: {res.stderr}")
        return False

    try:
        data = json.loads(res.stdout)
    except Exception as exc:
        print(f"FAIL: Design system output is not valid JSON: {exc}\n{res.stdout[:300]}")
        return False

    if "design_system" not in data or "persistence" not in data:
        print(f"FAIL: Missing top-level keys in design system output: {list(data.keys())}")
        return False

    ds = data["design_system"]
    if not isinstance(ds, dict):
        print(f"FAIL: 'design_system' field is not a dict: {type(ds)}")
        return False

    required_ds_keys = ["project_name", "category", "pattern", "style", "colors", "typography"]
    missing = [k for k in required_ds_keys if k not in ds]
    if missing:
        print(f"FAIL: Missing expected design system sub-keys: {missing}")
        return False

    if ds.get("project_name") != "FinFlow":
        print(f"FAIL: Expected project_name 'FinFlow', got {ds.get('project_name')!r}")
        return False

    print("PASS: Design system generated for 'FinFlow' with valid schema and expected top-level keys")
    return True


def main() -> int:
    gates = [
        ("Gate 1", run_gate1),
        ("Gate 2", run_gate2),
        ("Gate 3", run_gate3),
        ("Gate 4", run_gate4),
        ("Gate 5", run_gate5),
    ]

    failed = []
    for name, func in gates:
        try:
            ok = func()
        except Exception as exc:
            print(f"FAIL: {name} raised unexpected exception: {exc}")
            ok = False
        if not ok:
            failed.append(name)
        print()

    if failed:
        print(f"VERIFICATION FAILED: {len(failed)} of {len(gates)} gates failed: {', '.join(failed)}")
        return 1

    print(f"ALL {len(gates)} GATES PASSED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
