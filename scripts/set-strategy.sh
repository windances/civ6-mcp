#!/usr/bin/env bash
# Ad-hoc strategy injection for Git Bash (and any POSIX shell).
#
# Equivalent to scripts/set-strategy.ps1, for when PowerShell refuses to run
# scripts. It also sidesteps Windows command-line encoding entirely, so it is the
# safer choice for non-ASCII strategy text.
#
# Usage:
#   bash scripts/set-strategy.sh -Show
#   bash scripts/set-strategy.sh -File my-strategy.md
#   bash scripts/set-strategy.sh -Text "Pursue a science victory."
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill="$project_root/.dsh/skills/civ6-orchestrator/SKILL.md"

fail() { echo "error: $*" >&2; exit 2; }

[ -f "$skill" ] || fail "SKILL.md not found at $skill"
grep -q '<!-- DIRECTIVE:BEGIN' "$skill" || fail 'SKILL.md has no DIRECTIVE marker block'

mode=""
value=""
while [ $# -gt 0 ]; do
  case "$1" in
    -Show|--show)  mode=show; shift ;;
    -File|--file)  mode=file; value="${2:-}"; shift 2 ;;
    -Text|--text)  mode=text; value="${2:-}"; shift 2 ;;
    *) fail "unknown argument: $1" ;;
  esac
done
[ -n "$mode" ] || fail 'usage: set-strategy.sh -Show | -File <path> | -Text "<strategy>"'

if [ "$mode" = show ]; then
  awk '/<!-- DIRECTIVE:BEGIN/{f=1;next} /<!-- DIRECTIVE:END -->/{f=0} f' "$skill"
  exit 0
fi

tmp_text="$(mktemp)"
trap 'rm -f "$tmp_text"' EXIT

if [ "$mode" = file ]; then
  [ -f "$value" ] || fail "strategy file not found: $value"
  cat "$value" > "$tmp_text"
else
  case "$value" in *[!\ ]*) ;; *) fail 'strategy text is empty' ;; esac
  printf '%s\n' "$value" > "$tmp_text"
fi

tmp_out="$(mktemp)"
awk -v dfile="$tmp_text" '
  /<!-- DIRECTIVE:BEGIN/ { print; while ((getline l < dfile) > 0) print l; skip=1; next }
  /<!-- DIRECTIVE:END -->/ { skip=0 }
  !skip { print }
' "$skill" > "$tmp_out" && mv "$tmp_out" "$skill"

echo "Ad-hoc strategy injected into the directive block."
echo "The agent sees it on the next end_turn - no restart needed."
