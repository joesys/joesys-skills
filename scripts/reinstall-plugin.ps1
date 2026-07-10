<#
.SYNOPSIS
    Clean uninstall and reinstall of the joesys-skills plugin for Claude Code and/or Codex.

.DESCRIPTION
    Removes the plugin, its marketplace entry, and all cached files, then
    performs a fresh clone and reinstall. Useful when cached state gets stale
    or you need to pick up structural changes (new skills, renamed files, etc.).

    Claude Code and Codex install from the same GitHub repository: Claude via
    .claude-plugin/marketplace.json, Codex via .agents/plugins/marketplace.json.

.PARAMETER Target
    Which host to reinstall for: claude, codex, or both. Defaults to both.

.EXAMPLE
    .\scripts\reinstall-plugin.ps1

.EXAMPLE
    .\scripts\reinstall-plugin.ps1 -Target codex
#>

[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex', 'both')]
    [string]$Target = 'both'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$PluginName      = 'joesys-skills'
$MarketplaceName = 'joesys-skills'
$MarketplaceUri  = 'joesys/joesys-skills'

function Reinstall-ClaudePlugin {
    $PluginsRoot = Join-Path $env:USERPROFILE '.claude\plugins'

    # ── Step 1: Uninstall the plugin ────────────────────────────────────────
    Write-Host '[claude 1/5] Uninstalling plugin...' -ForegroundColor Cyan
    claude plugins uninstall "${PluginName}@${MarketplaceName}"

    # ── Step 2: Remove the marketplace ──────────────────────────────────────
    Write-Host '[claude 2/5] Removing marketplace...' -ForegroundColor Cyan
    claude plugins marketplace remove $MarketplaceName

    # ── Step 3: Clean up cached files ────────────────────────────────────────
    Write-Host '[claude 3/5] Cleaning cached files...' -ForegroundColor Cyan

    $CachePaths = @(
        Join-Path $PluginsRoot "marketplaces\$MarketplaceName"
        Join-Path $PluginsRoot "cache\$MarketplaceName"
    )

    # Temp git directories use a wildcard pattern
    $TempGitDirs = Get-ChildItem -Path (Join-Path $PluginsRoot 'cache') -Directory -Filter 'temp_git_*' -ErrorAction SilentlyContinue

    foreach ($path in $CachePaths) {
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
            Write-Host "  Removed: $path" -ForegroundColor DarkGray
        }
    }

    foreach ($dir in $TempGitDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        Write-Host "  Removed: $($dir.FullName)" -ForegroundColor DarkGray
    }

    # ── Step 4: Re-add the marketplace (fresh clone) ─────────────────────────
    Write-Host '[claude 4/5] Adding marketplace (fresh clone)...' -ForegroundColor Cyan
    claude plugins marketplace add $MarketplaceUri

    # ── Step 5: Reinstall the plugin ─────────────────────────────────────────
    Write-Host '[claude 5/5] Installing plugin...' -ForegroundColor Cyan
    claude plugins install $PluginName

    Write-Host "Done — $PluginName reinstalled for Claude Code.`n" -ForegroundColor Green
}

function Reinstall-CodexPlugin {
    # ── Step 1: Remove the installed plugin ──────────────────────────────────
    Write-Host '[codex 1/4] Removing plugin...' -ForegroundColor Cyan
    codex plugin remove "${PluginName}@${MarketplaceName}"

    # ── Step 2: Remove the marketplace ───────────────────────────────────────
    Write-Host '[codex 2/4] Removing marketplace...' -ForegroundColor Cyan
    codex plugin marketplace remove $MarketplaceName

    # ── Step 3: Re-add the marketplace (fresh snapshot) ──────────────────────
    Write-Host '[codex 3/4] Adding marketplace (fresh snapshot)...' -ForegroundColor Cyan
    codex plugin marketplace add $MarketplaceUri

    # ── Step 4: Reinstall the plugin ─────────────────────────────────────────
    Write-Host '[codex 4/4] Installing plugin...' -ForegroundColor Cyan
    codex plugin add "${PluginName}@${MarketplaceName}"

    Write-Host "Done — $PluginName reinstalled for Codex.`n" -ForegroundColor Green
}

if ($Target -in @('claude', 'both')) {
    Reinstall-ClaudePlugin
}

if ($Target -in @('codex', 'both')) {
    Reinstall-CodexPlugin
}
