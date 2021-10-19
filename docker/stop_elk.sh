#!/usr/bin/env bash
cd $(dirname $0)
docker-compose -f docker-compose-elk.yml -p elk stop
docker rm `docker ps -a -q -f "status=exited"`
docker system prune --volumes -f