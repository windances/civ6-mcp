#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dsh_bin="${project_root}/node_modules/.bin/dsh"

if [[ ! -x "${dsh_bin}" ]]; then
  echo "DSH is not installed. Run: npm run bootstrap" >&2
  exit 2
fi

cd "${project_root}"
export DSH_HOME="${project_root}/.dsh-home"
export DSH_TELEMETRY_MODE="DISABLED"
exec "${dsh_bin}" --profile headless --patch "${project_root}/dsh/civ6.cordis.yml" --dump-config
