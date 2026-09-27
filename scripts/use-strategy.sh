#!/usr/bin/env bash
# Git Bash equivalent of scripts/use-strategy.ps1.
#
# Usage:
#   bash scripts/use-strategy.sh            # list presets + which is active
#   bash scripts/use-strategy.sh science    # apply a preset
#   bash scripts/use-strategy.sh balanced    # restore the upstream default
set -euo pipefail

# This project is Windows-native; see run-dsh-headless.sh for why WSL is refused.
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  echo "error: refusing to run under WSL. Use Git Bash." >&2
  exit 2
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
strategies_dir="${project_root}/prompts/strategies"
workers_dir="${project_root}/prompts/workers"
skill="${project_root}/.dsh/skills/civ6-orchestrator/SKILL.md"
# The first line of an ad-hoc block, written by scripts/set-strategy.sh. An ad-hoc
# block is neither a preset nor a stale preset, and saying so is the difference between
# "re-apply to resynchronise" and "this override is deliberate".
ad_hoc_marker='<!-- ad-hoc directive from the human, not a preset: switching presets replaces it -->'

# Fixed by contracts/worker-proposal.schema.json; enforced by the static gate.
roles=(strategy military-map economy-cities diplomacy-victory)
required_phrases=("immutable" "Do not request tools")

presets() {
  find "$strategies_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort
}

# The preset files carry a UTF-8 BOM (they hold Chinese); the block inside SKILL.md
# does not, so every read and write of a directive goes through here.
strip_bom() {
  sed '1s/^\xEF\xBB\xBF//' "$1"
}

# The directive body SKILL.md carries right now, BOM stripped. Empty when SKILL.md or
# its marker block is missing.
skill_block() {
  [ -f "$skill" ] || return 0
  awk '/<!-- DIRECTIVE:BEGIN/ {inside=1; next}
       /<!-- DIRECTIVE:END -->/ {inside=0}
       inside' "$skill" | sed '1s/^\xEF\xBB\xBF//'
}

# A preset is active only when BOTH destinations agree: the four role files in
# prompts/workers/ and the directive block in SKILL.md. The role files alone reported a
# preset as active while the block still carried a different strategy (measured
# 2026-09-27: prompts/workers/ matched china-conquest while the block was 38 lines
# behind it), and the block is the copy the agent actually reads. Pass any argument to
# ask the weaker question - which preset are the role files from - which is what the
# near-miss message below needs.
current_preset() {
  local preset role ok skip_directive="${1:-}"
  while read -r preset; do
    [ -n "$preset" ] || continue
    ok=1
    for role in "${roles[@]}"; do
      if [ ! -f "$strategies_dir/$preset/$role.md" ]; then ok=0; break; fi
      if ! cmp -s "$strategies_dir/$preset/$role.md" "$workers_dir/$role.md"; then ok=0; break; fi
    done
    if [ "$ok" -eq 1 ] && [ -z "$skip_directive" ] && [ -f "$strategies_dir/$preset/directive.md" ]; then
      if ! diff -B -q <(skill_block) <(strip_bom "$strategies_dir/$preset/directive.md") >/dev/null 2>&1; then
        ok=0
      fi
    fi
    if [ "$ok" -eq 1 ]; then
      printf '%s\n' "$preset"
      return 0
    fi
  done < <(presets)
  return 1
}

