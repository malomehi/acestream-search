import asyncio
import datetime
import re
import socket
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import aiohttp
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parse
from dns import resolver
from tabulate import tabulate

from acestream_search.common.constants import ALTERNATIVE_EVENTS_URL
from acestream_search.common.constants import CATEGORIES
from acestream_search.common.constants import EVENTS_URL
from acestream_search.log import logger

source_url = EVENTS_URL


def switch_source_url():
    global source_url

    source_url = ALTERNATIVE_EVENTS_URL
    logger.warning(f'Not able to connect to main url: {EVENTS_URL}')
    logger.info(f'Using alternative url: {ALTERNATIVE_EVENTS_URL}')


def set_source_url():
    res = resolver.Resolver(configure=False)
    res.nameservers = ['1.1.1.1', '1.0.0.1']
    try:
        ips = list(
            res.resolve_name(
                EVENTS_URL.split('//')[1], socket.AF_INET
            ).addresses()
        )
    except Exception:
        switch_source_url()
        return

    ip = ips[0]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((ip, 443))
            test_request = requests.get(f'{EVENTS_URL}/enx/allupcomingsports/')
            test_request.raise_for_status()
            logger.info(f'Using main url: {EVENTS_URL}')
        except Exception:
            switch_source_url()
        finally:
            s.close()


def get_events_table(events: list):
    table = [
        [
            e['title'], e['category'],
            *get_events_extra_columns(e)
        ] for e in sorted(
            events, key=lambda x: (x['date'], x['category'], x['title'])
        ) if e['links']
    ]
    if not table:
        logger.info('Nothing found')
        return

    return tabulate(
        table,
        headers=[
            'Event', 'Category', 'Acestream Links', 'Language', 'Bitrate'
        ],
        tablefmt='fancy_grid',
        stralign='center',
        rowalign='center'
    )


def get_events_extra_columns(event: dict):
    properties = ['url', 'language', 'bitrate']
    return [
        tabulate(
            [[link[property]] for link in event['links']],
            tablefmt='plain'
        ) for property in properties
    ]


def get_events_from_sop(
    category_sop: BeautifulSoup, text: str,
    hours: int, category: str, show_empty: bool,
    include_android: bool
):
    pattern = re.compile(text, re.IGNORECASE)
    live_parents = {
        live.parent.parent for live in category_sop.findAll(
            name='a',
            attrs={'class': 'live'},
            string=pattern
        )
    }
    alt_parents = {
        alt.parent.parent for alt in category_sop.findAll(
            name='img',
            attrs={'alt': pattern}
        )
    }
    all_targets = {}
    now = datetime.datetime.now(ZoneInfo('Europe/London'))
    tzlocal = datetime.datetime.now().astimezone().tzinfo

    for event_parent in live_parents.union(alt_parents):
        span = event_parent.find(
            name='span',
            attrs={'class': 'evdesc'}
        )
        try:
            date_text = span.text.split('\n')[0].rstrip()
            date = date_parse(date_text).replace(
                tzinfo=ZoneInfo('Europe/London')
            )
        except Exception:
            continue
        if (date - now) > datetime.timedelta(hours=hours):
            continue
        if (now - date) > datetime.timedelta(hours=3):
            continue
        live = event_parent.find(
            name='a',
            attrs={'class': 'live'}
        )
        title = '\n'.join([
            event_parent.find(name='img').get('alt'),
            live.text,
            date.astimezone(tz=tzlocal).strftime('%d %B at %H:%M'),
        ])
        href = source_url + live.get('href')
        if href not in all_targets:
            all_targets[href] = {
                'title': title, 'date': date,
                'url': href, 'category': category.title().replace('_', ' ')
            }

    asyncio.run(
        process_targets(all_targets.values(), show_empty, include_android)
    )

    return all_targets.values()


async def process_targets(targets, show_empty: bool, include_android: bool):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for target in targets:
            tasks.append(
                process_target(
                    session, target, show_empty, include_android
                )
            )
            game = target['title'].split('\n')[1].strip()
            logger.info(f'Analysing event "{game}"')

        if tasks:
            logger.info('Waiting for results')
        await asyncio.gather(*tasks)


async def process_target(
    session, target, show_empty: bool, include_android: bool
):
    pattern = re.compile(r'acestream://')
    acestream_links = []
    async with session.get(target['url']) as resp:
        links_sop = BeautifulSoup(await resp.text(), 'html.parser')
    acestream_sops = links_sop.findAll(
        name='a', attrs={'href': pattern}
    )
    for acestream_sop in acestream_sops:
        link_parent = acestream_sop.parent.parent
        language = link_parent.find(name='img').get(
            'title'
        ) or 'Unknown'
        bitrate = link_parent.find(
            name='td', attrs={'class': 'bitrate'}
        ).text or 'Unknown'
        url = acestream_sop.get('href')
        if include_android:
            url += ' (Play on Android)'
        acestream_links.append(
            {'url': url, 'language': language, 'bitrate': bitrate}
        )
    target['links'] = sorted(
        acestream_links, key=lambda x: (x['language'], x['bitrate'])
    ) or (
        [{
            'url': 'No acestream links available at the moment',
            'language': '-',
            'bitrate': '-'
        }] if show_empty else None
    )


def get_events(
    text: str, hours: int, category: str,
    show_empty: bool, include_android=False
):
    global source_url

    set_source_url()

    search_text = f'with text "{text}" ' if text else ''
    categories = [category] if category else CATEGORIES.keys()

    events = []
    for category in categories:
        logger.info(
            f'Searching for events {search_text}'
            f'on category "{category}" in '
            f'the next {hours} hours'
        )
        resp = requests.get(
            f'{source_url}/enx/allupcomingsports/{CATEGORIES[category]}/'
        )
        resp.raise_for_status()
        if resp.history:
            new_url = 'https://' + urlparse(resp.url).netloc
            logger.warning(
                f'Source url has changed from "{source_url}" to "{new_url}"'
            )
            source_url = new_url
        main_sop = BeautifulSoup(resp.text, 'html.parser')

        events.extend(
            get_events_from_sop(
                main_sop, text, hours, category,
                show_empty, include_android
            )
        )

    return events


def run(category: str, text: str, hours: int, show_empty: bool):
    events = get_events(text, hours, category, show_empty)

    events_table = get_events_table(events)
    if not events_table:
        return

    print('')
    print(events_table)
