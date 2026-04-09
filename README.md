# Bruno Bronosky's Resume Builder

This repository contains the source code and generators for my professional resume. 
The core data is stored in `src/bruno.bronosky.resume.yaml` following the JSON Resume schema.

## Quick Start (NixOS / Linux)

This project uses a native Python generator and `libreoffice` (for PDF conversion). The easiest way to run this on NixOS is using `nix-shell`, which will automatically fetch dependencies, create a Python virtual environment, and install the generator CLI.

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

* `src/bruno.bronosky.resume.yaml` - The single source of truth for all resume data.
* `src/docx-generator/` - A custom Python CLI (`resume-docx`) that reads the YAML and generates a clean, unbreakable DOCX format.
* `build/` - Output directory for generated artifacts.

## Coming Soon (HTML Generation)
Currently, this focuses heavily on creating an ATS-friendly, clean DOCX and PDF.
In the future, the HTML and JSON-resume web generation pipeline (which uses `package.json` and Node.js) will be refactored to match this streamlined workflow.

