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
