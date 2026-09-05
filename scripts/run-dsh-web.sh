#!/usr/bin/env bash
set -euo pipefail

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
