from setuptools import setup

setup(
    name='acestream-search',
    version='0.0.1',
    install_requires=[
        'bs4',
        'python-dateutil',
        'requests',
        'tabulate'
    ],
    entry_points={
        'console_scripts': [
            'acestream-search = acestream_search.acestream_search:__main__',
        ]
    }
)
