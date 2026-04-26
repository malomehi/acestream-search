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

    candidate_url = ALTERNATIVE_EVENTS_URL
    logger.warning(f'Not able to connect to main url: {EVENTS_URL}')

    working_url = _validate_alternative_url(candidate_url)
    if working_url:
        source_url = working_url
        logger.info(f'Using alternative url: {source_url}')
        return

    logger.warning(
        f'Alternative url {candidate_url} is unavailable or returned 403/502. '
        'Trying the next numeric alternatives.'
    )
    logger.warning(
        'Please update the application to the latest '
        'version to avoid this issue.'
    )
    incremented_url = _try_incremental_alternative_urls(candidate_url)
    if incremented_url:
        source_url = incremented_url
        logger.info(f'Using alternative url: {source_url}')
        return

    source_url = candidate_url
    logger.info(f'Using alternative url: {candidate_url}')


def _normalize_url_base(url: str) -> str:
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'


def _is_valid_alternative_response(response):
    if response.status_code != 200:
        return False
    if 'Error. Page cannot be displayed' in response.text:
        return False

    sop = BeautifulSoup(response.text, 'html.parser')
    return bool(sop.find(name='a', attrs={'class': 'live'}))


def _validate_alternative_url(url):
    try:
        response = requests.get(
            f'{url}/enx/', timeout=3, allow_redirects=True
        )
        if _is_valid_alternative_response(response):
            return _normalize_url_base(response.url)
        return None
    except Exception:
        return None


def _try_incremental_alternative_urls(url, max_retries=20):
    match = re.match(r'^(https?://)([a-zA-Z]+)(\d+)(\..+)$', url)
    if not match:
        return None

    protocol, base_name, number, extension = match.groups()
    number = int(number)

    for retry in range(1, max_retries + 1):
        candidate_url = f'{protocol}{base_name}{number + retry}{extension}'
        try:
            response = requests.get(
                f'{candidate_url}/enx/',
                timeout=3,
                allow_redirects=True
            )
            if _is_valid_alternative_response(response):
                return _normalize_url_base(response.url)
        except Exception:
            continue

    return None


def get_events_timezone():
    test_request = requests.get(f'{source_url}/enx/')
    test_request.raise_for_status()
    sop = BeautifulSoup(test_request.text, 'html.parser')
    try:
        server_time_offset = sop.find(
            attrs={
                'class': 'small',
                'href': '/enx/userinfoedit/#timezone'
            }
        ).text.split('UTC')[-1].strip() or '0'
        tz = datetime.timezone(
            datetime.timedelta(hours=float(server_time_offset))
        )
        return tz
    except Exception:
        logger.warning(
            'Not able to retrieve events time zone from the server. '
            'Assuming Europe/London time zone.'
        )
        return datetime.timezone(
            datetime.datetime.now(
                tz=ZoneInfo('Europe/London')
            ).utcoffset()
        )


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
    include_android: bool, events_timezone: datetime.timezone
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
    now = datetime.datetime.now(events_timezone)
    tzlocal = datetime.datetime.now().astimezone().tzinfo

    for event_parent in live_parents.union(alt_parents):
        span = event_parent.find(
            name='span',
            attrs={'class': 'evdesc'}
        )
        try:
            date_text = span.text.split('\n')[0].rstrip()
            date = date_parse(date_text).replace(
                tzinfo=events_timezone
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
    events_timezone = get_events_timezone()

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
                show_empty, include_android, events_timezone
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
