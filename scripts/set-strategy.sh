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

# A document holding a non-ASCII byte carries a BOM and a pure-ASCII one does not
# (scripts/fix-text-encoding.py); the refusal below keeps this block ASCII, so the step
# is here to drop a BOM an earlier non-ASCII write left behind.
ensure_bom() {
  local file="$1" nonascii
  # Strip a leading BOM before counting, or the BOM's own three bytes make every file look
  # non-ASCII and the removal branch below can never run.
  nonascii="$(sed '1s/^\xEF\xBB\xBF//' "$file" | LC_ALL=C tr -d '\000-\177' | wc -c | tr -d ' ')"
  if [ "$nonascii" -gt 0 ]; then
    if [ "$(head -c 3 "$file" | od -An -tx1 | tr -d ' \n')" != "efbbbf" ]; then
      sed -i '1s/^/\xEF\xBB\xBF/' "$file"
    fi
  else
    sed -i '1s/^\xEF\xBB\xBF//' "$file"
  fi
}

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

# The skill is an English-only DSH document (human instruction 2026-09-28): the model reads English,
# and civ_mcp.text_encoding.ASCII_ONLY holds this file to pure ASCII, so a Chinese block would fail
# the gate a moment after it was written. Translate the text into English and write that - the
# `.cn.md` backup is generated from the English file and is never a place to write. Bytes, not
# characters: `tr -d` removes every ASCII byte, so what is left can only be non-ASCII.
nonascii="$(LC_ALL=C tr -d '\000-\177' < "$tmp_text" | wc -c | tr -d ' ')"
if [ "$nonascii" -ne 0 ]; then
  fail 'the strategy text is not ASCII: the skill is English only - translate it into English and write that'
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
ensure_bom "$skill"

# Read it back: a write that did not land would otherwise be reported as success, and
# the block is what the running session is handed.
if ! diff -B -q <(skill_block) "$tmp_body" >/dev/null 2>&1; then
  echo 'error: SKILL.md was written, but its directive block does not read back as the injected text.' >&2
  exit 2
fi

echo "Ad-hoc strategy injected into the directive block."
echo "The agent sees it on the next end_turn - no restart needed."
