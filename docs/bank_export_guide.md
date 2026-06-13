# Bank Export Guide

Put transaction exports in the matching ignored input folder.

## Revolut

Use CSV or XLSX exports where possible. Place files under `input/revolut/`.

## Tatra banka

Use XLS or XLSX transaction exports. Place files under `input/tatrabanka/`.

## Slovenska sporitelna

Use XLS or XLSX transaction exports. Place files under `input/slsp/`.

## SLSP Investments

Investment valuation snapshots are point-in-time holdings, not transactions. Place snapshot files under `input/investments/slsp/`.

Snapshots are imported into `Investment_Snapshots` and summarized separately from income and expenses.
