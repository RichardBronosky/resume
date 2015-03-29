#!/usr/bin/env bash

docker_username="$(sed 's/.*(//;s/).*//' <(docker login & sleep 0.2; kill %1))"
docker_path="$(dirname $(find . -name Dockerfile | sed 's?^./??'))"
docker_tag="$(basename $docker_path)"

docker run -it -P --rm --entrypoint="/bin/bash" $docker_username/$docker_tag
