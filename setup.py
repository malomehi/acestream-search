from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

console_scripts = [
    'acestream-search=acestream_search.acestream_search_launcher:main',
    'acestream-search-gui=acestream_search.acestream_search_gui_launcher:main'
]

setup(
    name='acestream-search',
    setup_requires=['setuptools-git-versioning'],
    install_requires=required,
    setuptools_git_versioning={
        'enabled': True,
    },
    packages=find_packages(),
    entry_points={
        'console_scripts': console_scripts
    }
)
