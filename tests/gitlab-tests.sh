#! /bin/sh

# Install BioMAJ Manager to test it later on
cd /builds || { echo "Can't cd to /builds" && exit 1; }
python setup.py -q install || { echo "Install failed" && exit 1; }

echo
echo

# Split tests
for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
    nosetests -a "$attr" -q -x || { echo "[BIOAMJ_MANAGER_TESTS] * $attr tests failed" && exit 1; }
    echo "[BIOMAJ_MANAGER_TESTS] * $attr OK"
done

exit 0