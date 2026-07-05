# Usage

This repo generates DOCX and PDF resumes from `src/bruno.bronosky.resume.yaml`
using `nix-shell` (Python and LibreOffice are provisioned automatically — no
system Python or Docker required).

## Prerequisites

- [Nix](https://nixos.org/download) package manager. If you don't have it:
  ```bash
  sh <(curl -L https://nixos.org/nix/install) --daemon
  ```

## Generate a resume

```bash
# 1. Drop into the development shell (auto-installs the generator CLI)
nix-shell

# 2. Build the DOCX version
make docx

# 3. Build the DOCX and PDF versions
make pdf
```

Outputs are saved to `build/`.

## Rebuilding from scratch

If the local `.venv` gets stale (e.g. after moving to a different machine or
a Nix package upgrade), delete it and let `nix-shell` recreate it:

```bash
rm -rf .venv
nix-shell
```

## Troubleshooting

- `resume-docx: command not found` inside `nix-shell` — delete `.venv` and
  re-enter the shell (see above); the shell hook reinstalls the CLI
  automatically.
- PDF conversion errors — LibreOffice is provisioned by `nix-shell`; make
  sure you're running `make pdf` (or `make docx`) from inside the shell.
