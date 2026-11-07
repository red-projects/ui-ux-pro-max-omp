#!/usr/bin/env python3
"""
Deterministic skill adapter for OMP (ui-ux-pro-max).

- Rewrites every SKILL.md frontmatter description to a fixed, <=300-byte UTF-8 string (Pillar 15).
- Rewrites the `${CLAUDE_PLUGIN_ROOT}/.../search.py` launcher forms to the canonical `omp-ui-ux-run`.
- Rewrites relative `references/x.md`, `scripts/...` and `../<skill>/scripts/...` links of the
  installed `.claude/skills` tree to absolute canonical paths (CWD-independent), in both
  `SKILL.md` and every `<skill>/references/*.md`.
- Replaces `${CLAUDE_PLUGIN_ROOT}` with the canonical repo root and `node <host-path>` with
  `bun <host-path>` in reference markdown (no Node runtime in this install).
- Never touches `.csv` data or `.py` scripts: only markdown is written.
- Fully idempotent: writes only when the content actually changes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLED_SKILLS = REPO_ROOT / ".claude" / "skills"
CLI_SKILLS = REPO_ROOT / "cli" / "assets" / "skills"
SKILL_DIRS = (INSTALLED_SKILLS, CLI_SKILLS)

MAX_DESC_BYTES = 300

DESCRIPTIONS = {
    "ui-ux-pro-max": "Design intelligence engine (146k stars): 80 UI styles, 192 color palettes (60-30-10), 74 font pairings, 119 UX/WCAG rules, 22 tech stacks.",
    "design-system": "Generate complete design systems and tokens: 60-30-10 palettes, typography scales, spacing grids, shadows, and token validators.",
    "ui-styling": "UI styling guide: Tailwind CSS, shadcn/ui components, CSS variables, GSAP motion, dark mode, and interactive component states.",
    "brand": "Brand identity design: visual systems, color palettes, typography rules, brand voice, and design token synchronization.",
    "banner-design": "Promotional banner and marketing creative design: visual hierarchy, contrast, CTA placement, and multi-format responsive grids.",
    "slides": "HTML presentation and slide deck engineering: 16:9 layouts, Chart.js data visualization, typography scales, and slide copy logic.",
    "design": "Core UI/UX design workflow: interface composition, icon and logo generation, Corporate Identity Programs (CIP), and usability review.",
}

FRONTMATTER = re.compile(r"\A---\n(.*?\n)---\n", re.S)
DESCRIPTION_LINE = re.compile(r"(?m)^description:[^\n]*(?:\n[ \t]+[^\n]*)*")
NAME_LINE = re.compile(r"(?m)^name:[^\n]*$")

# `python "…/search.py"`, `python3 …/search.py`, bare path — all collapse to the wrapper.
LAUNCHER = re.compile(
    r"""python3?\s+"?\$\{CLAUDE_PLUGIN_ROOT\}/\.claude/skills/ui-ux-pro-max/scripts/search\.py"?"""
    r"""|python3?\s+"?\.claude/skills/ui-ux-pro-max/scripts/search\.py"?"""
    r"""|\$\{CLAUDE_PLUGIN_ROOT\}/\.claude/skills/ui-ux-pro-max/scripts/search\.py"""
)

RELATIVE_LINK = re.compile(
    r"(?<![\w./~-])(?:\.\./([A-Za-z0-9_-]+)/)?"
    r"((?:references|scripts|templates)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)"
)
NODE_INVOCATION = re.compile(r"node (/home/konstantin/[^\s`]+?\.(?:cjs|mjs|js))")


def validate_description(desc: str) -> None:
    """Raise ValueError unless `desc` is non-empty and within the 300-byte UTF-8 budget."""
    if not desc:
        raise ValueError("description is empty")
    size = len(desc.encode("utf-8"))
    if size > MAX_DESC_BYTES:
        raise ValueError(f"description is {size} bytes, limit is {MAX_DESC_BYTES}")


def set_frontmatter(text: str, desc: str) -> str:
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("missing frontmatter")
    block = match.group(1)
    if not NAME_LINE.search(block):
        raise ValueError("frontmatter has no name")
    line = f'description: "{desc}"'
    if DESCRIPTION_LINE.search(block):
        block = DESCRIPTION_LINE.sub(line, block, count=1)
    else:
        block = NAME_LINE.sub(lambda m: f"{m.group(0)}\n{line}", block, count=1)
    return f"---\n{block}---\n" + text[match.end():]


def canonicalize_links(text: str, skill_dir: Path) -> str:
    """Resolve relative reference/script links against the skill dir, but only when the target exists."""

    def repl(match: re.Match[str]) -> str:
        sibling, rel = match.groups()
        base = skill_dir.parent / sibling if sibling else skill_dir
        target = base / rel
        return str(target) if target.is_file() else match.group(0)

    return RELATIVE_LINK.sub(repl, text)


def adapt_skill(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    name = path.parent.name
    desc = DESCRIPTIONS.get(name)
    if desc is None:
        print(f"adapt: no description for unknown skill {name!r}, skipped", file=sys.stderr)
        return False
    validate_description(desc)

    updated = LAUNCHER.sub("omp-ui-ux-run", set_frontmatter(original, desc))
    # cli/assets/skills is a portable distribution copy: absolute host paths would break installs.
    if path.parent.parent == INSTALLED_SKILLS:
        updated = canonicalize_links(updated, path.parent)
        updated = NODE_INVOCATION.sub(r"bun \1", updated)

    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def skill_files() -> list[Path]:
    found: list[Path] = []
    for base in SKILL_DIRS:
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            if "SKILL.md" in filenames:
                found.append(Path(dirpath) / "SKILL.md")
    return sorted(found)


def reference_files() -> list[Path]:
    return sorted(INSTALLED_SKILLS.glob("*/references/*.md"))


def adapt_reference(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    skill_dir = next(p for p in path.parents if p.parent == INSTALLED_SKILLS)
    updated = canonicalize_links(original, skill_dir)
    updated = updated.replace("${CLAUDE_PLUGIN_ROOT}", str(REPO_ROOT))
    updated = NODE_INVOCATION.sub(r"bun \1", updated)

    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    files = skill_files()
    changed = sum(1 for path in files if adapt_skill(path))
    refs = reference_files()
    changed += sum(1 for path in refs if adapt_reference(path))
    print(f"adapt: {len(files)}/13 skills, {len(refs)} references, {changed} modified")
    return 0 if len(files) == 13 else 1


if __name__ == "__main__":
    sys.exit(main())
