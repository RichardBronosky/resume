#!/bin/bash -eu

root_of_git_repo="$(git rev-parse --show-toplevel)"
remove_leading_dot_slash='s?^./??'
remove_trailing_path='s?[^/]*$??'
# See: https://stackoverflow.com/a/58795217/117471
docker_username="$(docker-credential-$(jq -r .credsStore ~/.docker/config.json) list | jq -r '. | to_entries[] | select(.key | contains("docker.io")) | last(.value)')"
docker_path="$(find $root_of_git_repo -name Dockerfile | sed "$remove_leading_dot_slash;$remove_trailing_path")"
docker_tag="$(basename $docker_path)"

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

confirm_and_run "docker build -t $docker_username/$docker_tag $docker_path"

