#!/usr/bin/env bash
# Starts Claude Code with the build-phase /goal (condition text in .claude/goal.txt).
# Usage: scripts/run-goal.sh [--headless] [--mode <permission-mode>] [-- extra claude args]
#   --headless   run non-interactively (claude -p); tools outside the allowlist are refused rather than prompted
#   --mode       Claude Code permission mode: default | acceptEdits (default here) | auto | plan | bypassPermissions
set -euo pipefail
cd "$(dirname "$0")/.."

mode="${FLUIDLAB_PERMISSION_MODE:-acceptEdits}"
headless=0
extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --headless) headless=1 ;;
    --mode) mode="$2"; shift ;;
    --) shift; extra=("$@"); break ;;
    *) extra+=("$1") ;;
  esac
  shift
done

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code isn't on your PATH. Run ./setup.sh first." >&2
  exit 1
fi

goal="$(tr '\n' ' ' < .claude/goal.txt | sed 's/  */ /g; s/ $//')"

echo "Where things stand:"
node scripts/goal-status.mjs | sed 's/^/  /'
echo
echo "Starting Claude Code with /goal (permission mode: $mode)…"

if [[ $headless -eq 1 ]]; then
  exec claude -p "/goal $goal" --permission-mode "$mode" ${extra[@]+"${extra[@]}"}
else
  exec claude --permission-mode "$mode" ${extra[@]+"${extra[@]}"} "/goal $goal"
fi
