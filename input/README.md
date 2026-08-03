# Private Input Files

Place real bank exports in these ignored folders:

- `input/revolut/`
- `input/tatrabanka/`
- `input/slsp/`
- `input/investments/slsp/`

The discovery code also recognizes some locally created aliases, including `input/tatra/`, `input/slovenska_sporitelna/`, and `input/legacy/`.

Do not commit files from this directory. Only this README and `.gitkeep` placeholders are intended for Git.

See [the bank export guide](../docs/setup/bank-export-guide.md) for supported formats and parser notes.
