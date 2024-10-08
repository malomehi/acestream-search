from setuptools import find_packages
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

console_scripts = [
    'acestream-search=acestream_search.acestream_search_launcher:main',
    'acestream-search-gui=acestream_search.acestream_search_gui_launcher:main'
]

setup(
    name='acestream-search',
    author_email='1456960+malomehi@users.noreply.github.com',
    description='Simple tool to scrape acestream links from HTML content',
    setup_requires=['setuptools-git-versioning'],
    install_requires=required,
    setuptools_git_versioning={
        'enabled': True,
    },
    package_data={'acestream_search.gui': ['resources/*']},
    packages=find_packages(),
    project_urls={
        'Bug Reports': 'https://github.com/malomehi/acestream-search/issues',
        'Source': 'https://github.com/malomehi/acestream-search',
    },
    entry_points={
        'console_scripts': console_scripts
    }
)
