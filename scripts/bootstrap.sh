#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_bin="${project_root}/.tools/bin"
uv_bin="${tools_bin}/uv"

mkdir -p "${tools_bin}"

if [[ ! -x "${uv_bin}" ]]; then
  installer="$(mktemp)"
  trap 'rm -f "${installer}"' EXIT
  curl -LsSf https://astral.sh/uv/install.sh -o "${installer}"
  env UV_INSTALL_DIR="${tools_bin}" sh "${installer}"
fi

cd "${project_root}"
npm install
export UV_CACHE_DIR="${project_root}/.uv-cache"
"${uv_bin}" sync --project "${project_root}"
npm run qualify

echo "Bootstrap complete. Start Civ VI, then run:"
echo "  npm run dsh:play -- \"Play one complete turn using the civ6-orchestrator skill.\""
