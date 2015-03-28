FROM ubuntu
MAINTAINER Nat Lownes <nat.lownes@gmail.com>

RUN apt-get update

#RUN apt-get install -y texlive-latex3
RUN apt-get install -y texlive-latex-recommended

ADD latexcat /usr/local/bin/latexcat
RUN chmod a+x /usr/local/bin/latexcat

ENTRYPOINT ["/usr/local/bin/latexcat"]
