#!/usr/bin/env bash

no_cache=${1:-"false"}
name="get_stepik_statistics"


docker rm -f ${name}
docker build --no-cache=${no_cache} -t ${name}_image  -f ./Dockerfile ./
#docker run --name ${name} -t ${name}_image
