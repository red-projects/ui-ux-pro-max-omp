# OMP UI/UX Pro Max Adaptation & Sync Guide

This directory contains the OMP (Omarchy / OMP Multi-Agent Platform) adaptation layer for `ui-ux-pro-max-skill`.

- **Upstream Repository:** [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (`main`)
- **Downstream Fork:** [red-projects/ui-ux-pro-max-omp](https://github.com/red-projects/ui-ux-pro-max-omp)
- **Active Branch:** `omp-compat`

---

## Transactional Upstream Sync Workflow

To safely ingest new upstream changes without risking regression or unverified commits:

```bash
cd ~/.local/share/omp-ui-ux-pro-max

# 1. Transactional sync: fetches upstream, merges with --no-ff --no-commit,
#    runs adapt/verify/self-audit, and stages adaptation delta if all pass
just sync-upstream main

# 2. Inspect the staged merge and adaptation delta
git diff --cached

# 3. Complete the merge explicitly (never auto-committed or auto-pushed)
git commit -m "chore: sync with upstream main"
git push origin omp-compat

# Alternatively, to cleanly abandon an in-progress or failed sync:
git merge --abort
```

### Transactional Sync Contract
- **Preflight:** Refuses to run on dirty tracked trees (exit code 2) or if `MERGE_HEAD` already exists.
- **Transactional Merge:** Merges using `git merge --no-ff --no-commit`. HEAD is never moved prematurely.
- **Worktree Compatibility:** Uses `git rev-parse --git-path MERGE_HEAD` supporting both standard checkouts and git worktrees.
- **Untracked Collision Safety:** If merge fails due to an untracked file collision, exits 2 without creating a bogus merge state or advising abort.
- **Post-Merge Adaptation & Validation:** Automatically runs `omp/adapt.py`, `omp/verify.py` (5 gates), and `omp/self_audit.py` (5 probes) while merge is staged.
- **Failure Containment:** If any check fails, exits non-zero (exit code 4) leaving `MERGE_HEAD` intact so the operator can inspect or run `git merge --abort`.
- **Staging Delta:** On success, runs `git add -u` staging only tracked adaptation changes so the index matches the worktree (`git diff --quiet`), leaving user untracked files unstaged.
- **Operator Authority:** Never auto-commits and never pushes.
