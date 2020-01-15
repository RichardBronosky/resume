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

cd $root_of_git_repo
confirm_and_run "tar cf - $(echo $(find . -maxdepth 1 -name '*tex' -or -name '*sty' -or -name '*ins' -or -name '*dtx')) | docker run -i richardbronosky/latex-compiler --tar | tar xv"
