TARGET=bruno.bronosky.resume.pdf

# HINT: Run `make clean` if you get "Nothing to be done for `all`."
all: $(TARGET)

%.pdf: %.tex
	docker run -i richardbronosky/latex-compiler < $< > $@

clean:
	rm -f $(TARGET) $$(cat .gitignore)

