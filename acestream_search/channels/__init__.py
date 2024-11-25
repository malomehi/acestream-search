import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

from acestream_search.common.constants import CHANNELS_URL
from acestream_search.log import logger


def get_channels_table(channels: list):
    table = [[c['name'], c['link']] for c in channels]
    if not table:
        logger.info('Nothing found')
        return

    return tabulate(
        table,
        headers=['Channel', 'Acestream Link'],
        tablefmt='fancy_grid',
        stralign='center',
        rowalign='center'
    )


def get_channels(url=CHANNELS_URL, include_android=False):
    logger.info('Searching for channels')
    resp = requests.get(url)
    resp.raise_for_status()
    if resp.history:
        new_url = 'https://' + urlparse(resp.url).netloc
        logger.warning(
            f'Source url has changed from "{url}" to "{new_url}"'
        )
        return get_channels(new_url, include_android)
    main_sop = BeautifulSoup(resp.text, 'html.parser')
    pattern = re.compile('acestream://.+')
    android = ' (Play on Android)' if include_android else ''

    links = json.loads(
        main_sop.find(name='script').text.split('=')[1].split(';')[0]
    )['links']

    channels = [
        {
            'name': link['name'],
            'link': f'{link['url']}{android}'
        } for link in links if pattern.match(link['url'])
    ]
    return sorted(channels, key=lambda x: x['name'])
