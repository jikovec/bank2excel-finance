$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
