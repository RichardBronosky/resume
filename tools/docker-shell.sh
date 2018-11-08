#!/bin/bash -eux

docker_username="$(awk '/Username/{print $NF}' <(docker info 2>/dev/null))"
docker_path="$(cd $(dirname $(find . -name Dockerfile | sed 's?^./??')); pwd)"
docker_tag="$(basename $docker_path)"
docker run -it -P --rm --entrypoint="/bin/bash" $docker_username/$docker_tag
