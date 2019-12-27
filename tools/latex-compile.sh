#!/bin/bash -eu

root_of_git_repo="$(git rev-parse --show-toplevel)"

confirm_and_run(){
    cmd="$*"
        cat <<NOTICE
About to execute:
    $cmd

Press return to continue. Ctrl-C to break.
NOTICE
    read
    eval "$cmd"
}

for latex_file in $(find $root_of_git_repo -name *.tex); do
    pdf_file="$(basename $latex_file .tex).pdf"
    confirm_and_run "docker run -i richardbronosky/latex-compiler < $latex_file > $pdf_file"
done
