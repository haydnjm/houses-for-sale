#!/bin/bash

docker buildx build -t houses-for-sale-emailer --platform linux/amd64 .
docker tag houses-for-sale-emailer europe-west4-docker.pkg.dev/houses-for-sale-392908/houses-for-sale/houses-for-sale-emailer:latest
docker push europe-west4-docker.pkg.dev/houses-for-sale-392908/houses-for-sale/houses-for-sale-emailer