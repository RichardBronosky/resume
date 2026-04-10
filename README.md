# Bruno Bronosky's Resume Builder

**[📄 View/Download PDF Version](https://github.com/RichardBronosky/resume/releases/latest/download/bruno.bronosky.resume.pdf)** | **[📝 Download DOCX Version](https://github.com/RichardBronosky/resume/releases/latest/download/bruno.bronosky.resume.docx)**


This repository contains the source code and generators for my professional resume. 
The core data is stored in `src/bruno.bronosky.resume.yaml` following the JSON Resume schema.

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

* `src/bruno.bronosky.resume.yaml` - The single source of truth for all resume data.
* `src/docx-generator/` - A custom Python CLI (`resume-docx`) that reads the YAML and generates a clean, unbreakable DOCX format.
* `build/` - Output directory for generated artifacts.

## Coming Soon (HTML Generation)
Currently, this focuses heavily on creating an ATS-friendly, clean DOCX and PDF.
In the future, the HTML and JSON-resume web generation pipeline (which uses `package.json` and Node.js) will be refactored to match this streamlined workflow.

