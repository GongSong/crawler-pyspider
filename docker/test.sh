cd $(dirname $0)
cmd="python -m unittest $*"
cmd=${cmd//projects\//}
docker-compose -p pyspider exec pyspider-web sh -c "$cmd"
