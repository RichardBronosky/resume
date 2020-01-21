#!/bin/bash -eu

root_of_git_repo="$(git rev-parse --show-toplevel)"

confirm_and_run(){
    cmd="$*"
        cat >&2 <<NOTICE
About to execute:
    $cmd

Press return to continue. Ctrl-C to break.
NOTICE
    read
    eval "$cmd"
}

get_files(){
    find . -maxdepth 1 \( -name '*tex' -or -name '*sty' -or -name '*ins' -or -name '*dtx' \) -print0 | \
        xargs -0 -n1 -I {} bash -c "printf '%q ' '{}'"
}

extract_pdfs(){
    cp -v output/*.pdf ./
}

cd $root_of_git_repo
files="$(get_files)"

confirm_and_run "tar cf - $files | docker run -i richardbronosky/latex-compiler --tar | tar xvv"
extract_pdfs
