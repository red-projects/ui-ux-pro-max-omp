---
name: slides
description: "HTML presentation and slide deck engineering: 16:9 layouts, Chart.js data visualization, typography scales, and slide copy logic."
argument-hint: "[topic] [slide-count]"
metadata:
  author: claudekit
  version: "1.0.0"
---

# Slides

Strategic HTML presentation design with data visualization.

## When to Use

- Marketing presentations and pitch decks
- Data-driven slides with Chart.js
- Strategic slide design with layout patterns
- Copywriting-optimized presentation content

## Subcommands

| Subcommand | Description | Reference |
|------------|-------------|-----------|
| `create` | Create strategic presentation slides | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/slides/references/create.md` |

## Script Paths

Script paths in this skill and its `references/` are relative to the directory that contains this SKILL.md, not to the project: `scripts/<file>` is this skill's own `scripts/` folder, and `../<skill>/scripts/<file>` is a sibling sub-skill installed alongside it. Build the full path from that directory (Claude Code reports it as the skill's base directory when the skill loads) and keep the working directory at the project root — the scripts read and write project files such as `docs/brand-guidelines.md`, `assets/design-tokens.json` or `src/` relative to it.

## References (Knowledge Base)

| Topic | File |
|-------|------|
| Layout Patterns | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/slides/references/layout-patterns.md` |
| HTML Template | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/slides/references/html-template.md` |
| Copywriting Formulas | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/slides/references/copywriting-formulas.md` |
| Slide Strategies | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/slides/references/slide-strategies.md` |

## Routing

1. Parse subcommand from `$ARGUMENTS` (first word)
2. Load corresponding `references/{subcommand}.md`
3. Execute with remaining arguments
