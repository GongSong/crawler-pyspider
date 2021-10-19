#!/usr/bin/env bash
# stop
cd $(dirname $0)
docker-compose  -p pyspider stop
docker rm `docker ps -a -q -f "status=exited"`
#docker system prune --volumes -f

# start
cid=$(docker images | grep "icy/pyspider" | awk '{print $1}')
if [ "$cid" = "" ] || [ "$1" = "build" ]; then
   cd ../
   docker build -t icy/pyspider .
   cd docker
fi
docker-compose -p pyspider up -d
sleep 2
docker-compose -p pyspider up -d
