from setuptools import setup

with open('acestream_search/requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='acestream-search',
    setup_requires=['setuptools-git-versioning'],
    install_requires=required,
    setuptools_git_versioning={
        'enabled': True,
    },
    entry_points={
        'console_scripts': [
            'acestream-search = acestream_search.acestream_search:__main__',
        ]
    }
)
