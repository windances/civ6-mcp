#!/usr/bin/env bash
set -euo pipefail

# See run-dsh-headless.sh: this project is Windows-native and must not run under
# WSL (no Linux Node, and WSL2 networking can lock up the game's tuner).
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  {
    echo "error: refusing to run under WSL."
    echo
    echo "  Use Git Bash (Windows-native) instead:"
    echo "    'C:\\Program Files\\Git\\bin\\bash.exe'"
    echo "  or from PowerShell:"
    echo "    npm run dsh:web:win"
  } >&2
  exit 2
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dsh_bin="${project_root}/node_modules/.bin/dsh"

if [[ ! -x "${dsh_bin}" || ! -x "${project_root}/.tools/bin/uv" ]]; then
  echo "Dependencies are missing. Run: npm run bootstrap" >&2
  exit 2
fi

cd "${project_root}"
export DSH_HOME="${project_root}/.dsh-home"
export DSH_TELEMETRY_MODE="${DSH_TELEMETRY_MODE:-DISABLED}"
exec "${dsh_bin}" --profile web --patch "${project_root}/dsh/civ6.cordis.yml" --no-open
