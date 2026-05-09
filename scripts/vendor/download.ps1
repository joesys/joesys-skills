# download.ps1 — Fetches vendored JavaScript libraries and fonts.
# Run once after cloning the plugin source. Idempotent.

$ErrorActionPreference = "Stop"
$VendorDir = $PSScriptRoot

function Fetch($url, $dest) {
    if (Test-Path $dest) {
        Write-Host "  exists: $dest"
        return $false
    }
    Write-Host "  fetch: $url"
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    return $true
}

# Prism (syntax highlighting) — bundle core + common languages
$PrismFetched = Fetch "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js" "$VendorDir/prism.min.js"
Fetch "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css" "$VendorDir/prism-light.css" | Out-Null
Fetch "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" "$VendorDir/prism-dark.css" | Out-Null

# Concatenate language components into a single bundle (so we don't ship 25 files).
# Only run when prism.min.js was just freshly fetched — otherwise re-runs would
# double-append language components on top of an already-bundled file.
if ($PrismFetched) {
    $Languages = @(
        "typescript", "javascript", "jsx", "tsx",
        "python", "rust", "go", "java", "csharp", "kotlin",
        "c", "cpp", "ruby", "php", "swift",
        "bash", "powershell",
        "yaml", "json", "toml",
        "sql", "markdown", "css"
    )
    $Bundle = ""
    foreach ($lang in $Languages) {
        $url = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-$lang.min.js"
        Write-Host "  bundle: prism-$lang"
        $tmp = New-TemporaryFile
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $Bundle += "`n" + (Get-Content $tmp -Raw)
        Remove-Item $tmp
    }
    Add-Content -Path "$VendorDir/prism.min.js" -Value $Bundle -NoNewline
}

# Mermaid (diagrams)
Fetch "https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js" "$VendorDir/mermaid.min.js" | Out-Null

# Fonts — Source Serif 4 (TTF flavor; OTF dir exists too but TTF is the recommended web variant).
# Note: files in WOFF2/TTF/ use the .ttf.woff2 extension (not .otf.woff2).
$SourceSerifBase = "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/WOFF2/TTF"
Fetch "$SourceSerifBase/SourceSerif4-Regular.ttf.woff2" "$VendorDir/fonts/source-serif-4-regular.woff2" | Out-Null
Fetch "$SourceSerifBase/SourceSerif4-It.ttf.woff2" "$VendorDir/fonts/source-serif-4-italic.woff2" | Out-Null
Fetch "$SourceSerifBase/SourceSerif4-Bold.ttf.woff2" "$VendorDir/fonts/source-serif-4-bold.woff2" | Out-Null

# Fonts — Inter
$InterBase = "https://raw.githubusercontent.com/rsms/inter/v4.0/docs/font-files"
Fetch "$InterBase/Inter-Regular.woff2" "$VendorDir/fonts/inter-regular.woff2" | Out-Null
Fetch "$InterBase/Inter-SemiBold.woff2" "$VendorDir/fonts/inter-semibold.woff2" | Out-Null

# Fonts — JetBrains Mono
$JBMBase = "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/webfonts"
Fetch "$JBMBase/JetBrainsMono-Regular.woff2" "$VendorDir/fonts/jetbrains-mono-regular.woff2" | Out-Null

Write-Host ""
Write-Host "Vendor assets fetched into $VendorDir"
