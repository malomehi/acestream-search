# -*- coding: utf-8 -*-

import datetime
import re
import requests

from acestream_search.log import logger
from acestream_search.common.constants import CATEGORIES, MAIN_URL
from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parse
from tabulate import tabulate
from urllib.parse import urlparse


def get_events_table(events: list):
    table = [
        [
            e['title'], e['category'],
            *get_events_extra_columns(e)
        ] for e in sorted(
            events, key=lambda x: (x['date'], x['category'])
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
    live_parents = set(
        live.parent.parent for live in category_sop.findAll(
            name='a',
            attrs={'class': 'live'},
            string=pattern
        )
    )
    alt_parents = set(
        alt.parent.parent for alt in category_sop.findAll(
            name='img',
            attrs={'alt': pattern}
        )
    )
    all_targets = {}
    now = datetime.datetime.now()
    for event_parent in live_parents.union(alt_parents):
        span = event_parent.find(
            name='span',
            attrs={'class': 'evdesc'}
        )
        try:
            date_text = span.text.split('\n')[0].rstrip()
            date = date_parse(date_text)
        except Exception:
            continue
        if (date - now) > datetime.timedelta(hours=hours):
            continue
        if (now - date) > datetime.timedelta(hours=2):
            continue
        live = event_parent.find(
            name='a',
            attrs={'class': 'live'}
        )
        title = '\n'.join([
            event_parent.find(name='img').get('alt'),
            live.text,
            date_text
        ])
        href = MAIN_URL + live.get('href')
        if href not in all_targets:
            all_targets[href] = {
                'title': title, 'date': date,
                'url': href, 'category': category.title().replace('_', ' ')
            }

    pattern = re.compile(r'acestream://')
    for target in all_targets.values():
        acestream_links = []
        game = target['title'].split('\n')[1].strip()
        logger.info(f'Analysing event "{game}"')
        resp = requests.get(target['url'], verify=False)
        resp.raise_for_status()
        links_sop = BeautifulSoup(resp.text, 'html.parser')
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

    return all_targets.values()


def get_events(
    text: str, hours: int, category: str,
    show_empty: bool, include_android=False
):
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
            f'{MAIN_URL}/enx/allupcomingsports/{CATEGORIES[category]}/',
            verify=False
        )
        resp.raise_for_status()
        if resp.history:
            main_url = 'https://' + urlparse(resp.url).netloc
            logger.warning(f'Main url has changed to "{main_url}"')
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

    print("")
    print(events_table)
