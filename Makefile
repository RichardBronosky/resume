TARGET=richard.paul.bronosky.resume.pdf

all: $(TARGET)

%.pdf: %.tex
	pdflatex $<

clean:
	rm -f *.log *.aux $(TARGET) *.ps *.dvi *.out

