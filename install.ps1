# Install kaggle-skill into ~/.claude
#
# Copies the skill bundle to $env:USERPROFILE/.claude/skills/kaggle-skill
# and slash commands to $env:USERPROFILE/.claude/commands/.
#
# Usage:
#   pwsh -File install.ps1                        # install for current user
#   pwsh -File install.ps1 -Scope project         # install into ./.claude in CWD
#   pwsh -File install.ps1 -Force                 # overwrite existing files

[CmdletBinding()]
param(
    [ValidateSet('user', 'project')]
    [string]$Scope = 'user',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$source = $PSScriptRoot
if (-not $source) { $source = Split-Path -Parent $MyInvocation.MyCommand.Path }

$skillName = 'kaggle-skill'

if ($Scope -eq 'user') {
    $claudeRoot = Join-Path $env:USERPROFILE '.claude'
} else {
    $claudeRoot = Join-Path (Get-Location) '.claude'
}

$skillTarget = Join-Path (Join-Path $claudeRoot 'skills') $skillName
$commandsTarget = Join-Path $claudeRoot 'commands'

Write-Host "Installing $skillName"
Write-Host "  source: $source"
Write-Host "  skill : $skillTarget"
Write-Host "  cmds  : $commandsTarget"
Write-Host ""

if (-not (Test-Path (Join-Path $source 'SKILL.md'))) {
    throw "SKILL.md not found at $source; run install.ps1 from inside the kaggle-skill directory."
}

New-Item -ItemType Directory -Path $skillTarget -Force | Out-Null
New-Item -ItemType Directory -Path $commandsTarget -Force | Out-Null

$copyArgs = @{ Recurse = $true }
if ($Force) { $copyArgs['Force'] = $true }

function Copy-Clean {
    param([string]$Src, [string]$Dst)
    if (Test-Path -LiteralPath $Src -PathType Leaf) {
        Copy-Item -LiteralPath $Src -Destination $Dst -Force:$Force
        return
    }
    New-Item -ItemType Directory -Path $Dst -Force | Out-Null
    Get-ChildItem -LiteralPath $Src -Force | ForEach-Object {
        if ($_.Name -eq '__pycache__') { return }
        if ($_.Name -like '*.pyc') { return }
        Copy-Clean -Src $_.FullName -Dst (Join-Path $Dst $_.Name)
    }
}

# Copy skill payload (SKILL.md + references/ + scripts/ + agents/)
foreach ($entry in @('SKILL.md', 'references', 'scripts', 'agents')) {
    $src = Join-Path $source $entry
    if (-not (Test-Path $src)) { continue }
    $dst = Join-Path $skillTarget $entry
    if ((Test-Path $dst) -and -not $Force) {
        Write-Host "[skip] $entry already exists (use -Force to overwrite)"
        continue
    }
    if (Test-Path $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
    Copy-Clean -Src $src -Dst $dst
    Write-Host "[copy] $entry"
}

# Copy each slash command file individually
$commandsDir = Join-Path $source 'commands'
if (Test-Path $commandsDir) {
    Get-ChildItem -Path $commandsDir -Filter '*.md' | ForEach-Object {
        $dst = Join-Path $commandsTarget $_.Name
        if ((Test-Path $dst) -and -not $Force) {
            Write-Host "[skip] command $($_.Name) already exists (use -Force to overwrite)"
            return
        }
        Copy-Item -Path $_.FullName -Destination $dst -Force:$Force
        Write-Host "[copy] command $($_.Name)"
    }
}

Write-Host ""
Write-Host "Installed. Slash commands available:"
Get-ChildItem -Path $commandsTarget -Filter 'kaggle-*.md' |
    Sort-Object Name |
    ForEach-Object { Write-Host "  /$([System.IO.Path]::GetFileNameWithoutExtension($_.Name))" }
Write-Host ""
Write-Host "Restart Claude Code to pick up new commands."
