#! /bin/sh

# Set env variable to use right MongoDB URI string
export BIOMAJ_MANAGER_DOCKER_CONF="/builds/tuco/biomaj-manager/tests/global-docker.properties"
nosetests -q -x || { echo "[BIOAMJ_MANAGER_TESTS] Tests failed" && exit 1; }

# Split tests
#for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
#    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
#    nosetests -a "$attr" -q -x || { echo "[BIOAMJ_MANAGER_TESTS] * $attr tests failed" && exit 1; }
#    echo "[BIOMAJ_MANAGER_TESTS] * $attr OK"
#done

exit 0