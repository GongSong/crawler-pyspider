cd $(dirname $0)
docker-compose -f docker-compose-elk.yml -p elk up -d
