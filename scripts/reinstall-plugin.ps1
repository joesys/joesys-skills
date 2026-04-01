<#
.SYNOPSIS
    Clean uninstall and reinstall of the joesys-skills Claude Code plugin.

.DESCRIPTION
    Removes the plugin, its marketplace entry, and all cached files, then
    performs a fresh clone and reinstall. Useful when cached state gets stale
    or you need to pick up structural changes (new skills, renamed files, etc.).

.EXAMPLE
    .\scripts\reinstall-plugin.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$PluginName      = 'joesys-skills'
$MarketplaceName = 'joesys-skills'
$MarketplaceUri  = 'joesys/joesys-skills'
$PluginsRoot     = Join-Path $env:USERPROFILE '.claude\plugins'

# ── Step 1: Uninstall the plugin ────────────────────────────────────────────
Write-Host '[1/5] Uninstalling plugin...' -ForegroundColor Cyan
claude plugins uninstall "${PluginName}@${MarketplaceName}"

# ── Step 2: Remove the marketplace ──────────────────────────────────────────
Write-Host '[2/5] Removing marketplace...' -ForegroundColor Cyan
claude plugins marketplace remove $MarketplaceName

# ── Step 3: Clean up cached files ───────────────────────────────────────────
Write-Host '[3/5] Cleaning cached files...' -ForegroundColor Cyan

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

# ── Step 4: Re-add the marketplace (fresh clone) ───────────────────────────
Write-Host '[4/5] Adding marketplace (fresh clone)...' -ForegroundColor Cyan
claude plugins marketplace add $MarketplaceUri

# ── Step 5: Reinstall the plugin ────────────────────────────────────────────
Write-Host '[5/5] Installing plugin...' -ForegroundColor Cyan
claude plugins install $PluginName

Write-Host "`nDone — $PluginName reinstalled from a clean state." -ForegroundColor Green
