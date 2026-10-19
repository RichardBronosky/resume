YAML_INPUT = src/bruno.bronosky.resume.yaml
BASE = build/bruno.bronosky.resume
DOCX_OUTPUT = $(BASE).docx
VARIANT_JSON = ./tools/resume-variant.py
# Always run the generator in this checkout. A `resume-docx` on PATH may be an
# editable install of some other clone, with different layout code.
PYTHON = $(firstword $(wildcard .venv/bin/python) python3)
RESUME_DOCX = PYTHONPATH=$(CURDIR)/src/docx-generator/src $(PYTHON) -m docx_generator.cli

# Every output is rendered from the JSON of one variant (src/variants/*.yaml):
#   web       -> $(BASE).json, .html        (bronosky.com/resume/)
#   paper     -> $(BASE).docx, .pdf
#   ats       -> $(BASE).ats.docx
#   <one-off> -> $(BASE).<one-off>.docx, .pdf   e.g. make oneoff VARIANT=mysql-dba
.PHONY: all docx pdf ats oneoff json clean check-docx

all: docx

json:
	mkdir -p build
	$(VARIANT_JSON) web -o $(BASE).json
	$(VARIANT_JSON) paper -o $(BASE).paper.json
	$(VARIANT_JSON) ats -o $(BASE).ats.json

check-docx:
	@$(PYTHON) -c 'import docx, jsonschema, yaml' || { echo "Error: python-docx/jsonschema/PyYAML missing. Run inside nix-shell."; exit 1; }

docx: json check-docx
	$(RESUME_DOCX) $(BASE).paper.json -o $(DOCX_OUTPUT)

pdf: json check-docx
	$(RESUME_DOCX) $(BASE).paper.json -o $(DOCX_OUTPUT) --pdf

ats: json check-docx
	$(RESUME_DOCX) $(BASE).ats.json -o $(DOCX_OUTPUT) --ats

oneoff: check-docx
	@test -n "$(VARIANT)" || { echo "Usage: make oneoff VARIANT=<name of a src/variants/*.yaml>"; exit 1; }
	mkdir -p build
	$(VARIANT_JSON) $(VARIANT) -o $(BASE).$(VARIANT).json
	$(RESUME_DOCX) $(BASE).$(VARIANT).json -o $(BASE).$(VARIANT).docx --pdf

clean:
	rm -rf build/
	rm -rf .venv/
	rm -rf src/docx-generator/build/
	rm -rf src/docx-generator/*.egg-info/

open-docx: docx
	@libreoffice $(DOCX_OUTPUT) >/dev/null 2>&1 &

open-pdf: pdf
	@libreoffice $(DOCX_OUTPUT:.docx=.pdf) >/dev/null 2>&1 &

# --- Release Automation ---
# Defaults to today's date (e.g., 2026.04.09) but can be overridden: make release VERSION=1.0.0
VERSION ?= $(shell date +%Y.%m.%d)

release: pdf docx
	@command -v gh >/dev/null 2>&1 || { echo "Error: 'gh' CLI not found. Please run inside nix-shell."; exit 1; }
	@echo "Creating GitHub release v$(VERSION)..."
	gh release create "v$(VERSION)" $(DOCX_OUTPUT) $(DOCX_OUTPUT:.docx=.pdf) \
		--title "Resume Update $(VERSION)" \
		--notes "Automated release of latest resume PDF and DOCX artifacts." \
		--latest
	@echo "Release v$(VERSION) published successfully!"
