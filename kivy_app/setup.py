from pathlib import Path

from setuptools import find_packages
from setuptools import setup


with open('requirements.txt') as f:
    required = f.read().splitlines()

required.append(
    f'acestream-search @ {(Path(__file__).parent.parent).as_uri()}'
)

setup(
    name='acestream-search-kivy',
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
        'Source': 'https://github.com/malomehi/acestream-search/kivy_app',
    }
)
