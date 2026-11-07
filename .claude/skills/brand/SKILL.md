---
name: brand
description: "Brand identity design: visual systems, color palettes, typography rules, brand voice, and design token synchronization."
argument-hint: "[update|review|create] [args]"
metadata:
  author: claudekit
  version: "1.0.0"
---

# Brand

Brand identity, voice, messaging, asset management, and consistency frameworks.

## When to Use

- Brand voice definition and content tone guidance
- Visual identity standards and style guide development
- Messaging framework creation
- Brand consistency review and audit
- Asset organization, naming, and approval
- Color palette management and typography specs

## Script Paths

Script paths in this skill and its `references/` are relative to the directory that contains this SKILL.md, not to the project: `scripts/<file>` is this skill's own `scripts/` folder, and `../<skill>/scripts/<file>` is a sibling sub-skill installed alongside it. Build the full path from that directory (Claude Code reports it as the skill's base directory when the skill loads) and keep the working directory at the project root — the scripts read and write project files such as `docs/brand-guidelines.md`, `assets/design-tokens.json` or `src/` relative to it.

## Quick Start

**Inject brand context into prompts:**
```bash
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/inject-brand-context.cjs
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/inject-brand-context.cjs --json
```

**Validate an asset:**
```bash
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/validate-asset.cjs <asset-path>
```

**Extract/compare colors:**
```bash
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/extract-colors.cjs --palette
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/extract-colors.cjs <image-path>
```

## Brand Sync Workflow

```bash
# 1. Edit docs/brand-guidelines.md (or use /brand update)
# 2. Sync to design tokens
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/sync-brand-to-tokens.cjs
# 3. Verify
bun /home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/inject-brand-context.cjs --json | head -20
```

The sync stops when it detects existing token files, `:root` custom properties
or Tailwind v4 `@theme` variables in common CSS entry points and their local
CSS imports, or Tailwind theme colors and presets. Review the reported source
before proceeding. If the detected files are the managed
`assets/design-tokens.*` outputs from an earlier sync and replacing them is
intentional, re-run with `--force`.

**Files synced:**
- `docs/brand-guidelines.md` → Source of truth
- `assets/design-tokens.json` → Token definitions
- `assets/design-tokens.css` → CSS variables

## Subcommands

| Subcommand | Description | Reference |
|------------|-------------|-----------|
| `update` | Update brand identity and sync to all design systems | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/update.md` |

## References

| Topic | File |
|-------|------|
| Voice Framework | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/voice-framework.md` |
| Visual Identity | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/visual-identity.md` |
| Messaging | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/messaging-framework.md` |
| Consistency | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/consistency-checklist.md` |
| Guidelines Template | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/brand-guideline-template.md` |
| Asset Organization | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/asset-organization.md` |
| Color Management | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/color-palette-management.md` |
| Typography | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/typography-specifications.md` |
| Logo Usage | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/logo-usage-rules.md` |
| Approval Checklist | `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/references/approval-checklist.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/inject-brand-context.cjs` | Extract brand context for prompt injection |
| `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/sync-brand-to-tokens.cjs` | Sync brand-guidelines.md → design-tokens.json/css |
| `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/validate-asset.cjs` | Validate asset naming, size, format |
| `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/scripts/extract-colors.cjs` | Extract and compare colors against palette |

## Templates

| Template | Purpose |
|----------|---------|
| `/home/konstantin/.local/share/omp-ui-ux-pro-max/.claude/skills/brand/templates/brand-guidelines-starter.md` | Complete starter template for new brands |

## Routing

1. Parse subcommand from `$ARGUMENTS` (first word)
2. Load corresponding `references/{subcommand}.md`
3. Execute with remaining arguments
