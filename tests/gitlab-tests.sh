#! /bin/sh

# Install BioMAJ Manager to test it later on
#sudo python setup.py -q install || { echo "Install failed" && exit 1; }
export BIOMAJ_MANAGER_DOCKER_CONF="/builds/tuco/biomaj-manager/tests/global-docker.properties"

# Split tests
for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
    nosetests -a "$attr" -q -x || { echo "[BIOAMJ_MANAGER_TESTS] * $attr tests failed" && exit 1; }
    echo "[BIOMAJ_MANAGER_TESTS] * $attr OK"
done

exit 0