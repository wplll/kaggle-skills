# Uninstall kaggle-skill from ~/.claude
#
# Removes the skill bundle from $env:USERPROFILE/.claude/skills/kaggle-skill
# and slash commands from $env:USERPROFILE/.claude/commands/.
#
# Per the user's global rule, this script removes files one explicit path
# at a time. It does NOT use Remove-Item -Recurse on user-controlled paths.
#
# Usage:
#   pwsh -File uninstall.ps1                  # uninstall from current user
#   pwsh -File uninstall.ps1 -Scope project   # uninstall from ./.claude
#   pwsh -File uninstall.ps1 -DryRun          # show what would be removed

[CmdletBinding()]
param(
    [ValidateSet('user', 'project')]
    [string]$Scope = 'user',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$skillName = 'kaggle-skill'

if ($Scope -eq 'user') {
    $claudeRoot = Join-Path $env:USERPROFILE '.claude'
} else {
    $claudeRoot = Join-Path (Get-Location) '.claude'
}

$skillTarget = Join-Path (Join-Path $claudeRoot 'skills') $skillName
$commandsTarget = Join-Path $claudeRoot 'commands'

Write-Host "Uninstalling $skillName"
Write-Host "  skill : $skillTarget"
Write-Host "  cmds  : $commandsTarget"
if ($DryRun) { Write-Host "  mode  : dry run (no files removed)" }
Write-Host ""

function Remove-OneFile {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    if ($DryRun) {
        Write-Host "[would remove] $Label"
        return
    }
    Remove-Item -LiteralPath $Path -Force
    Write-Host "[remove] $Label"
}

function Remove-EmptyDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    $children = Get-ChildItem -LiteralPath $Path -Force
    if ($children.Count -ne 0) {
        Write-Host "[keep ] non-empty directory: $Path"
        return
    }
    if ($DryRun) {
        Write-Host "[would remove dir] $Path"
        return
    }
    Remove-Item -LiteralPath $Path -Force
    Write-Host "[remove dir] $Path"
}

# Slash commands — fixed list, one Remove-Item per file
$commandFiles = @(
    'kaggle-research.md',
    'kaggle-past.md',
    'kaggle-fork.md',
    'kaggle-data.md',
    'kaggle-experiment.md',
    'kaggle-watch.md',
    'kaggle-diagnose.md'
)
foreach ($file in $commandFiles) {
    Remove-OneFile -Path (Join-Path $commandsTarget $file) -Label "command $file"
}

# Skill payload — walk the installed tree, remove each file one by one
if (Test-Path -LiteralPath $skillTarget -PathType Container) {
    $files = Get-ChildItem -LiteralPath $skillTarget -Recurse -File -Force | Sort-Object FullName -Descending
    foreach ($f in $files) {
        Remove-OneFile -Path $f.FullName -Label $f.FullName.Substring($skillTarget.Length).TrimStart('\','/')
    }
    # Remove now-empty subdirectories from leaves up
    $dirs = Get-ChildItem -LiteralPath $skillTarget -Recurse -Directory -Force |
        Sort-Object { $_.FullName.Length } -Descending
    foreach ($d in $dirs) {
        Remove-EmptyDir -Path $d.FullName
    }
    Remove-EmptyDir -Path $skillTarget
}

Write-Host ""
Write-Host "Done. Restart Claude Code so the slash commands disappear from the registry."
