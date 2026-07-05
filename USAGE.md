# Usage (pyenv)

This repo includes a Python-based DOCX generator. These instructions use pyenv to install Python locally, create a virtual environment, and generate a resume.

## Prerequisites

- pyenv installed and available in your shell
- Docker running (required for PDF conversion and page counting)
- pdfinfo available (from poppler-utils)

## Install Python with pyenv

```bash
pyenv install 3.12.8
pyenv local 3.12.8
python -V
```

## Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install the generator

```bash
pip install -r src/docx-generator/requirements.txt
pip install -e src/docx-generator
```

## Generate a DOCX resume

```bash
resume-docx src/bruno.bronosky.resume.yaml -o build/Bruno_Bronosky_Resume_From_YAML.docx
```

## Generate DOCX and PDF

```bash
resume-docx src/bruno.bronosky.resume.yaml -o build/Bruno_Bronosky_Resume_From_YAML.docx --pdf
```

## Troubleshooting

- If you see a Docker permission error, run the command with sudo or add your user to the docker group.
- If you see "No such file or directory: 'pdfinfo'", install poppler-utils and re-run.
