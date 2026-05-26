#!/usr/bin/env bash
# Install kaggle-skill into ~/.claude
#
# Copies the skill bundle to $HOME/.claude/skills/kaggle-skill
# and slash commands to $HOME/.claude/commands/.
#
# Usage:
#   ./install.sh                # install for current user
#   ./install.sh --project      # install into ./.claude in CWD
#   ./install.sh --force        # overwrite existing files

set -euo pipefail

SCOPE="user"
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --project) SCOPE="project" ;;
        --user)    SCOPE="user" ;;
        --force|-f) FORCE=1 ;;
        -h|--help)
            sed -n '2,11p' "$0"
            exit 0
            ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="kaggle-skill"

if [[ "$SCOPE" == "user" ]]; then
    CLAUDE_ROOT="$HOME/.claude"
else
    CLAUDE_ROOT="$PWD/.claude"
fi

SKILL_TARGET="$CLAUDE_ROOT/skills/$SKILL_NAME"
COMMANDS_TARGET="$CLAUDE_ROOT/commands"

echo "Installing $SKILL_NAME"
echo "  source: $SOURCE"
echo "  skill : $SKILL_TARGET"
echo "  cmds  : $COMMANDS_TARGET"
echo

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
    echo "SKILL.md not found at $SOURCE; run install.sh from inside the kaggle-skill directory." >&2
    exit 1
fi

mkdir -p "$SKILL_TARGET" "$COMMANDS_TARGET"

copy_clean() {
    # Copy a file or directory but drop __pycache__/ and *.pyc.
    local src="$1" dst="$2"
    if [[ -f "$src" ]]; then
        cp "$src" "$dst"
        return
    fi
    mkdir -p "$dst"
    local entry name
    for entry in "$src"/* "$src"/.[!.]*; do
        [[ -e "$entry" ]] || continue
        name="$(basename "$entry")"
        [[ "$name" == "__pycache__" ]] && continue
        [[ "$name" == *.pyc ]] && continue
        copy_clean "$entry" "$dst/$name"
    done
}

copy_entry() {
    local src="$1" dst="$2" label="$3"
    if [[ -e "$dst" && $FORCE -eq 0 ]]; then
        echo "[skip] $label already exists (use --force to overwrite)"
        return
    fi
    rm -rf -- "$dst" 2>/dev/null || true
    copy_clean "$src" "$dst"
    echo "[copy] $label"
}

for entry in SKILL.md references scripts agents; do
    [[ -e "$SOURCE/$entry" ]] || continue
    copy_entry "$SOURCE/$entry" "$SKILL_TARGET/$entry" "$entry"
done

if [[ -d "$SOURCE/commands" ]]; then
    for cmd in "$SOURCE/commands"/*.md; do
        [[ -f "$cmd" ]] || continue
        name="$(basename "$cmd")"
        dst="$COMMANDS_TARGET/$name"
        if [[ -e "$dst" && $FORCE -eq 0 ]]; then
            echo "[skip] command $name already exists (use --force to overwrite)"
            continue
        fi
        cp "$cmd" "$dst"
        echo "[copy] command $name"
    done
fi

echo
echo "Installed. Slash commands available:"
for f in "$COMMANDS_TARGET"/kaggle-*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f" .md)"
    echo "  /$base"
done
echo
echo "Restart Claude Code to pick up new commands."
