#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${project_root}/.venv/bin/python"

if [[ ! -x "${python_bin}" ]]; then
  echo "Python environment is not installed. Run: npm run bootstrap" >&2
  exit 2
fi

cd "${project_root}"
export UV_CACHE_DIR="${project_root}/.uv-cache"
exec "${python_bin}" "${project_root}/scripts/qualify-mcp.py"
