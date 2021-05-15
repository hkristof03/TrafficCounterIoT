cd ./$1
docker-compose build --no-cache $@
docker-compose push $@
docker-compose pull $@
cd ..