import asyncio
import datetime
import os
import re
import socket
import ssl
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import aiohttp
import requests
from aia import AIASession
from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parse
from dns import resolver
from tabulate import tabulate

from acestream_search.common.constants import ALTERNATIVE_EVENTS_URL
from acestream_search.common.constants import CATEGORIES
from acestream_search.common.constants import EVENTS_URL
from acestream_search.log import logger


class EventManager():
    def __init__(self):
        self.url_verified = False

    def get_events_timezone(self):
        test_request = requests.get(
            f'{self.source_url}/enx/', verify=self.verify
        )
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

    def check_cert_chain(self):
        res = resolver.Resolver(configure=False)
        res.nameservers = ['1.1.1.1', '1.0.0.1']
        ips = list(
            res.resolve_name(
                self.source_url.split('//')[1], socket.AF_INET
            ).addresses()
        )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((ips[0], 443))
                test_request = requests.get(
                    f'{self.source_url}/enx/allupcomingsports/',
                    verify=self.verify
                )
                test_request.raise_for_status()
            except requests.exceptions.SSLError:
                logger.warning(
                    f'SSL error reported for url: {self.source_url}'
                )
                logger.info('creating aia session')
                aia_session = AIASession()
                logger.info('reading ca data')
                cadata = aia_session.cadata_from_url(self.source_url)
                with NamedTemporaryFile('w', delete=False) as pem_file:
                    logger.info('creating temp ca data file')
                    pem_file.write(cadata)
                    pem_file.flush()
                    self.verify = pem_file.name
                    self.context = ssl.create_default_context(
                        cafile=self.verify
                    )
                    logger.info(f'pem file: {pem_file.name}')
            finally:
                s.close()
        self.url_verified = True

    def set_source_url(self):
        if self.url_verified:
            return
        for url in [EVENTS_URL, ALTERNATIVE_EVENTS_URL]:
            logger.info(f'Using url: {url}')
            self.source_url = url
            self.verify = True
            self.context = True
            try:
                self.check_cert_chain()
                return
            except Exception:
                logger.warning(f'Not able to connect to url: {url}')

        logger.error('Not able to connect to any valid url')

    def get_events_table(self, events: list):
        table = [
            [
                e['title'], e['category'],
                *self.get_events_extra_columns(e)
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

    def get_events_extra_columns(self, event: dict):
        properties = ['url', 'language', 'bitrate']
        return [
            tabulate(
                [[link[property]] for link in event['links']],
                tablefmt='plain'
            ) for property in properties
        ]

    def get_events_from_sop(
        self, category_sop: BeautifulSoup, text: str,
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
            href = self.source_url + live.get('href')
            if href not in all_targets:
                all_targets[href] = {
                    'title': title, 'date': date,
                    'url': href, 'category': category.title().replace('_', ' ')
                }

        asyncio.run(
            self.process_targets(
                all_targets.values(), show_empty, include_android
            )
        )

        return all_targets.values()

    async def process_targets(
        self, targets, show_empty: bool, include_android: bool
    ):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for target in targets:
                tasks.append(
                    self.process_target(
                        session, target, show_empty, include_android
                    )
                )
                game = target['title'].split('\n')[1].strip()
                logger.info(f'Analysing event "{game}"')

            if tasks:
                logger.info('Waiting for results')
            await asyncio.gather(*tasks)

    async def process_target(
        self, session, target, show_empty: bool, include_android: bool
    ):
        pattern = re.compile(r'acestream://')
        acestream_links = []
        async with session.get(target['url'], ssl=self.context) as resp:
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
        self, text: str, hours: int, category: str,
        show_empty: bool, include_android=False
    ):
        events_timezone = self.get_events_timezone()

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
                f'{self.source_url}/enx/allupcomingsports/'
                f'{CATEGORIES[category]}/',
                verify=self.verify
            )
            resp.raise_for_status()
            if resp.history:
                new_url = 'https://' + urlparse(resp.url).netloc
                logger.warning(
                    f'Source url has changed from "{self.source_url}" '
                    f'to "{new_url}"'
                )
                self.source_url = new_url
            main_sop = BeautifulSoup(resp.text, 'html.parser')

            events.extend(
                self.get_events_from_sop(
                    main_sop, text, hours, category,
                    show_empty, include_android, events_timezone
                )
            )

        return events

    def cleanup(self):
        if isinstance(self.verify, str):
            os.remove(self.verify)


def run(category: str, text: str, hours: int, show_empty: bool):
    em = EventManager()
    try:
        em.set_source_url()
        if not em.url_verified:
            return
        events = em.get_events(text, hours, category, show_empty)
        events_table = em.get_events_table(events)
        if not events_table:
            return

        print('')
        print(events_table)
    finally:
        em.cleanup()
