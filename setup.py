from distutils.core import setup

config = {
    'name': 'biomaj-manager',
    'version': '1.0.2',
    'packages': ['biomajmanager'],
    'scripts': ['bin/biomaj-manager.py'],
    'url': 'https://github.com/horkko/biomaj-manager',
    'license': '',
    'install_requires': ['biomaj',
			 'Jinja2',
			 'Yapsy'],
    'include_package_data': True,
    'author' :'Emmanuel Quevillon',
    'author_email' :'horkko@gmail.com',
    'description' :'BioMAJ3 toolbox'
}

setup(**config)
