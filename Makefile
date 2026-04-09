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
