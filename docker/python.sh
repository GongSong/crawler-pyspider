cd $(dirname $0)
docker-compose -p pyspider exec pyspider-web sh -c "python $*"
