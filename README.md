# Bruno Bronosky's Resume Builder

**[📄 View/Download PDF Version](https://github.com/RichardBronosky/resume/releases/latest/download/bruno.bronosky.resume.pdf)** | **[📝 Download DOCX Version](https://github.com/RichardBronosky/resume/releases/latest/download/bruno.bronosky.resume.docx)**

This repository contains the source code and generators for my professional resume.

The current active workflow uses structured resume data in `src/bruno.bronosky.resume.yaml`, following the [JSON Resume](https://jsonresume.org/) schema, to generate clean, ATS-friendly DOCX and PDF outputs for job applications.

The LaTeX heritage of this project still [remains](#legacy--latex-notes).

## Quick Start (macOS / Linux)

This project uses a native Python generator and `libreoffice` (for PDF conversion). The easiest way to run this on any macOS or Linux system is using the Nix package manager (you don't need NixOS). Running `nix-shell` will [automatically fetch dependencies](shell.nix#L7-L11), create a Python virtual environment, and install the generator CLI.

**Don't have Nix?** You can install the package manager on any Mac or Linux distro without altering your base OS:
```bash
sh <(curl -L https://nixos.org/nix/install) --daemon
```

```bash
# 1. Drop into the development shell
nix-shell

# 2. Build the DOCX version
make docx

# 3. Build the DOCX and PDF versions
make pdf
```

Outputs will be saved to the `build/` directory.

## Repository Layout

* [`src/bruno.bronosky.resume.yaml`](src/bruno.bronosky.resume.yaml) - The single source of truth for all resume data.
* [`src/docx-generator/`](src/docx-generator/) - A custom Python CLI (`resume-docx`) that reads the YAML and generates a clean, unbreakable DOCX format.
* [`build/`](build/) - Output directory for generated artifacts.

## Current Focus

Right now, the YAML → DOCX/PDF pipeline is the path I am actively maintaining for job applications. The generated outputs are working well for ATS use, and that is the workflow I am prioritizing.

## Legacy / LaTeX Notes

This repo also preserves the earlier LaTeX-based workflow and remains the historical source for the [richardbronosky/latex-compiler](https://registry.hub.docker.com/r/richardbronosky/latex-compiler) Docker image. That tooling is still part of the repository, but it is not the workflow I am actively optimizing right now.
