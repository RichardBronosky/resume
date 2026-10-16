YAML_INPUT = src/bruno.bronosky.resume.yaml
BASE = build/bruno.bronosky.resume
DOCX_OUTPUT = $(BASE).docx
LOCAL_RESUME_DOCX = src/docx-generator/.venv/bin/resume-docx
RESUME_DOCX = $(shell command -v resume-docx 2>/dev/null)
VARIANT_JSON = ./tools/resume-variant.py

ifeq ($(RESUME_DOCX),)
RESUME_DOCX = $(LOCAL_RESUME_DOCX)
endif

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
	@test -x "$(RESUME_DOCX)" || { echo "Error: resume-docx not found. Run inside nix-shell or use the local generator venv at $(LOCAL_RESUME_DOCX)."; exit 1; }

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
