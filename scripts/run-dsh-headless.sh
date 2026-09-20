#!/usr/bin/env bash
set -euo pipefail

# Refuse to run under WSL. This project drives a Windows-native Civ VI over
# 127.0.0.1:4318 using a Windows Python venv and a Windows Node install; inside
# WSL none of that resolves (the npm shim at node_modules/.bin/dsh only takes its
# cygpath branch under MINGW/MSYS, so it falls through to `exec node`, which the
# distro does not have), and WSL2 networking can lock up the game's tuner.
# Git Bash is Windows-native and is the supported bash environment here.
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  {
    echo "error: refusing to run under WSL."
    echo
    echo "  Use Git Bash (Windows-native) instead:"
    echo "    'C:\\Program Files\\Git\\bin\\bash.exe'"
    echo "  or from PowerShell:"
    echo "    npm run dsh:play:win"
  } >&2
  exit 2
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dsh_bin="${project_root}/node_modules/.bin/dsh"

# --task-file <path> reads the task from a file instead of an argument, and that
# file is never passed as text. --task-file passes a one-line pointer and the
# agent reads the file itself.
#
# This is the only path that works. The task reaches dsh as a process argument,
# and cmd.exe ends the command line at the first newline (the batch shim
# node_modules\.bin\dsh.cmd truncated a 307-character prompt to its first 80
# characters, silently), while Windows PowerShell does not escape embedded double
# quotes, so a quoted phrase splits the text into extra arguments. A pointer is
# short, single-line and pure ASCII, which is byte-exact through both, and it
# removes the command-line length limit from the picture.
#
# Because the launcher no longer carries the prompt text, the encoding of that
# file stops mattering to the shell: a Chinese prompt launches exactly as safely
# as an English one, from this launcher or the PowerShell one.
#
# --dry-run prints what would be handed to dsh plus the file's digest, and exits
# 0 without launching anything. Use it (never a live invocation) to exercise the
# parsing paths: a real run spawns a whole agent session and, with no game
# attached, leaves a half-initialised session and heartbeat behind.
task_file=""
task_arg=""
dry_run=0

# A leading UTF-8 BOM is a Windows-viewer affordance, not part of the prompt: it
# is what makes Notepad, PowerShell 5.1's Get-Content, and an editor configured
# for GBK recognise a BOM-less UTF-8 file as UTF-8 instead of the ANSI code page.
# It is stripped when reporting the file's digest so the digest describes the
# text, matching run-dsh-headless.ps1.
utf8_bom=$'\xEF\xBB\xBF'

has_bom() {
  [ "$(head -c 3 "$1" 2>/dev/null | od -An -tx1 | tr -d ' \n')" = "efbbbf" ]
}

file_digest() {
  if has_bom "$1"; then
    tail -c +4 "$1" | sha256sum | cut -d' ' -f1 | tr 'a-f' 'A-F'
  else
    sha256sum "$1" | cut -d' ' -f1 | tr 'a-f' 'A-F'
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --task-file)
      if [ -z "${2:-}" ]; then
        echo "error: --task-file needs a path" >&2
        exit 2
      fi
      task_file="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --)
      shift
      while [ $# -gt 0 ]; do
        if [ -n "${task_arg}" ]; then
          echo "error: expected at most one task argument" >&2
          exit 2
        fi
        task_arg="$1"
        shift
      done
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      exit 2
      ;;
    *)
      if [ -n "${task_arg}" ]; then
        echo "error: expected at most one task argument" >&2
        exit 2
      fi
      task_arg="$1"
      shift
      ;;
  esac
done

# Match the PowerShell launcher: --task-file and an argument are mutually exclusive.
if [ -n "${task_file}" ] && [ -n "${task_arg}" ]; then
  echo "error: --task-file and a task argument are mutually exclusive; pass one or the other." >&2
  exit 2
fi

if [ -n "${task_file}" ]; then
  # Resolve relative paths against the project root, not the caller's cwd: the
  # agent's working directory is the project root, and every other path in this
  # script is rooted there too.
  case "${task_file}" in
    /*) abs="${task_file}" ;;
    [A-Za-z]:[\\/]*) abs="${task_file}" ;;
    *) abs="${project_root}/${task_file}" ;;
  esac
  if [ ! -f "${abs}" ]; then
    echo "error: task file not found: ${task_file}" >&2
    exit 2
  fi
  body="$(cat "${abs}")"
  body="${body#"${utf8_bom}"}"
  if [ -z "${body//[[:space:]]/}" ]; then
    echo "error: task file is empty: ${task_file}" >&2
    exit 2
  fi
  reference="${abs}"
  case "${reference}" in
    "${project_root}/"*) reference="${reference#"${project_root}/"}" ;;
  esac
  task="Read ${reference} and carry out every instruction in it before doing anything else."
  task_source="pointer to ${reference}"
elif [ -n "${task_arg}" ]; then
  task="${task_arg}"
  case "${task}" in
    *$'\n'*)
      echo "error: a task argument cannot contain a newline: cmd.exe ends the command line there, so dsh would silently receive only the first line. Put the text in a file and pass --task-file." >&2
      exit 2
      ;;
  esac
  case "${task}" in
    *'"'*)
      echo "error: a task argument cannot contain a double quote: Windows PowerShell does not escape it, so the text would be split into extra arguments. Put the text in a file and pass --task-file." >&2
      exit 2
      ;;
  esac
  task_source="argument"
else
  task="Play one complete turn using the civ6-orchestrator skill."
  task_source="default"
fi

if [ "${dry_run}" -eq 1 ]; then
  echo "dry run - nothing launched"
  echo "  source      : ${task_source}"
  if [ -n "${task_file}" ]; then
    echo "  file bytes  : $(wc -c < "${abs}" | tr -d ' ') on disk"
    if has_bom "${abs}"; then
      echo "  file bom    : present (stripped when the file is read)"
    fi
    if command -v sha256sum >/dev/null 2>&1; then
      echo "  file sha256 : $(file_digest "${abs}")"
    fi
  fi
  echo "  task chars  : ${#task}"
  if command -v sha256sum >/dev/null 2>&1; then
    echo "  task sha256 : $(printf '%s' "${task}" | sha256sum | cut -d' ' -f1 | tr 'a-f' 'A-F')"
  fi
  echo "  --- the entire task handed to dsh (console rendering may be lossy) ---"
  printf '%s\n' "${task}"
  echo "  --- dry run: nothing launched ---"
  exit 0
fi

if [[ ! -x "${dsh_bin}" || ! -x "${project_root}/.tools/bin/uv" ]]; then
  echo "Dependencies are missing. Run: npm run bootstrap" >&2
  exit 2
fi

cd "${project_root}"
export DSH_HOME="${project_root}/.dsh-home"
export DSH_TELEMETRY_MODE="${DSH_TELEMETRY_MODE:-DISABLED}"
exec "${dsh_bin}" --profile headless --patch "${project_root}/dsh/civ6.cordis.yml" "${task}"
