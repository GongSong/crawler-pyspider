if [ ! -d "$1" ]; then
  mkdir $1
fi

python3 -m grpc_tools.protoc -I ./proto --python_out=./$1 --grpc_python_out=./$1 ./proto/crawler.proto
