#!/usr/bin/env bash
cd $(dirname $0)
docker-compose  -p pyspider stop
docker rm `docker ps -a -q -f "status=exited"`
#docker system prune --volumes -f