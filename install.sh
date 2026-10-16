#!/usr/bin/env bash
# Install skills into Claude Code, Codex, Cursor and/or Antigravity.
#
#   ./install.sh                         # all skills, every agent, user-wide
#   ./install.sh --agent cursor de-slop  # one skill, one agent
#   ./install.sh --project               # into ./<agent dir> of the current repo instead of $HOME
#   ./install.sh --list                  # show available skills
#
# Re-running is safe: each skill folder is replaced with the current version.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS="claude codex cursor antigravity"
SCOPE=user
SELECTED=()

usage() { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

dest_for() { # $1 agent -> destination dir
  local base
  if [[ $SCOPE == project ]]; then base="$PWD"; else base="$HOME"; fi
  case "$1" in
    claude)      echo "$base/.claude/skills" ;;
    codex)       echo "$base/.agents/skills" ;;
    cursor)      echo "$base/.cursor/skills" ;;
    antigravity) if [[ $SCOPE == project ]]; then echo "$base/.agents/skills"; else echo "$base/.gemini/config/skills"; fi ;;
    *) echo "unknown agent: $1 (use: $AGENTS)" >&2; exit 2 ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)   AGENTS="${2:?--agent needs a value}"; shift 2 ;;
    --project) SCOPE=project; shift ;;
    --list)    for d in "$ROOT"/plugins/*/skills/*/; do echo "$(basename "$(dirname "$(dirname "$d")")")/$(basename "$d")"; done; exit 0 ;;
    -h|--help) usage ;;
    -*)        echo "unknown option $1" >&2; usage 2 ;;
    *)         SELECTED+=("$1"); shift ;;
  esac
done

SKILL_DIRS=()
for d in "$ROOT"/plugins/*/skills/*/; do
  name="$(basename "$d")"
  if [[ ${#SELECTED[@]} -eq 0 ]] || [[ " ${SELECTED[*]} " == *" $name "* ]]; then SKILL_DIRS+=("${d%/}"); fi
done
[[ ${#SKILL_DIRS[@]} -gt 0 ]] || { echo "no matching skills; try --list" >&2; exit 1; }

DONE=" "
for agent in $AGENTS; do
  dest="$(dest_for "$agent")"
  [[ "$DONE" == *" $dest "* ]] && { echo "✓ $agent (shares $dest)"; continue; }
  mkdir -p "$dest"
  for src in "${SKILL_DIRS[@]}"; do
    rm -rf "${dest:?}/$(basename "$src")"
    cp -R "$src" "$dest/"
  done
  DONE="$DONE$dest "
  echo "✓ $agent: ${#SKILL_DIRS[@]} skills → $dest"
done
