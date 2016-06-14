#!/usr/bin/env bash

docker_username="$(sed '/Username/!d;s/.*(//;s/).*//' <(docker login & sleep 0.2; kill %1))"
docker_path="$(dirname $(find . -name Dockerfile | sed 's?^./??'))"
docker_tag="$(basename $docker_path)"
CMD="docker build --force-rm=true -t $docker_username/$docker_tag $docker_path"

echo $CMD
$CMD
