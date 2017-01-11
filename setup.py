try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

config = {
    'name': 'biomajmanager',
    'version': '1.1.10',
    'packages': find_packages(),
    'scripts': ['bin/biomaj-manager.py'],
    'url': 'https://github.com/horkko/biomaj-manager',
    'download_url': 'https://github.com/horkko/biomaj-manager',
    'classifiers': [
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'
    ],
    'install_requires': ['biomaj>=3.1',
                         'biomaj-core>=3.0.7',
                         'Jinja2',
                         'Yapsy'],
    'include_package_data': True,
    'author': 'Emmanuel Quevillon',
    'author_email': 'tuco@pasteur.fr,horkko@gmail.com',
    'description': 'BioMAJ3 contribution Swiss knife'
}

setup(**config)
