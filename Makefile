YAML_INPUT = src/bruno.bronosky.resume.yaml
DOCX_OUTPUT = build/bruno.bronosky.resume.docx

.PHONY: all docx pdf clean

all: docx

docx:
	mkdir -p build
	resume-docx $(YAML_INPUT) -o $(DOCX_OUTPUT)

pdf:
	mkdir -p build
	resume-docx $(YAML_INPUT) -o $(DOCX_OUTPUT) --pdf

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
