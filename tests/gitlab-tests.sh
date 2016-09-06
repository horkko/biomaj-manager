#! /bin/sh

# Set env variable to use right MongoDB URI string
export BIOMAJ_MANAGER_DOCKER_CONF="/builds/tuco/biomaj-manager/tests/global-docker.properties"
nosetests -q -x || { echo "[BIOAMJ_MANAGER_TESTS] Tests failed" && exit 1; }

exit 0