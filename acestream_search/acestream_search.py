# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import re
import requests

from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parse
from tabulate import tabulate
from urllib.parse import urlparse

MAIN_URL = 'https://livetv763.me'

CATEGORIES = {
    'american_football': 27,
    'athletics': 9,
    'bandy': 11,
    'baseball': 19,
    'basketball': 3,
    'beach_soccer': 23,
    'billiard': 29,
    'combat_sport': 75,
    'cricket': 41,
    'cycling': 40,
    'darts': 30,
    'field_hockey': 38,
    'floorball': 32,
    'football': 1,
    'futsal': 12,
    'golf': 37,
    'handball': 13,
    'ice_hockey': 2,
    'mma': 110,
    'netball': 96,
    'padel_tennis': 71,
    'racing': 7,
    'rugby_league': 17,
    'rugby_sevens': 77,
    'rugby_union': 33,
    'table_tennis': 39,
    'tennis': 4,
    'volleyball': 5,
    'winter_sport': 18
}


def main(category: str, text: str, hours: int, show_empty: bool):
    search_text = f'with text "{text}" ' if text else ''
    categories = [category] if category else CATEGORIES.keys()

    events = []
    for category in categories:
        logging.info(
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

        events.extend(get_events(main_sop, text, hours, category, show_empty))

    table = [
        [e['title'], e['category'], *get_event_subtables(e)] for
        e in sorted(
            events, key=lambda x: (x['date'], x['category'])
        ) if e['links']
    ]
    if not table:
        logger.info('Nothing found')
        return

    print("")
    print(
        tabulate(
            table,
            headers=[
                'Event', 'Category', 'Acestream Links', 'Language', 'Bitrate'
            ],
            tablefmt='fancy_grid',
            stralign='center',
            rowalign='center'
        )
    )


def get_event_subtables(event):
    properties = ['url', 'language', 'bitrate']
    return [
        tabulate(
            [[link[property]] for link in event['links']],
            tablefmt='plain'
        ) for property in properties
    ]


def get_events(
    category_sop: BeautifulSoup, text: str,
    hours: int, category: str, show_empty: bool
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


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--category',
        type=str,
        choices=CATEGORIES.keys(),
        default=None,
        help='Event category (default: all)'
    )
    parser.add_argument(
        '--search',
        type=str,
        default='',
        metavar='TEXT',
        help='Text to look for in the event titles (default: any text)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=1,
        help='Events starting within the next number of hours. '
        'Started events are also included (2 hours ago max). '
        '(default: 1 hour)'
    )
    parser.add_argument(
        '--show-empty',
        action='store_true',
        default=False,
        help='Show events with no available acestream links (default: False)'
    )
    args = parser.parse_args()
    main(args.category, args.search, args.hours, args.show_empty)


requests.packages.urllib3.disable_warnings()

logger = logging.getLogger()
logger.setLevel('INFO')
format = '[%(levelname)s] %(message)s'
logging.basicConfig(format=format)

if __name__ == '__main__':
    __main__()
