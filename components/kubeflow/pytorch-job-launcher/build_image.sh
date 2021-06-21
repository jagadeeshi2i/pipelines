#!/bin/bash -e
# Copyright 2019 The Kubeflow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

while getopts ":ht:i:" opt; do
  case "${opt}" in
    h) echo "-t: tag name"
       echo "-i: image name. If provided, project name and tag name are not necessary"
       exit
      ;;
    t) TAG_NAME=${OPTARG}
      ;;
    i) LAUNCHER_IMAGE_NAME=${OPTARG}
      ;;
    \? ) echo "Usage: cmd [-t] tag [-i] image"
      exit
      ;;
  esac
done

mkdir -p ./build
rsync -arvp ./src/ ./build/
rsync -arvp ../common/ ./build/

LOCAL_LAUNCHER_IMAGE_NAME=ml-pipeline-kubeflow-pytorchjob

docker build -t ${LOCAL_LAUNCHER_IMAGE_NAME} .
docker tag ${LOCAL_LAUNCHER_IMAGE_NAME} ${LAUNCHER_IMAGE_NAME}:${TAG_NAME}
docker push ${LAUNCHER_IMAGE_NAME}:${TAG_NAME}

rm -rf ./build
