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

# The first line of an ad-hoc block: see scripts/set-strategy.ps1 (same literal).
ad_hoc_marker='<!-- ad-hoc directive from the human, not a preset: switching presets replaces it -->'

# The directive body SKILL.md carries right now, with any stray BOM stripped.
skill_block() {
  awk '/<!-- DIRECTIVE:BEGIN/{f=1;next} /<!-- DIRECTIVE:END -->/{f=0} f' "$skill" | sed '1s/^\xEF\xBB\xBF//'
}

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
  skill_block
  exit 0
fi

tmp_text="$(mktemp)"
tmp_body="$(mktemp)"
tmp_out="$(mktemp)"
trap 'rm -f "$tmp_text" "$tmp_body" "$tmp_out"' EXIT

if [ "$mode" = file ]; then
  [ -f "$value" ] || fail "strategy file not found: $value"
  # The source may carry a UTF-8 BOM (any .md holding Chinese does); inside the block it
  # would match nothing and read as stray bytes.
  sed '1s/^\xEF\xBB\xBF//' "$value" > "$tmp_text"
else
  case "$value" in *[!\ ]*) ;; *) fail 'strategy text is empty' ;; esac
  printf '%s\n' "$value" > "$tmp_text"
fi

# The marker makes a deliberate override distinguishable from a preset whose text
# drifted (tests/test_strategy_block.py); re-applying a preset rewrites the whole block
# and so removes it.
{ printf '%s\n\n' "$ad_hoc_marker"; cat "$tmp_text"; } > "$tmp_body"

awk -v dfile="$tmp_body" '
  /<!-- DIRECTIVE:BEGIN/ { print; while ((getline l < dfile) > 0) print l; skip=1; next }
  /<!-- DIRECTIVE:END -->/ { skip=0 }
  !skip { print }
' "$skill" > "$tmp_out" && mv "$tmp_out" "$skill"

# Read it back: a write that did not land would otherwise be reported as success, and
# the block is what the running session is handed.
if ! diff -B -q <(skill_block) "$tmp_body" >/dev/null 2>&1; then
  echo 'error: SKILL.md was written, but its directive block does not read back as the injected text.' >&2
  exit 2
fi

echo "Ad-hoc strategy injected into the directive block."
echo "The agent sees it on the next end_turn - no restart needed."
