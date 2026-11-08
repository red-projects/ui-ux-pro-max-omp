set shell := ["bash", "-uc"]

default:
    @just --list

# Set up runtime permissions, ~/.local/bin symlink, and verify runner
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 -c 'import sys; assert sys.version_info >= (3, 8), "Python 3.8+ required"'
    chmod +x bin/ui-ux-run omp/adapt.py omp/verify.py omp/self_audit.py
    mkdir -p ~/.local/bin
    ln -sf "$(pwd)/bin/ui-ux-run" ~/.local/bin/omp-ui-ux-run
    bin/ui-ux-run --help >/dev/null
    echo "✓ OMP UI-UX-PRO-MAX runtime setup complete (runner: ~/.local/bin/omp-ui-ux-run)."

# Adapt skill files for OMP runtime compatibility (deterministic, idempotent)
adapt:
    python3 omp/adapt.py

# Run the 5-gate verification suite
test:
    python3 omp/verify.py

# Run self-audit with 5 falsification probes and generate audit report
self-audit:
    python3 omp/self_audit.py

# Safely fetch upstream, merge into current branch, adapt and verify
sync-upstream ref="main":
    bash omp/sync-upstream.sh "{{ref}}"

# Link the 7 skills into target project's .omp/skills/ directory
link-project target_dir=".":
    #!/usr/bin/env bash
    set -euo pipefail
    dest="{{target_dir}}/.omp/skills"
    mkdir -p "$dest"
    for skill_path in .claude/skills/*; do
        if [ -d "$skill_path" ]; then
            name="$(basename "$skill_path")"
            ln -sfn "$(pwd)/$skill_path" "$dest/$name"
            echo "Linked $name -> $dest/$name"
        fi
    done
    echo "✓ Linked skills into $dest"
