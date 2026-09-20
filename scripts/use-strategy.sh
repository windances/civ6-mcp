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

# Fixed by contracts/worker-proposal.schema.json; enforced by the static gate.
roles=(strategy military-map economy-cities diplomacy-victory)
required_phrases=("immutable" "Do not request tools")

presets() {
  find "$strategies_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort
}

current_preset() {
  local preset role ok
  while read -r preset; do
    [ -n "$preset" ] || continue
    ok=1
    for role in "${roles[@]}"; do
      if [ ! -f "$strategies_dir/$preset/$role.md" ]; then ok=0; break; fi
      if ! cmp -s "$strategies_dir/$preset/$role.md" "$workers_dir/$role.md"; then ok=0; break; fi
    done
    if [ "$ok" -eq 1 ]; then
      printf '%s\n' "$preset"
      return 0
    fi
  done < <(presets)
  return 1
}

show_presets() {
  local current preset
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
  if [ -z "$current" ]; then
    echo
    echo "prompts/workers/ matches no preset (hand-edited)."
    echo "Apply one to return to a known state: bash scripts/use-strategy.sh balanced"
  fi
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
# the skill is loaded at session start and is actually read.
skill="$project_root/.dsh/skills/civ6-orchestrator/SKILL.md"
directive="$preset_dir/directive.md"
if [ ! -f "$directive" ]; then
  echo "warning: preset '$name' has no directive.md; SKILL.md left unchanged" >&2
elif [ ! -f "$skill" ]; then
  echo "warning: SKILL.md not found at $skill" >&2
elif ! grep -q '<!-- DIRECTIVE:BEGIN' "$skill"; then
  echo "warning: SKILL.md has no DIRECTIVE marker block; strategy not injected" >&2
else
  tmp="$(mktemp)"
  awk -v dfile="$directive" '
    /<!-- DIRECTIVE:BEGIN/ { print; while ((getline l < dfile) > 0) print l; skip=1; next }
    /<!-- DIRECTIVE:END -->/ { skip=0 }
    !skip { print }
  ' "$skill" > "$tmp" && mv "$tmp" "$skill"
  echo "Strategy directive injected into SKILL.md."
fi

echo "Applied strategy preset: $name"
echo

if command -v node >/dev/null 2>&1; then
  node "${project_root}/scripts/qualify-static.mjs"
else
  echo "warning: node not found on PATH; skipped static gate verification" >&2
fi