show_presets() {
  local current preset roles_only first_line
  current="$(current_preset || true)"
  echo "Available strategy presets:"
  while read -r preset; do
    [ -n "$preset" ] || continue
    if [ "$preset" = "$current" ]; then
      echo "  $preset <- active"
    else
      echo "  $preset"
    fi
  done < <(presets)
  if [ -n "$current" ]; then return 0; fi
  echo
  if [ ! -f "$skill" ] || ! grep -q '<!-- DIRECTIVE:BEGIN' "$skill"; then
    echo "SKILL.md is missing, or has no DIRECTIVE:BEGIN/END block:"
    echo "  $skill"
    echo "No preset can report as active until one is applied to write the block."
    return 0
  fi
  roles_only="$(current_preset role-files-only || true)"
  first_line="$(skill_block | sed -n '1p')"
  if [ "$first_line" = "$ad_hoc_marker" ]; then
    echo "The SKILL.md directive block is an ad-hoc directive, not a preset."
    if [ -n "$roles_only" ]; then echo "prompts/workers/ still matches '$roles_only'."; fi
    echo "Re-apply a preset to replace it: bash scripts/use-strategy.sh ${roles_only:-balanced}"
    return 0
  fi
  if [ -n "$roles_only" ]; then
    echo "prompts/workers/ matches '$roles_only', but the SKILL.md directive block does not."
    echo "The block is the copy the agent reads, so both are re-applied together:"
    echo "  bash scripts/use-strategy.sh $roles_only"
    return 0
  fi
  echo "prompts/workers/ matches no preset (hand-edited)."
  echo "Apply one to return to a known state: bash scripts/use-strategy.sh balanced"
}

name="${1:-}"
case "$name" in
  ""|--list|-l) show_presets; exit 0 ;;
esac

preset_dir="$strategies_dir/$name"
if [ ! -d "$preset_dir" ]; then
  echo "No such preset '$name'. Available: $(presets | tr '\n' ' ')" >&2
  exit 2
fi

# Validate before touching prompts/workers/ so a bad preset cannot be applied.
problems=()
for role in "${roles[@]}"; do
  file="$preset_dir/$role.md"
  if [ ! -f "$file" ]; then
    problems+=("missing file: $role.md")
    continue
  fi
  size=$(wc -c < "$file" | tr -d ' ')
  if [ "$size" -le 100 ]; then
    problems+=("$role.md is only $size bytes (gate needs > 100)")
  fi
  for phrase in "${required_phrases[@]}"; do
    if ! grep -qF "$phrase" "$file"; then
      problems+=("$role.md must contain the phrase '$phrase'")
    fi
  done
done

if [ "${#problems[@]}" -gt 0 ]; then
  echo "Preset '$name' is not valid:" >&2
  printf '  - %s\n' "${problems[@]}" >&2
  exit 2
fi

for role in "${roles[@]}"; do
  cp -f "$preset_dir/$role.md" "$workers_dir/$role.md"
done

# Inject the directive into SKILL.md. Verified 2026-09-19 that the running agent
# never reads prompts/workers/*.md, so a preset applied only there has no effect;
# the skill is loaded at session start and is actually read. $skill is defined at the
# top, because the same file decides which preset is active.
directive="$preset_dir/directive.md"
if [ ! -f "$directive" ]; then
  echo "warning: preset '$name' has no directive.md; SKILL.md left unchanged" >&2
elif [ ! -f "$skill" ]; then
  echo "warning: SKILL.md not found at $skill" >&2
elif ! grep -q '<!-- DIRECTIVE:BEGIN' "$skill"; then
  echo "warning: SKILL.md has no DIRECTIVE marker block; strategy not injected" >&2
else
  tmp="$(mktemp)"
  body="$(mktemp)"
  # Without the strip the preset's BOM lands in the middle of SKILL.md, and the block
  # then matches no preset in either shell.
  strip_bom "$directive" > "$body"
  awk -v dfile="$body" '
    /<!-- DIRECTIVE:BEGIN/ { print; while ((getline l < dfile) > 0) print l; skip=1; next }
    /<!-- DIRECTIVE:END -->/ { skip=0 }
    !skip { print }
  ' "$skill" > "$tmp" && mv "$tmp" "$skill"
  rm -f "$body"
  # Read it back: a write that did not land would otherwise be reported as success, and
  # "which preset is active" is computed from the file.
  if ! diff -B -q <(skill_block) <(strip_bom "$directive") >/dev/null 2>&1; then
    echo "error: SKILL.md was written, but its directive block does not read back as '$name'" >&2
    exit 2
  fi
  echo "Strategy directive injected into SKILL.md."
fi

echo "Applied strategy preset: $name"
echo

if command -v node >/dev/null 2>&1; then
  node "${project_root}/scripts/qualify-static.mjs"
else
  echo "warning: node not found on PATH; skipped static gate verification" >&2
fi
