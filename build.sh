export VERSION=0.0.1
export PROJECT="watcher"
export USERNAME="iaggo"
export REPOSITORY="watcher"

docker build -t ${REPOSITORY} .

docker image tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${VERSION}

docker image  push  ${USERNAME}/${REPOSITORY}:${VERSION}
