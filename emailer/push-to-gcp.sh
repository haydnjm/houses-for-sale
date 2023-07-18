#!/bin/bash

docker buildx build -t houses-for-sale --platform linux/amd64 .
docker tag houses-for-sale europe-west4-docker.pkg.dev/houses-for-sale-392908/houses-for-sale/houses-for-sale:latest
docker push europe-west4-docker.pkg.dev/houses-for-sale-392908/houses-for-sale/houses-for-sale