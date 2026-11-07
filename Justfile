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

# Fetch upstream commits and verify suite
sync-upstream ref="main":
    #!/usr/bin/env bash
    set -euo pipefail
    git fetch upstream
    echo "Upstream fetched. Comparing with upstream/{{ref}}:"
    git log --oneline -n 5 "upstream/{{ref}}" || true
    python3 omp/adapt.py
    python3 omp/verify.py
    python3 omp/self_audit.py

# Link the 7 skills into target project's .claude/skills/ directory
link-project target_dir=".":
    #!/usr/bin/env bash
    set -euo pipefail
    dest="{{target_dir}}/.claude/skills"
    mkdir -p "$dest"
    for skill_path in .claude/skills/*; do
        if [ -d "$skill_path" ]; then
            name="$(basename "$skill_path")"
            ln -sfn "$(pwd)/$skill_path" "$dest/$name"
            echo "Linked $name -> $dest/$name"
        fi
    done
    echo "✓ Linked skills into $dest"
