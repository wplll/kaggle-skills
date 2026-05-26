#!/usr/bin/env bash
# Uninstall kaggle-skill from ~/.claude
#
# Removes the skill bundle from $HOME/.claude/skills/kaggle-skill
# and slash commands from $HOME/.claude/commands/.
#
# Per the user's global rule, this script removes files one explicit path
# at a time. It does NOT use rm -rf on user-controlled paths.
#
# Usage:
#   ./uninstall.sh                # uninstall for current user
#   ./uninstall.sh --project      # uninstall from ./.claude
#   ./uninstall.sh --dry-run      # show what would be removed

set -euo pipefail

SCOPE="user"
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --project) SCOPE="project" ;;
        --user)    SCOPE="user" ;;
        --dry-run|-n) DRY_RUN=1 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

SKILL_NAME="kaggle-skill"
if [[ "$SCOPE" == "user" ]]; then
    CLAUDE_ROOT="$HOME/.claude"
else
    CLAUDE_ROOT="$PWD/.claude"
fi
SKILL_TARGET="$CLAUDE_ROOT/skills/$SKILL_NAME"
COMMANDS_TARGET="$CLAUDE_ROOT/commands"

echo "Uninstalling $SKILL_NAME"
echo "  skill : $SKILL_TARGET"
echo "  cmds  : $COMMANDS_TARGET"
[[ $DRY_RUN -eq 1 ]] && echo "  mode  : dry run (no files removed)"
echo

remove_one_file() {
    local path="$1" label="$2"
    [[ -f "$path" ]] || return 0
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[would remove] $label"
        return 0
    fi
    rm -- "$path"
    echo "[remove] $label"
}

remove_empty_dir() {
    local path="$1"
    [[ -d "$path" ]] || return 0
    if [[ -n "$(ls -A "$path" 2>/dev/null)" ]]; then
        echo "[keep ] non-empty directory: $path"
        return 0
    fi
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[would remove dir] $path"
        return 0
    fi
    rmdir -- "$path"
    echo "[remove dir] $path"
}

# Slash commands — fixed list, one rm per file
for file in kaggle-research.md kaggle-past.md kaggle-fork.md kaggle-experiment.md kaggle-watch.md kaggle-diagnose.md; do
    remove_one_file "$COMMANDS_TARGET/$file" "command $file"
done

# Skill payload — walk and remove each file individually
if [[ -d "$SKILL_TARGET" ]]; then
    while IFS= read -r -d '' f; do
        rel="${f#$SKILL_TARGET/}"
        remove_one_file "$f" "$rel"
    done < <(find "$SKILL_TARGET" -type f -print0)

    # Remove now-empty subdirectories, deepest first
    while IFS= read -r -d '' d; do
        remove_empty_dir "$d"
    done < <(find "$SKILL_TARGET" -mindepth 1 -type d -print0 | sort -rz)

    remove_empty_dir "$SKILL_TARGET"
fi

echo
echo "Done. Restart Claude Code so the slash commands disappear from the registry."
