#!/bin/bash -eux

docker_username="$(awk '/Username/{print $NF}' <(docker info 2>/dev/null))"
docker_path="$(cd $(dirname $(find . -name Dockerfile | sed 's?^./??')); pwd)"
docker_tag="$(basename $docker_path)"
docker build -t $docker_username/$docker_tag $docker_path
