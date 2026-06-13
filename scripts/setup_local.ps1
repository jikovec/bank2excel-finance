$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Dirs = @(
    "config",
    "input",
    "input/revolut",
    "input/tatrabanka",
    "input/slsp",
    "input/investments/slsp",
    "output",
    "cache",
    "reports"
)

foreach ($Dir in $Dirs) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
}

$Copies = @(
    @{ From = ".env.example"; To = ".env" },
    @{ From = "config/accounts.example.csv"; To = "config/accounts.csv" },
    @{ From = "config/categories.example.csv"; To = "config/categories.csv" },
    @{ From = "config/currency_rates.example.csv"; To = "config/currency_rates.csv" },
    @{ From = "config/settings.example.yaml"; To = "config/settings.yaml" }
)

foreach ($Copy in $Copies) {
    if ((Test-Path -LiteralPath $Copy.From) -and -not (Test-Path -LiteralPath $Copy.To)) {
        Copy-Item -LiteralPath $Copy.From -Destination $Copy.To
    }
}

Write-Host "Local folders are ready. Existing private files were not overwritten."
