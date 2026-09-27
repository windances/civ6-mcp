#!/usr/bin/env bash
# Add, retire and inspect the temporary tasks in prompts/tasks/tmp/ - the bash twin of
# scripts/temp-task.cmd, for Git Bash and any POSIX shell.
#
# Usage (from the project root):
#   bash scripts/temp-task.sh status
#   bash scripts/temp-task.sh add --title "take Brussels: analysis, staging, assault" \
#       --instruction @.tmp/instruction.txt \
#       --why "take the city-state Brussels on the human's instruction" \
#       --done-when @.tmp/done-when.txt --overrides @.tmp/overrides.txt --scope @.tmp/scope.txt \
#       --body-file .tmp/body.md
#   bash scripts/temp-task.sh retire 021 --expired --turn 270 --note "..."
#
# It is exactly `python scripts/temp-task.py "$@"`: the task file, the register row and AGENTS.md's
# IN FORCE NOW line are written together, the mandatory text gate and tests/test_temp_tasks.py run,
# and the commit follows only when both are green.
#
# On non-ASCII: in Git Bash this route is the safest place for Chinese instruction text to survive,
# because the argument crosses through msys's UTF-8 conversion instead of the console code page.
# `--instruction @file` remains the belt-and-braces form, and the reasoning is in
# SETUP-WINDOWS.md section 11.
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python_bin=""
for candidate in \
    "$project_root/.venv/Scripts/python.exe" \
    "$project_root/.venv/bin/python" \
    python3 \
    python
do
    if [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; then
        python_bin="$candidate"
        break
    fi
done

if [ -z "$python_bin" ]; then
    echo "error: no python interpreter found (looked in .venv/Scripts, .venv/bin and \$PATH)" >&2
    exit 2
fi

exec "$python_bin" "$project_root/scripts/temp-task.py" "$@"
