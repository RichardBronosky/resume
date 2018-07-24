# latex-compiler
A Docker container for reliably and repeatably compiling LaTeX documents

--------

## Introduction

This is a [really simple Docker image] that tries to [really smart] about how it compiles LaTeX. If you have a question, feature request, or bug report, [open an issue]. If you think it's awesome, it's conveniently part of [my resume repo]. ;-)

## Rationale

If you don't often compile LaTeX, you may find that it is quite a chore to setup a working build environment every few years when you update your resume. LaTeX takes up a lot of space and there is no need kep keep it hanging around when you don't need it. Finally, If you have special packages, styles, fonts, etc. that you need, you probably have documentation along with your project that reminds you how to setup your LaTeX environment. Well, Docker is that documentation is executable form.

## Usage

Here are some of the many ways you can run this image:

```bash
# get pdf output and save it to a file
docker run -i richardbronosky/latex-compiler < bruno.bronosky.resume.tex > bruno.bronosky.resume.pdf

# cat the log and get ls -l output
docker run -i richardbronosky/latex-compiler --debug < bruno.bronosky.resume.tex

# get tar output and expand it (creating an output directory in the current directory)
docker run -i richardbronosky/latex-compiler --tar < bruno.bronosky.resume.tex | tar x

# get tar output and save it to a file
docker run -i richardbronosky/latex-compiler --tar < bruno.bronosky.resume.tex > output.tar

# send tar input if your document requires additional tex and sty files
tar cf - *.tex *.sty | docker run -i richardbronosky/latex-compiler > bruno.bronosky.resume.pdf
# NOTE: All files with a `\documentclass` command will be compiled into PDFs forcing tar output if more than 1.
#       It's probably safer to do the following...

# send tar input and expand tar output
tar cf - *.tex *.sty | docker run -i richardbronosky/latex-compiler --tar | tar x
```
[really simple Docker image]: https://github.com/RichardBronosky/resume/blob/master/latex-compiler/Dockerfile 
[really smart]: https://github.com/RichardBronosky/resume/blob/master/latex-compiler/latexcat 
[open an issue]: https://github.com/RichardBronosky/resume/issues 
[my resume repo]: https://github.com/RichardBronosky/resume 
